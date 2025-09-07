#!/home/anja/snap/miniconda3/bin/python3

"""

Main application file \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""

import os
from uuid import uuid4
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, g
import flask_login
from flask_login import LoginManager, UserMixin, logout_user, login_required
from werkzeug.utils import secure_filename
from .src.client_constants import USERS, UPLOAD_FOLDER, DOWNLOAD_FOLDER, MAX_CONT_LEN
from .src.tools import allowed_file, input2dnavi, move_dnavi_files

###############################################################################
# CONFIGURE APP
###############################################################################
login_manager = LoginManager()
app = Flask(__name__)
app.secret_key = "74352743t#+#´01230435¹^xvc1u"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONT_LEN
login_manager.init_app(app)

class User(UserMixin):
  pass

@login_manager.user_loader
def user_loader(username):
  if username not in USERS:
    return

  user = User()
  user.id = username
  return user

@login_manager.request_loader
def request_loader(request):
  username = request.form.get('username')
  if username not in USERS:
    return

  user = User()
  user.id = username
  user.is_authenticated = request.form['pw'] == USERS[username]['pw']
  return user

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template(f'index.html')
    email = request.form['username']
    try:
        request.form['pw'] == USERS[email]['pw']
        print("SUCCESS LOGGING IN")
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect(url_for('protect'))
    except:
        return render_template(f'index.html',
                               error=f"LOGIN FAILED")

@app.route('/gallery', methods=['GET','POST'])
@login_required
def gallery():
    return render_template(f'gallery.html')

@app.route("/info")
def info():
    return "Hello, World! (info)"

@app.route("/warning")
def warning():
    return "A warning message. (warning)"



##############################################################################
# PROCESS INPUT
##############################################################################
@app.route('/protect', methods=['GET','POST'])
@login_required

def protect():
    error=None
    output_id = None

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
                               missing_error=error)
        if ladder_inpt == '':
            error = "Missing Ladder file."
            return render_template(f'protected.html',
                               missing_error=error)

        ######################################################################
        #        UNIQUE ID, CREATE PROCESSING DIRECTORY, SAVE FILES
        ######################################################################
        request_id = str(uuid4())
        processing_folder = f"{app.config['UPLOAD_FOLDER']}{request_id}/"
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
        #               ZIP + MOVE OUTPUT TO DOWNLOAD                        #
        ######################################################################
        print("--- PROVIDING RESULTS FOR DOWNLOAD")
        output_id = move_dnavi_files(request_id=request_id,
            error=error, upload_folder=app.config['UPLOAD_FOLDER'],
            download_folder=app.config['DOWNLOAD_FOLDER'])
        g.output_id = output_id # Output id global for later cleaning

        ######################################################################
        #         DISPLAY ERROR + MAKE DOWNLOAD AVAIL                        #
        ######################################################################
        if error:
            return render_template(f'protected.html',
                               error=error)
        return download(f"{output_id}.zip")
    return render_template(f'protected.html', error=error)

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
    if os.path.isfile(f"{app.config['DOWNLOAD_FOLDER']}{output_id}.zip"):
       os.remove(f"{app.config['DOWNLOAD_FOLDER']}{output_id}.zip")
       print("---- CLEANED")
    else:
        print("Error cleaning up.")
    return response

@app.route('/logout')
def logout():
  logout_user()
  return 'Logged out'

@app.route('/download', methods=['POST'])
def download(filename):
    # The directory where the files are  located
    directory = app.config['DOWNLOAD_FOLDER']
    # Flask's send_from_directory to send the file to the client
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ =='__main__':
    # pip install pyopenssl
    app.run(host="0.0.0.0", debug=True) #, ssl_context="adhoc")


# END OF SCRIPT
