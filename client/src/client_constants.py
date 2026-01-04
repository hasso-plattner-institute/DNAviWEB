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
STATIC_DIR = f"{MAINDIR}static/"

REPORT_COLUMNS =  f"{STATIC_DIR}pdf_report/ELBS_columns.csv"

EXAMPLE_DIR = f"{STATIC_DIR}tests/"
EXAMPLE_TABLE = f"{EXAMPLE_DIR}electropherogram.csv"
EXAMPLE_LADDER = f"{EXAMPLE_DIR}size_standard.csv"
EXAMPLE_META = f"{EXAMPLE_DIR}metadata.csv"

LADDER_DIR = f"{STATIC_DIR}/ladders/"
LADDER_DICT = {"D1000": f"{LADDER_DIR}D1000.csv",
               "HSD5000": f"{LADDER_DIR}HSD5000.csv",
               "gDNA": f"{LADDER_DIR}gDNA.csv",
               "cfDNA": f"{LADDER_DIR}cfDNA.csv",
               "D1000B": f"{LADDER_DIR}D1000B.csv",
               "D7500": f"{LADDER_DIR}D7500.csv",
               "HSDNA": f"{LADDER_DIR}HSDNAB.csv"}
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

####################################################################################
# VM
####################################################################################
# Path to vm1 where the database and file system are.
VM1_API_URL = os.getenv("VM1_API_URL")
# Path to the certificate of vm1 in HTTPS requests.
VM1_CERT_PATH = f"{DNAVI_ROOT}{os.getenv('VM1_CERT_FILE')}"
# Files excluded from saving to vm1 file system
EXCLUDED_FILES = [
    "electropherogram.csv",
    os.path.join("electropherogram", "signal_table.csv"),
    os.path.join("electropherogram", "qc", "bp_translation.csv")
]
