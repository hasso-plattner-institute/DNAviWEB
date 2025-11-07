"""

Main application file \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""
import datetime
from email.mime.text import MIMEText
import logging
import os
import shutil
import tarfile
import smtplib
import threading
from uuid import uuid4

import pandas as pd
import requests
from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory, g
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from client.db_utils import rebuild_electropherogram_and_bp_translation, save_data
from database.config import SessionLocal
from database.schema.file import File
from database.schema.submission import Submission
from database.schema.user_details import UserDetails
from .src.client_constants import UPLOAD_FOLDER, DOWNLOAD_FOLDER, MAX_CONT_LEN, EXAMPLE_TABLE, EXAMPLE_LADDER, \
    EXAMPLE_META, LADDER_DICT, STATIC_DIR, REPORT_COLUMNS, VM1_API_URL
from .src.errors import secure_error
from .src.tools import allowed_file, file2pdf, input2dnavi, get_result_files, move_dnavi_files
from .src.users_saving import get_username, save_user

###############################################################################
# CONFIGURE APP
###############################################################################
login_manager = LoginManager()
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')
# Logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = BASE_DIR.rstrip("/")
LOG_FILE = os.path.join(BASE_DIR, "log", "connect_to_vm1.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="a"), 
        logging.StreamHandler()
    ]
)
logging.info("Test log message at startup")
# Mail
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
HPI_USER = os.environ.get("HPI_EMAIL")
HPI_PASS = os.environ.get("HPI_PASSWORD")
SHARED_MAILBOX = os.environ.get("SHARED_MAILBOX")

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = "74352743t#+#´01230435¹^xvc1u"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONT_LEN
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    db = SessionLocal()
    user_record = db.query(UserDetails).filter_by(username=username).first()
    db.close()
    if not user_record:
        return None
    user = User()
    user.id = user_record.username
    return user
@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    password = request.form.get('pw')
    if not username or not password:
        return None
    db = SessionLocal()
    user_record = db.query(UserDetails).filter_by(username=username).first()
    db.close()
    if not user_record:
        return None
    from werkzeug.security import check_password_hash
    if check_password_hash(user_record.password_hash, password):
        user = User()
        user.id = user_record.username
        return user
    return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template(f'home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template(f'login.html')
    username = request.form['username']
    password = request.form.get('pw')
    if not username or not password:
            return render_template('login.html', error="Username and password are required")
    # Load user record from database
    db = SessionLocal()
    user_record = db.query(UserDetails).filter_by(username=username).first()
    db.close()
    # If record exists and password is correct Log in
    if user_record and check_password_hash(user_record.password_hash, password):
        print("SUCCESS LOGGING IN")
        user = User()
        user.id = user_record.username
        login_user(user)
        return redirect(url_for('submissions_dashboard'))
    else:
        return render_template('login.html', error="Login failed: incorrect username or password")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    username = request.form.get('username')
    password = request.form.get('pw')
    # Check if user tried to register without filling everything out
    if not username or not password:
        return render_template('register.html', error="Username and password are required")
    try:
        db = SessionLocal()
        # Check if username already exists
        existing_user = db.query(Submission).filter_by(username=username).first()
        db.close()
        if existing_user:
            return render_template('register.html', error="User already exists")
        save_user(username, password)
    except Exception as e:
        return render_template('register.html', error="Failed to create user, please try again")
    finally:
        db.close()
    # Go to login page after successful registration
    return redirect(url_for('login'))

@app.route("/ols_proxy")
def ols_proxy():
    """
    Method called from metadata_utils.js
    A proxy for the OLS (Ontology Lookup Service).
    When DNAvi asks OLS for data, the request goes here first.
    This function takes the search text (q) and ontology name,
    sends the request to the OLS API, and returns the OLS response as JSON.
    return:
        - JSON data from OLS if the request works in 10 sec, otherwise error.
    """
    query = request.args.get("q", "")
    ontology = request.args.get("ontology", "efo")
    url = f"https://www.ebi.ac.uk/ols/api/search?q={query}&ontology={ontology}&type=class&rows=10"
    try:
        # Wait for 10 sec
        r = requests.get(url, timeout=10)
        return jsonify(r.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error getting url in 10 sec": str(e)}), 500
    
@app.route('/gallery', methods=['GET','POST'])
@login_required
def gallery():
    return render_template(f'gallery.html')

@app.route('/documentation', methods=['GET','POST'])
def documentation():
    return render_template(f'documentation.html')

@app.route("/info")
def info():
    return "Hello, World! (info)"

@app.route("/warning")
def warning():
    return "A warning message. (warning)"

@app.route("/contact")
def contact():
    return render_template(f'contact.html')

@app.route("/legal_notice")
def legal_notice():
    return render_template(f'legal_notice.html')

@app.route("/citation")
def citation():
    return render_template(f'citation.html')


@app.route('/submissions_dashboard', methods=['GET','POST'])
#@login_required
def submissions_dashboard():
    """
    This route returns the submissions dashboard for the username.
    It retrieves only submissions that the user chose to store in the DB.
    """
    username = get_username()
    submissions = []
    # Only show in the dashboard submissions submissions saved in DB
    db = SessionLocal()
    saved_submissions = db.query(Submission).filter_by(username=username).all()
    db.close()
    for sub in saved_submissions:
        submissions.append({
            "submission_id": sub.submission_id,
            "submission_date": sub.created_at.timestamp()
        })
    # Sort submissions newest first
    submissions.sort(key=lambda x: x["submission_date"], reverse=True)
    return render_template(
        'submissions_dashboard.html',
        submissions=submissions,
        num_submissions=len(submissions)
    )

@app.route("/instructions")
def instructions():
    return render_template("instructions.html")


##############################################################################
#   PARSE OPTIONAL ELBS REPORT COLUMNS TO METADATA TABLE (USER INTERFACE)    #
##############################################################################
@app.route('/get-column-names', methods=['GET'])
def get_column_names():
    """
    This function will read the columns to display in the user interface
    from a table located in static
    :return:
    """
    df = pd.read_table(REPORT_COLUMNS)
    df = df[df["show"] == True]
    # Prepare the information by constructing a list of dictionaries
    columns_info = df[['Item', 'action', 'category']].rename(
        columns={'Item': 'ColumnName', 'action': 'ColumnType',
                 'category': 'Category'}
    ).to_dict(orient='records')
    return jsonify({'columnsInfo': columns_info})
    # END OF FUNCTION
    
##############################################################################
# PROCESS INPUT
##############################################################################
@app.route('/protect', methods=['GET','POST'])
# Allow users to use DNAvi without logging in
#@login_required
def protect():
    error=None
    output_id = None
    #########################################################################
    # SET USERNAME IF USER IS AUTHENTICATED OTHERWISE GENERATE A RANDOM GUEST
    #########################################################################
    username = get_username()
    if request.method == 'POST' and 'incomp_results' not in request.form:
        ######################################################################
        # SET INPUT VARIABLES
        ######################################################################
        request_dict = request.form.to_dict(flat=False)
        example_case = False
        default_ladder = False
        m = None
        m_all = None
        print(request_dict)
        print("............................")

        ######################################################################
        # CHECK IF SOME OF THE DATA ARE REPOSITORY DEFAULTS
        ######################################################################
        if 'Example' in request_dict:
            data_inpt = EXAMPLE_TABLE
            ladder_inpt = EXAMPLE_LADDER
            meta_inpt = EXAMPLE_META
            example_case = True
        else:
            # Rename uploaded gel/signal table to: electropherogram
            uploaded_data_file = request.files['data_file']
            ext = os.path.splitext(uploaded_data_file.filename)[1]

            data_inpt = f"electropherogram{ext}"
            meta_inpt = request.files['meta_file']
            if request_dict['ladder_file'] == ["upload"]:
                ladder_inpt = request.files['ladder_file']
            else:
                default_ladder = True
                ladder_inpt = LADDER_DICT[request_dict['ladder_file'][0]]
                print(f"LADDER SELECTED FROM DEFAULTS {ladder_inpt}")

        ######################################################################
        # BASIC QC
        ######################################################################
        if data_inpt == '' or not allowed_file(data_inpt):
            error = "Missing DNA file (table/image) or format not allowed"
            return render_template(
                f'protected.html',
                missing_error=error,
                user_logged_in = current_user.is_authenticated)
        if ladder_inpt == '':
            error = "Missing Ladder file."
            return render_template(
                f'protected.html',
                missing_error=error,
                user_logged_in = current_user.is_authenticated)

        ######################################################################
        # UNIQUE ID, CREATE PROCESSING DIRECTORY,SAVE FILES TEMPORARLY (VM2) #
        ######################################################################
        request_id = str(uuid4())
        processing_folder = f"{app.config['UPLOAD_FOLDER']}{username}/{request_id}/"
        os.makedirs(processing_folder, exist_ok=True)
        f = f"{processing_folder}{secure_filename(data_inpt)}"
        l = f"{f.rsplit('.', 1)[0]}_ladder.csv"

        ######################################################################
        #  If it's the example or default, simply compy #
        ######################################################################
        if example_case or default_ladder:
            if example_case:
                m = f"{f.rsplit('.', 1)[0]}_meta.csv"
                shutil.copyfile(data_inpt, f)
                shutil.copyfile(ladder_inpt, l)
                shutil.copyfile(meta_inpt, m)
            if default_ladder:
                shutil.copyfile(ladder_inpt, l)
                request.files['data_file'].save(f)
        ######################################################################
        #  Otherwise save user input
        ######################################################################
        else: # otherwise save user input
            request.files['data_file'].save(f)
            request.files['ladder_file'].save(l)

        ######################################################################
        #  Handle meta data and report
        ######################################################################
        if meta_inpt and not example_case:
            m = f"{f.rsplit('.',1)[0]}_meta.csv"
            request.files['meta_file'].save(m)
            # Make a all copy first to save all metadata in db even if some empty
            m_all = m.replace(".csv", "_all.csv")
            shutil.copy(m, m_all)
            print(f"all of metadata saved as: {m_all}")
            # List of metadata columns (values) chosen by user to group by
            group_columns = request.form.getlist('metadata_group_columns_checkbox')
            selected_columns = ['SAMPLE'] # Always keep SAMPLE
            meta_df = pd.read_csv(m)
            #! Important validate of these cols even exist
            if group_columns:
                valid_group_columns = [e for e in group_columns if e in meta_df.columns]
                print("--- Valid group columns", valid_group_columns)
                selected_columns += valid_group_columns
            meta_df = meta_df[selected_columns]
            # Remove all not selected columns
            meta_df.to_csv(m, index=False)
            print("Metadata columns selected for grouping:", selected_columns)
        ######################################################################
        #                       RUN THE ANALYSIS                             #
        ######################################################################
        assigned_vars = [e for e in [("i",f),("l",l),("m",m)] if e[1]]
        op, error = input2dnavi(in_vars=assigned_vars)

        ######################################################################
        #                       CREATE PDF REPORT                           #
        ######################################################################
        if m_all:
            file2pdf(file_dir=m_all, static_dir=STATIC_DIR)

        ######################################################################
        #               ZIP + MOVE OUTPUT TO DOWNLOAD (VM2)                  #
        ######################################################################
        print("--- PROVIDING RESULTS FOR DOWNLOAD")
        output_id = move_dnavi_files(request_id=request_id,
            error=error, upload_folder=f"{app.config['UPLOAD_FOLDER']}{username}/",
            download_folder=f"{app.config['DOWNLOAD_FOLDER']}{username}/")
        g.output_id = output_id # Output id global for later cleaning
        ######################################################################
        #                          DISPLAY ERROR                             #
        ######################################################################
        if error:
            return render_template(
                f'protected.html',
                error=secure_error(error),
                user_logged_in = current_user.is_authenticated)
        ######################################################################
        #                        SAVE DATA TO DATABASE                       #
        ######################################################################
        # Trigger thread to save the data to database in the background
        # to allow returing the results page to the user immidiatly without
        # waiting for saving to the DB.
        save_to_db_flag = request.form.get('save_to_db')
        threading.Thread(target=save_data, args=(app, output_id, username, save_to_db_flag)).start()
        ######################################################################
        #                RETURN ANALYSIS RESULTS                             #
        ######################################################################
        statistics_files, peaks_files, other_files = get_result_files(
            f"{app.config['DOWNLOAD_FOLDER']}{username}/{output_id}")
        #download(f"{output_id}.zip")    
        return render_template(
            "results.html",
            peaks_files=peaks_files,
            other_files=other_files,
            statistics_files=statistics_files,
            output_id=output_id
        )
        # TODO: DELETE FROM VM2 ON SESSION END
    return render_template(f'protected.html', error=error, user_logged_in = current_user.is_authenticated)

##############################################################################
# APP ROUTES
##############################################################################
@app.after_request

def after_request_func(response):
    """
    Function to be exectued AFTER the request is made.
    :param response:
    :return:
    """
    try:
        error = g.get('error')
        output_id = g.get('output_id')
    except:
        print("")
    ###########################################################################
    # Clean up download dir.
    ###########################################################################
    username = get_username()
    if os.path.isfile(f"{app.config['DOWNLOAD_FOLDER']}{username}/{output_id}.zip"):
        os.remove(f"{app.config['DOWNLOAD_FOLDER']}{username}/{output_id}.zip")
        print("---- CLEANED")
    else:
        print("Error cleaning up.")
    return response

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/results/<output_id>/<path:filename>')
def serve_result_file(output_id, filename):
    username = get_username()
    directory = os.path.join(f"{app.config['DOWNLOAD_FOLDER']}{username}/", output_id)
    return send_from_directory(directory, filename)

@app.route('/results/<output_id>', methods=['GET'])
def results(output_id):
    """
    This method describes the route that the dashboard (in submissions_dashboard.html) 
    directs to when a user clicks a specific saved submission id to see the results.
    If files are missing locally on VM2, search if submission exists in DB, if yes search
    for paths to files on DB and request them from VM1 (permanent storage file system).
    """
    username = get_username()
    user_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], username)
    result_dir = os.path.join(user_dir, output_id)
    # If the files are no longer on vm2 -> must get them from permanent store vm1
    if not os.path.exists(result_dir):
        # Lookup DB
        db = SessionLocal()
        submission = db.query(Submission).filter_by(submission_id=output_id).first()
        if not submission:
            return jsonify({'error': 'Submission not found in database'}), 404
        files = db.query(File).filter_by(submission_id=output_id).all()
        db.close()
        if not files:
            return jsonify({'error': 'No files found in database associated with this submission'}), 404
        try:
            # Send request to vm1
            download_url = f"{VM1_API_URL}/send_files"
            logging.info("Requesting submission files from VM1: %s", download_url)
            response = requests.post(
                download_url,
                json={
                    "username": username,
                    "submission_id": output_id
                },
                stream=True,
                timeout=(10, 300)
            )
            response.raise_for_status()
            os.makedirs(user_dir, exist_ok=True)
            archive_path = os.path.join(user_dir, f"{output_id}.tar.gz") # Temporary save
            with open(archive_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            # Extract all files and save
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(user_dir)
            os.remove(archive_path) # Remove temporary archive
            logging.info("Submission files restored from VM1 to VM2 successfully!")
        except requests.RequestException as e:
            logging.error("Failed to get files from VM1: %s", e)
            return jsonify({'error': 'Failed to get submission files from VM1'}), 500

    # Now submission files are on vm2, return results page
    statistics_files, peaks_files, other_files = get_result_files(result_dir)
    return render_template(
        "results.html",
        peaks_files=peaks_files,
        other_files=other_files,
        statistics_files=statistics_files,
        output_id=output_id
    )

@app.route('/download/<submission_id>', methods=['GET'])
def download(submission_id):
    username = get_username()
    # The directory where the result files are  located
    directory = f"{app.config['DOWNLOAD_FOLDER']}{username}/"
    submission_folder = os.path.join(directory, submission_id)
    zip_filename = f"{submission_id}_compressed.zip"
    zip_path = os.path.join(directory, zip_filename)
    # Check if zip exists
    if os.path.isfile(zip_path):
        return send_from_directory(directory, zip_filename, as_attachment=True)
    # Zip missing -> file was delted from temporary storage
    # rebuild local folder with missing files from DB (file system files already
    # loaded during results page retrieval)
    electro_path, bp_path = rebuild_electropherogram_and_bp_translation(submission_id, submission_folder)
    if not electro_path or not bp_path:
        logging.error(f"Failed to rebuild required CSVs for submission {submission_id}. ZIP not created.")
    # Create zip and send
    shutil.make_archive(zip_path.replace(".zip", ""), 'zip', submission_folder)
    logging.info(f"Created zip for submission {submission_id} at {zip_path}")
    return send_from_directory(directory, zip_filename, as_attachment=True)

@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.datetime.fromtimestamp(value).strftime('%b %d, %Y')


@app.route("/request-delete", methods=["POST"])
def request_delete():
    """
    This method sends a mail to shared mailbox when user requests deletion of a submission.
    """
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SHARED_MAILBOX = os.getenv("SHARED_MAILBOX")
    data = request.get_json()
    submission_id = data.get("submission_id")
    subject = f"Automated Notification: Deletion Request for  Submission"
    body = f"""
            Dear DNAvi Support Team,

            A deletion request has been submitted via the DNAvi WEB.

            • Requested by: {current_user.id}
            • Submission ID: {submission_id}

            Please review this request and proceed with the deletion process.

            Best regards,
            DNAvi WEB Automated Notification
            """
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SHARED_MAILBOX
    msg["To"] = SHARED_MAILBOX
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.send_message(msg)
        logging.info("Deletion request email sent for submission %s", submission_id)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error("Email sending failed for submission %s: %s", submission_id, e)
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ =='__main__':
    app.run(host="0.0.0.0", debug=True)

# END OF SCRIPT