"""

File with constants for the flask app / client interaction \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""

import os
import datetime

####################################################################################
# USER
####################################################################################
SUCCESS_TOKEN = "--- DONE. Results in same folder as input file."

####################################################################################
# DIRECTORIES
####################################################################################
MAINDIR = str(os.path.dirname(os.path.abspath(__file__))).rsplit("src",1)[0]
DNAVI_ROOT =  MAINDIR.rsplit("client",1)[0]
UPLOAD_DIR = f"{DNAVI_ROOT}exchange/"
UPLOAD_FOLDER =  f"{UPLOAD_DIR}uploads/"
DOWNLOAD_FOLDER =  f"{UPLOAD_DIR}downloads/"
####################################################################################
# EXECUTION
####################################################################################
DNAVI_EXE = f"{DNAVI_ROOT}lib/DNAvi/DNAvi.py"

####################################################################################
# INPUT
####################################################################################
SESSION_ID = datetime.datetime.now().strftime("%H%M_%d-%m-%Y")
ALLOWED_EXTENSIONS = {'txt', 'tsv', 'csv', 'png', 'jpg', 'jpeg'}
IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}
MAX_CONT_LEN =  16 * 1000 * 1000 # Max. 16MB upload