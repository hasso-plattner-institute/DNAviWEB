"""

Main application file \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""

import threading
import os
import pandas as pd
from uuid import uuid4
import logging
import datetime
from flask import Flask, jsonify, request, render_template, redirect, url_for, send_from_directory, g
import requests
from flask_login import current_user, LoginManager, UserMixin, logout_user, login_required, login_user
from werkzeug.utils import secure_filename
from .src.client_constants import UPLOAD_FOLDER, DOWNLOAD_FOLDER, MAX_CONT_LEN
from .src.tools import allowed_file, input2dnavi, get_result_files, move_dnavi_files
from .src import users_saving as users_module
from .src.users_saving import get_email, save_users, load_users

###############################################################################
# CONFIGURE APP
###############################################################################
login_manager = LoginManager()
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')
#############################Logging####################################
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
#############################Logging####################################
load_users()

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

app.secret_key = "74352743t#+#´01230435¹^xvc1u"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONT_LEN
login_manager.init_app(app)

class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(email):
    # Refresh USERS dict from file
    users_module.load_users()
    
    if email not in users_module.USERS:
        return
    user = User()
    user.id = email
    return user

@login_manager.request_loader
def request_loader(request):
    # Refresh USERS dict from file
    users_module.load_users()
    
    email = request.form.get('email')
    if email not in users_module.USERS:
        return

    if users_module.USERS[email]['pw'] == request.form['pw']:
        user = User()
        user.id = email
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
    email = request.form['email']
    password = request.form.get('pw')

    # Refresh USERS dict from file
    users_module.load_users()
    
    # Check if user exists and password matches
    if email in users_module.USERS and users_module.USERS[email]['pw'] == password:
        print("SUCCESS LOGGING IN")
        user = User()
        user.id = email
        login_user(user)
        return redirect(url_for('submissions_dashboard'))
    else:
        return render_template(f'login.html',
                               error=f"Login failed: incorrect email or password")

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
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template(f'register.html')
    email = request.form['email']
    password = request.form['pw']
    
    # Refresh USERS dict from file
    users_module.load_users()
    
    # Check if email exists already
    if email in users_module.USERS:
        return render_template("register.html", error="User already exists")
    users_module.USERS[email] = {"pw": password}
    # Save new user
    save_users()
    # Send user to log in page
    return redirect(url_for('login'))


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


@app.route('/submissions_dashboard', methods=['GET','POST'])
def submissions_dashboard():
    email = get_email()
    user_downloads = os.path.join(app.config['DOWNLOAD_FOLDER'], email)
    submissions = []

    if os.path.exists(user_downloads):
        for sub_id in os.listdir(user_downloads):
            sub_path = os.path.join(user_downloads, sub_id)
            if os.path.isdir(sub_path):
                submissions.append({
                    "submission_id": sub_id,
                    "submission_date": os.path.getctime(sub_path)  # creation time
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
#                          SAVE ANALYSIS TO DB                               #                 
##############################################################################
# Path to vm1 where the database and file system are.
VM1_API_URL = "http://10.131.22.143:8000/upload"

def save_analysis_to_db(output_id, email, save_to_db):
    """
    Save user data permanently in database on VM1, if consent is given.
    """
    # No consent to save data to db, do nothing
    if save_to_db != 'yes':
        return
    # User consented, save
    user_folder = os.path.join(app.config['DOWNLOAD_FOLDER'], email, output_id)
    if not os.path.exists(user_folder):
        print(f"Folder not found: {user_folder}")
        return 
    # Save only result files to file system in vm1
    statistics_files, peaks_files, other_files = get_result_files(user_folder)
    # Combine all paths
    all_files = []
    for f in statistics_files:
        all_files.append(os.path.join(user_folder, f['name']))
    for f in peaks_files:
        all_files.append(os.path.join(user_folder, f))
    for f in other_files:
        all_files.append(os.path.join(user_folder, f))
    # Prepare files to send
    files_to_send = []
    for path in all_files:
        if os.path.isfile(path):
            filename = os.path.basename(path)
            files_to_send.append(("files", (filename, open(path, "rb"))))
    data = {
        "email": email,
        "sample_id": output_id,
        "description": f"Results for submission {output_id}"
    }
    # Send files to VM1
    try:
        logging.info("Sending files to VM1...")
        response = requests.post(VM1_API_URL, files=files_to_send, data=data, timeout=10)
        logging.info("[save_analysis_to_db] VM1 response: %s %s", response.status_code, response.text)
    except requests.exceptions.RequestException as e:
        logging.info("[save_analysis_to_db] Error sending files to VM1: %s", e)
    finally:
        # Close all opened file
        for _, file_tuple in files_to_send:
            file_tuple[1].close()

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
    # SET email IF USER IS AUTHENTICATED OTHERWISE GENERATE A RANDOM GUEST
    #########################################################################
    email = get_email()
    if request.method == 'POST' and 'incomp_results' not in request.form:
        ######################################################################
        # PERFORM BASIC CHECKS
        ######################################################################
        data_inpt = request.files['data_file'].filename
        ladder_inpt = request.files['ladder_file'].filename
        meta_inpt = request.files['meta_file']
        m = None

        if data_inpt == '' or not allowed_file(data_inpt):
            error = "Missing DNA file (table/image) or format not allowed"
            return render_template(f'protected.html',
                               missing_error=error, user_logged_in = current_user.is_authenticated)
        if ladder_inpt == '':
            error = "Missing Ladder file."
            return render_template(f'protected.html',
                               missing_error=error, user_logged_in = current_user.is_authenticated)

        ######################################################################
        # UNIQUE ID, CREATE PROCESSING DIRECTORY,SAVE FILES TEMPORARLY(VM2)  #
        ######################################################################
        request_id = str(uuid4())
        processing_folder = f"{app.config['UPLOAD_FOLDER']}{email}/{request_id}/"
        os.makedirs(processing_folder, exist_ok=True)
        f = f"{processing_folder}{secure_filename(data_inpt)}"
        request.files['data_file'].save(f)
        l = f"{f.rsplit('.',1)[0]}_ladder.csv"
        request.files['ladder_file'].save(l)
        if meta_inpt:
            m = f"{f.rsplit('.',1)[0]}_meta.csv"
            request.files['meta_file'].save(m)

        ######################################################################
        #                       RUN THE ANALYSIS                             #
        ######################################################################
        assigned_vars = [e for e in [("i",f),("l",l),("m",m)] if e[1]]
        op, error = input2dnavi(in_vars=assigned_vars)
        ######################################################################
        #               ZIP + MOVE OUTPUT TO DOWNLOAD (VM2)                  #
        ######################################################################
        print("--- PROVIDING RESULTS FOR DOWNLOAD")
        output_id = move_dnavi_files(request_id=request_id,
            error=error, upload_folder=f"{app.config['UPLOAD_FOLDER']}{email}/",
            download_folder=f"{app.config['DOWNLOAD_FOLDER']}{email}/")
        g.output_id = output_id # Output id global for later cleaning

        ######################################################################
        #         DISPLAY ERROR + MAKE DOWNLOAD AVAILABLE                    #
        ######################################################################
        if error:
            return render_template(f'protected.html',
                               error=error, user_logged_in = current_user.is_authenticated)

        statistics_files, peaks_files, other_files = get_result_files(f"{app.config['DOWNLOAD_FOLDER']}{email}/{output_id}")
        
        ######################################################################
        #                        SAVE DATA TO DATABASE                       #
        ######################################################################
        # Trigger thread to save the data to database in the background
        # to allow returing the results page to the user immidiatly without
        # waiting for saving to the DB.
        save_to_db_flag = request.form.get('save_to_db')
        threading.Thread(target=save_analysis_to_db, args=(output_id, email, save_to_db_flag)).start()
        ######################################################################
        #                RETURN ANALYSIS RESULTS                             #
        ######################################################################
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
    email = get_email()
    if os.path.isfile(f"{app.config['DOWNLOAD_FOLDER']}{email}/{output_id}.zip"):
        os.remove(f"{app.config['DOWNLOAD_FOLDER']}{email}/{output_id}.zip")
        print("---- CLEANED")
    else:
        print("Error cleaning up.")
    return response

@app.route('/logout')
def logout():
    logout_user()
    return 'Logged out'

@app.route('/results/<output_id>/<path:filename>')
def serve_result_file(output_id, filename):
    email = get_email()
    directory = os.path.join(f"{app.config['DOWNLOAD_FOLDER']}{email}/", output_id)
    return send_from_directory(directory, filename)

@app.route('/results/<output_id>', methods=['GET'])
def results(output_id):
    email = get_email()
    result_dir = os.path.join(app.config['DOWNLOAD_FOLDER'], email, output_id)

    if not os.path.exists(result_dir):
        return f"Results not found for {output_id}", 404

    statistics_files, peaks_files, other_files = get_result_files(result_dir)

    return render_template(
        "results.html",
        peaks_files=peaks_files,
        other_files=other_files,
        statistics_files=statistics_files,
        output_id=output_id
    )

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    email = get_email()
    # The directory where the result files are  located
    directory = f"{app.config['DOWNLOAD_FOLDER']}{email}/"
    # Flask's send_from_directory to send the file to the client
    return send_from_directory(directory, filename, as_attachment=True)

@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.datetime.fromtimestamp(value).strftime('%b %d, %Y')

if __name__ =='__main__':
    app.run(host="0.0.0.0", debug=True)

# END OF SCRIPT