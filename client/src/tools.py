"""

Support functions to enable client / DNAvi interaction \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""
import subprocess
import shutil
from .client_constants import ALLOWED_EXTENSIONS, DNAVI_EXE

def allowed_file(filename):
    """
    Function to check if a file is allowed
    :param filename: str
    :return: str
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def run_cmd(cmd):
    """
    Submit a command to shell and W A I T

    :param cmd: Command to be executed
    :return: subprocess is opened

    """
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()  # Critical

    return output, err
    # END OF FUNCTION

def input2dnavi(in_vars, log_dir="./log/dnavi.log"):
    """
    Function to transform user inputs into command-line usable arguments
    for DNAvi
    in_vars: list of tuples (arg:val)
    :param in_dict: list of tuples (arg:val)
    :param log_dir: str (where to write log info to)
    :return:submit cmd
    """

    # Basic minimal input
    cmd = f"python3 {DNAVI_EXE}"
    for argument, variable in in_vars:
        print(argument, variable)
        cmd += f" -{argument} {variable}"
    try:
        subprocess.check_output(cmd, shell=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        error = e.output.decode("utf-8")
        # Save error to log file
        with open(log_dir, "w") as text_file:
            text_file.write(error)
        text_file.close()
        error_msg = f"--- Error occured, please check {log_dir}"
        return "", error_msg

    return "", "", #output, error
    # END OF FUNCTION

def move_dnavi_files(request_id="", error=None, upload_folder="", download_folder=""):
    """
    Function to move dnavi files
    :param error: str
    :param upload_folder: str
    :param download_folder: str
    :return:
    """

    current_folder_loc = f"{upload_folder}{request_id}"

    if error:
        output_id = f"ERROR_{request_id}"
        interm_destination = f"{upload_folder}{output_id}"
        final_destination = f"{download_folder}{output_id}"
    else:
        output_id = request_id
        interm_destination = f"{upload_folder}{output_id}"
        final_destination = f"{download_folder}{output_id}"

    shutil.make_archive(interm_destination, 'zip',current_folder_loc)
    shutil.move(f"{interm_destination}.zip", final_destination)
    # CLEAN UP THE UPLOAD DIR
    shutil.rmtree(current_folder_loc)

    return output_id
    # END OF FUNCTION