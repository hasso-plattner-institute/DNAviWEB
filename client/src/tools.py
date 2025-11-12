"""

Support functions to enable client / DNAvi interaction \n

Author: Anja Hess \n
Date: 2025-AUG-29 \n


"""
import re
import subprocess
import shutil
import os
import pandas as pd
import sys
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import datetime
from .client_constants import ALLOWED_EXTENSIONS, DNAVI_EXE, EXCLUDED_FILES, SUCCESS_TOKEN


def df2html(df, meta_df):
    """

    For each Section, collect the data and convert them to html. Will be integrated into the PDF.

    :param df:
    :param meta_df:
    :return: dfs_to_pass

    """
    section_dict = df.to_dict()
    retrieve_status = section_dict['retrieve_from']
    columns_avail = meta_df.columns.tolist()
    item2string = section_dict["Item"]
    disclaimer_dict = section_dict['disclaimer']
    disclaimer = "/"
    # Initiate the collection of section name and corresponding data frame
    dfs_to_pass = []

    for item in item2string:
        item_string = item2string[item]
        retrieve_from = retrieve_status[item]
        disclaimer_present = disclaimer_dict[item]
        item_name = f"{item} - {item_string}"
        item_df = pd.DataFrame(["Not available"],columns=[item_string],
                               )

        # Get data from meta table if present
        if item_string in columns_avail:
            item_df = pd.DataFrame(meta_df[item_string])

        # Or get the data from other columns
        if retrieve_from != "FALSE":
            collect_from = [col for col in retrieve_status[item].split(",")
                            if col in columns_avail]
            item_df = meta_df[collect_from]

        # Check if there is a disclaimer to display
        if disclaimer_present != "FALSE":
            disclaimer = disclaimer_dict[item]

        # Rename axes
        item_df = item_df.rename_axis(None, axis=0)

        # Add Item ID & Patient ID & move to front
        #item_df[f"Item {item}"] = ""

        # Add a header and (if applicable) a disclaimer
        header_df = pd.DataFrame(columns=[f"Item {item}", item_string])
        if disclaimer_present != "FALSE":
            header_df.loc[len(header_df)] =  ["!", f"Disclaimer: {disclaimer}"]
        item_df["Patient ID"] = item_df.index
        item_df.reset_index(drop=True, inplace=True)
        starting_cols = ["Patient ID"]
        col_order =  starting_cols + [e for e in item_df.columns if e not in starting_cols]
        item_df = item_df[col_order]

        # Append to the html-converted dataframe to the collection
        dfs_to_pass.append([header_df.to_html(classes='table table-bordered', index=False,),
                            item_df.to_html(classes='table table-bordered', index=False,)])

    # Return the dataframe collection
    return dfs_to_pass
    # END OF FUNCTION



def file2pdf(file_dir, title="DNAvi Liquid Biopsy Report",
             static_dir = "./static/", template_html="ELBS_template.html",
             template_csv="ELBS_template.csv", template_section_html="ELBS_template_section.html",
             style_sheet="style.css"):
    """

    Function to render a report in pdf format from an input csv file.
    Tutorial: https://pbpython.com/pdf-reports.html

    :return:

    """

    ##############################################################################
    # 1. Load the Report metadata and templates
    ##############################################################################
    meta_df = pd.read_csv(file_dir, index_col=0)
    template_dir = f"{static_dir}pdf_report/{template_csv}"
    df = pd.read_table(template_dir, index_col=0)
    out_pdf = file_dir.rsplit("/",1)[0]+"/DNAviReport.pdf"
    style_dir = f"{static_dir}pdf_report/{style_sheet}"

    env = Environment(loader=FileSystemLoader(f"{static_dir}pdf_report/"))

    ##############################################################################
    # 2. Split report by section and get HTMLs for each section
    ##############################################################################
    dfs_final = []
    for section in df["category"].unique():
        print(f"----- SECTION {section}")
        section_df = df[df["category"] == section]
        # Convert to a pretty html output:
        dfs_to_pass = df2html(section_df, meta_df)

        # Render into subsection html:
        template = env.get_template(template_section_html)
        template_vars = {"Report_Detail": dfs_to_pass}
        html_out = template.render(template_vars)
        dfs_final.append([section, html_out])

    ##############################################################################
    # 3. Render everything into the final report template
    ##############################################################################
    template = env.get_template(template_html)
    template_vars = {"title": title,
                     "logo_filename": f"file://{static_dir}img/logo.svg",
                     "style_filename":  f"file://{static_dir}img/logo.svg",
                     "creation_date_time": datetime.datetime.now(
                     ).strftime("%Y-%m-%d %H:%M:%S"),
                     "Report_Detail": dfs_final}

    # Render our file and create the PDF using our css style file
    html_out = template.render(template_vars)

    HTML(string=html_out).write_pdf(out_pdf, stylesheets=[style_dir])
    print(f"--- Saved pdf report to: {out_pdf}")
    # END OF PDF REPORT FUNCTION

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
    # !!! CRITICAL Set the python executable for DNAvi (it will not know other.)
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
        with open(f"{abs_dirname.rsplit('src', 1)[0]}{log_dir}", "w") as text_file:
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

    output_id = request_id
    interm_destination = f"{upload_folder}{output_id}"
    final_destination = f"{download_folder}{output_id}"
    print(interm_destination)
    print(current_folder_loc)
    print(final_destination)

    print("Compressing to: ", f"{interm_destination}.{arx}")
    zip_path = f"{interm_destination}_compressed"
    shutil.make_archive(zip_path, arx, current_folder_loc)

    if os.path.isfile(f"{zip_path}.{arx}"):
        shutil.move(f"{interm_destination}", final_destination + "/")
        shutil.move(f"{zip_path}.{arx}", download_folder + "/")
        print("Success, moving now from: ", interm_destination)
        print("Success, moving now to: ", final_destination)
        # Delete the parent folder of interm_destination only if it is empty
        # because if parallel submissions happen per user, need to wait and
        # not delete the uploads file until all finished
        parent_folder = os.path.dirname(interm_destination)
        if os.path.isdir(parent_folder) and not os.listdir(parent_folder):
            shutil.rmtree(parent_folder)
            print(f"Deleted {parent_folder} folder from uploads")

    return output_id
    # END OF FUNCTION


def get_result_files(folder, prefix=''):
    """
    Collect result files from a folder (recursively), grouped into categories:
      - statistics_files: CSV files containing 'statistics', each with a preview of first 5 rows
      - peaks_files: PNG files named like peaks_<num>_sample.png
      - other_files: Other PNG files in plots/qc/stats folders
      - pdf_files: PDF files (DNAviReport.pdf)

    :param folder: str, base folder to search
    :param prefix: str, relative prefix (used internally for recursion)
    :return: tuple of lists: (statistics_files, peaks_files, other_files, pdf_files)
    """
    statistics_files = []
    peaks_files = []
    other_files = []
    pdf_files = []

    for f in os.listdir(folder):
        full_path = os.path.join(folder, f)
        relative_path = os.path.join(prefix, f) if prefix else f

        if os.path.isdir(full_path):
            # Recursively extend lists
            stats, peaks, other, pdfs = get_result_files(full_path, relative_path)
            statistics_files.extend(stats)
            peaks_files.extend(peaks)
            other_files.extend(other)
            pdf_files.extend(pdfs)
        else:
            fname = f.lower()
            rel_lower = relative_path.lower()
            # CSV statistics files 
            if fname.endswith(".csv") and "statistics" in fname:
                try:
                    df = pd.read_csv(full_path)
                    # Show all rows if it's a basic_statistics file
                    if("basic_statistics" in fname):
                        preview = df.to_dict(orient='records')
                    # Show only first 5 rows otherwise
                    else:
                        preview = df.head(5).to_dict(orient='records')
                except Exception:
                    preview = []
                statistics_files.append({'name': relative_path,
                                         'preview': preview,
                                         'columns': list(df.columns) if preview else []})
            # Peaks PNG
            elif re.match(r"peaks_\d+_sample\.png$", fname):
                peaks_files.append(relative_path)
            # Other PNGs in plots/qc/stats
            elif fname.endswith(".png") and any(folder_name in rel_lower
                                                for folder_name in ["plots", "qc", "stats"]):
                other_files.append(relative_path)
            # PDF files
            elif os.path.basename(f).lower() == "dnavireport.pdf":
                pdf_files.append(relative_path)

    return statistics_files, peaks_files, other_files, pdf_files
    # END OF FUNCTION

def get_all_files_except_saved_in_db(folder, prefix=''):
    """
    Recursively collect ALL files from the folder and subfolders,
    except those that are already stored in the database.
    Excluded:
      - electropherogram.csv
      - qc/bp_translation.csv
    :param folder: str, base folder to search in the first call it is the submission_folder
    :param prefix: str, relative prefix (used internally for recursion)
    :return: list of FULL PATHS of files found in folder and subfolders
    """
    collected_files = []
    for f in os.listdir(folder):
        full_path = os.path.join(folder, f)
        relative_path = os.path.join(prefix, f) if prefix else f
        if os.path.isdir(full_path):
            # Gather files inside subfolders
            collected_files.extend(get_all_files_except_saved_in_db(full_path, relative_path))
        else:
            # Skip files already saved in db
            if relative_path in EXCLUDED_FILES:
                continue
            collected_files.append(relative_path)
    return collected_files