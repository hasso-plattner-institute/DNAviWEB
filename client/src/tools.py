"""

Support functions to enable client / DNAvi interaction \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""
import re
import subprocess
import shutil
import os
import sys
from .client_constants import ALLOWED_EXTENSIONS, DNAVI_EXE, SUCCESS_TOKEN

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
    output = output.decode("utf-8")
    if "error" in output:
        print("Written error: " + output)

    p_status = p.wait()  # Critical

    return output, err
    # END OF FUNCTION

def input2dnavi(in_vars, log_dir="/log/dnavi.log"):
    """
    Function to transform user inputs into command-line usable arguments
    for DNAvi
    in_vars: list of tuples (arg:val)
    :param in_dict: list of tuples (arg:val)
    :param log_dir: str (where to write log info to)
    :return:submit cmd
    """


    ##############################################################################
    # !!! CRITICAL Set the python executable for DNAvi (it will not know othwer.)
    ##############################################################################
    OUR_PYTHON=sys.executable
    cmd = f"{OUR_PYTHON} {DNAVI_EXE}"

    for argument, variable in in_vars:
        print(argument, variable)
        cmd += f" -{argument} {variable}"
    print(cmd)
    ##############################################################################
    # Actually run DNAvi
    ##############################################################################
    outpt, err = run_cmd(cmd)
    print(outpt)

    ##############################################################################
    # Require the SUCCESS_TOKEN (a string) to not throw the error.
    ##############################################################################
    if SUCCESS_TOKEN not in outpt:
        error = outpt
        # Save error to log file
        abs_dirname = os.path.dirname(os.path.abspath(__file__))
        with open(f"{abs_dirname.rsplit('src', 
                                        1)[0]}{log_dir}", "w") as text_file:
            text_file.write(error)
        text_file.close()
        error_msg = f"--- Error occured: {outpt}, also see {log_dir}."
        return "", error_msg

    elif SUCCESS_TOKEN in outpt:
        return "", None # set error to None
    # END OF FUNCTION

def move_dnavi_files(request_id="", error=None, upload_folder="", download_folder="",
                     arx="zip"):
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

    print(interm_destination)
    print(current_folder_loc)
    print(final_destination)

    print("Compressing to: ", f"{interm_destination}.{arx}")
    shutil.make_archive(interm_destination, arx, current_folder_loc)

    if os.path.isfile(f"{interm_destination}.{arx}"):
        print("Success, moving now from: ", interm_destination)
        print("Success, moving now to: ", final_destination)
        shutil.move(f"{interm_destination}", final_destination+"/")
        shutil.move(f"{interm_destination}.{arx}", f"{final_destination}.{arx}")
        
    return output_id
    # END OF FUNCTION

def get_result_files(folder, prefix=''):
    """
    Collect result files from a folder (recursively), grouped into categories:
      - statistics_files: CSV files containing 'statistics'
      - peaks_files: HTML files named like peaks_<num>_sample.html
      - other_files: Other HTML files
    
    :param folder: str, base folder to search
    :param prefix: str, relative prefix (used internally for recursion)
    :return: tuple of lists: (statistics_files, peaks_files, other_files)
    """
    statistics_files = []
    peaks_files = []
    other_files = []

    for f in os.listdir(folder):
        full_path = os.path.join(folder, f)
        relative_path = os.path.join(prefix, f) if prefix else f

        if os.path.isdir(full_path):
            # Recursively extend lists
            stats, peaks, other = get_result_files(full_path, relative_path)
            statistics_files.extend(stats)
            peaks_files.extend(peaks)
            other_files.extend(other)
        else:
            fname = f.lower()
            rel_lower = relative_path.lower()
            if fname.endswith(".csv") and "statistics" in fname:
                statistics_files.append(relative_path)
            elif re.match(r"peaks_\d+_sample\.png$", fname):
                peaks_files.append(relative_path)
            elif fname.endswith(".png") and any(folder_name in rel_lower for folder_name in ["plots", "qc", "stats"]):
                other_files.append(relative_path)

    return statistics_files, peaks_files, other_files
    # END OF FUNCTION
