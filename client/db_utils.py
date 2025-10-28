"""
This module handles data saving into database and file system of vm_1.
"""
import os
import uuid
import logging
import chardet
import pandas as pd
import requests
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from database.config import engine
from database.schema.gel_electrophoresis_devices import GelElectrophoresisDevice
from database.schema.ladder import Ladder
from database.schema.ladder_peak import LadderPeak
from database.schema.ontology_term import OntologyTerm
from database.schema.subject import Subject
from database.schema.submission import Submission
from .src.tools import get_result_files
# Path to vm1 where the database and file system are.
VM1_API_URL = "http://10.131.22.143:8000/upload"

def get_clean_value(row, column_name):
    """
    Extract from column_name the value in row. 
    Return None if value in column is None, else return the value striped
    from whitesapces.
    """
    value = None
    if column_name in row:
        value = row[column_name]
    if value is not None:
        return str(value).strip()
    return value

def detect_file_encoding(file_path):
    """
    Detect encoding of csv file (can be different depending on user's operating system)
    """
    with open(file_path, 'rb') as raw_file:
        rows = raw_file.read(10000)
        detected = chardet.detect(rows)
        encoding = detected.get('encoding', 'utf-8')
        logging.info("Detected encoding: %s for file %s", encoding, file_path)
    return encoding

def detect_ontology(label_col):
    label_lower = label_col.lower()
    if "disease" in label_lower or "ethnicity" in label_lower:
        return "efo"
    if "anatomical" in label_lower:
        return "uberon"
    if "cell type" in label_lower:
        return "cl"
    if "phenotypic" in label_lower:
        return "hp"
    if "organism" in label_lower:
        return "ncbitaxon"
    if "condition" in label_lower:
        return "xco"
    if "treatment" in label_lower:
        return "dron"
    return "efo"

def get_ols_term_id(label, label_col):
    """
    Query OLS for a label and return its ontology term id.
    If not found, return empty string.
    """
    ontology = detect_ontology(label_col)
    url = "https://www.ebi.ac.uk/ols/api/search"
    params = {"q": label, "ontology": ontology, "type": "class", "exact": "true"}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("response", {}).get("numFound", 0) > 0:
            doc = data["response"]["docs"][0]
            return doc.get("obo_id") or doc.get("iri")
        else:
            return ""
    except Exception:
        return ""

##############################################################################
#                                 SAVE LADDER                                #
##############################################################################        
def save_ladder(session, ladder_path):
    """
    Read ladder csv file into tables: Ladder and Ladder peaks.
    """
    # TODO: SAVE SPACE DONT SAVE SAME LADDER MANY TIMES
    ladder_encoding = detect_file_encoding(ladder_path)
    ladder_df = pd.read_csv(ladder_path, encoding=ladder_encoding)
    # Check for empty Peak or Basepairs
    if ladder_df["Peak"].isna().any() or ladder_df["Basepairs"].isna().any():
        raise ValueError("Ladder file contains empty Peak or Basepairs values.")
    # Create a new ladder
    ladder_name = None
    # Check if name exists
    if "Name" in ladder_df.columns and len(ladder_df) >= 2 and pd.notna(ladder_df.loc[1, "Name"]):
        ladder_name = str(ladder_df.loc[1, "Name"]).strip()
    new_ladder = Ladder(ladder_name=ladder_name)
    session.add(new_ladder)
    # Must flush because the ladder peaks depend on autoincrement value ladder_id
    session.flush()
    # Insert ladder peaks
    peaks = [
        LadderPeak(ladder_id=new_ladder.ladder_id,
                   peak=row["Peak"],
                   basepairs=float(row["Basepairs"]))
        for _, row in ladder_df.iterrows()
    ]
    session.add_all(peaks)
    logging.info("Saved ladder %s as ladder_id %s", ladder_name, new_ladder.ladder_id)
    return new_ladder

##############################################################################
#                           SAVE ONTOLOGY TERMS                              #
##############################################################################
def save_ontology_terms(session, metadata_path):
    """
    Save all ontology terms inside the metadata file to the database.
    Assume metadata file exists at metadata_path.
    """
    metadata_encoding = detect_file_encoding(metadata_path)
    meta_df = pd.read_csv(metadata_path, encoding=metadata_encoding)
    ontology_term_fields = [
        "Disease", "Cell Type", "Phenotypic Abnormality", "Treatment",
        "Ethnicity", "Organism", "Condition Under Study", "Material Anatomical Entity"
    ]
    # Loop through each ontology terms column in metadata
    for label_col in ontology_term_fields:
        if label_col not in meta_df.columns:
            continue
        for raw_value in meta_df[label_col].dropna():
            labels = [lbl.strip() for lbl in str(raw_value).split(";") if lbl.strip()]
            for label in labels:
                # Skip if this label already exists in DB
                exists = session.query(OntologyTerm).filter(
                    func.lower(OntologyTerm.term_label) == label.lower()
                ).first()
                if exists:
                    continue
                # Get term ID from OLS
                term_id = get_ols_term_id(label, label_col)
                if not term_id:  # None or empty string
                    term_id = str(uuid.uuid4())
                stmt = (
                    insert(OntologyTerm)
                    .values(term_id=term_id, term_label=label)
                    .on_conflict_do_nothing(index_elements=["term_id"])
                )
                session.execute(stmt)
    logging.info("Ontology terms saved successfully.")

##############################################################################
#                           SAVE GEL DEVICES                                 #
##############################################################################
def save_devices(session, metadata_path):
    """
    Save gel electrophoresis devices into database if not stored yet.
    Assume meadata file exists in metadata_path.
    """
    metadata_encoding = detect_file_encoding(metadata_path)
    meta_df = pd.read_csv(metadata_path, encoding=metadata_encoding)
    if "Gel Electrophoresis Device" not in meta_df.columns:
        return
    for raw_device in meta_df["Gel Electrophoresis Device"].dropna():
        devices = [d.strip() for d in str(raw_device).split(";") if d.strip()]
        for device_label in devices:
            stmt = (
                insert(GelElectrophoresisDevice)
                .values(device_name=device_label)
                .on_conflict_do_nothing(index_elements=["device_name"])
            )
            session.execute(stmt)
    logging.info("Device terms saved successfully.")

##############################################################################
#                           SAVE SUBJECTS (SAMPLES DONORS)                   #
##############################################################################
def save_subjects(session, metadata_path):
    """
    Save all subjects appearing in the metadata file in the path provided.
    If a subject_name appears multiple times in the same metadata file,
    only insert it once.
    NOTE: Different files can use the same subject_name, but they will be treated
    as different subjects and inserted multiple times.
    Assume metadata file exists at metadata_path.
    """
    metadata_encoding = detect_file_encoding(metadata_path)
    meta_df = pd.read_csv(metadata_path, encoding=metadata_encoding)
    seen_subjects = set()
    for _, row in meta_df.iterrows():
        # Fill fields if found
        subject_name = get_clean_value(row, "Subject ID")
        # Skip empty subject and None
        if not subject_name:
            continue
        # subject name already seen in this csv file -> do not insert to db
        if subject_name.lower() in seen_subjects:
            continue
        biological_sex = get_clean_value(row, "Biological Sex")
        ethnicity_label = get_clean_value(row, "Ethnicity")
        ethnicity_term_id = None
        # Ethnicty not None and not ""
        if ethnicity_label:
            term = session.query(OntologyTerm).filter(func.lower(OntologyTerm.term_label) == ethnicity_label.lower()).first()
            if term:
                ethnicity_term_id = term.term_id
        stmt = insert(Subject).values(
            subject_name=subject_name,
            biological_sex=biological_sex,
            ethnicity_term_id=ethnicity_term_id
        )
        session.execute(stmt)
        # Mark this subject as already added to db.
        seen_subjects.add(subject_name.lower())
    logging.info("Subjects saved successfully.")

##############################################################################
#                           SAVE TO SUBMISSION TABLE                         #
##############################################################################    
def save_submission(session, username, output_id):
    """
    Save the following submission info into database:
        username: Username of the submitter.
        output_id: Submission ID (UUID string).
        paths to files in file system on vm1 of analysis results.
    """
    # Insert submission row
    stmt = insert(Submission).values(
        submission_id=output_id,
        username=username,
        output_files_path=""  # temporary, will update after saving files
    ).on_conflict_do_nothing(index_elements=["submission_id"])
    session.execute(stmt)
    logging.info("Saved submission %s successfully.", output_id)

##############################################################################
#                          SAVE ANALYSIS TO DB                               #                 
##############################################################################
def save_data_to_db(output_id, username, signal_table_path, bp_translation_path, ladder_path, metadata_path):
    """
    Save signal table, bp translation, ladder and metadata to database VM1.
    """
    logging.info("Starting saving to database.")
    try:
        with Session(engine) as session:
            # Save ladder
            save_ladder(session, ladder_path)
            # Save metadata
            if os.path.exists(metadata_path):
                save_ontology_terms(session, metadata_path)
                save_devices(session, metadata_path)
                save_subjects(session, metadata_path)
            # Commit all together to ensure all or nothing writes (Atomicity)
            session.commit()
            logging.info("Saved all data to database successfully!")
    except Exception as e:
        logging.info("Error saving files to database: %s", e)
        # Revert all changes on exception
        with Session(engine) as session:
            session.rollback()

def save_data(app, output_id, username, save_to_db):
    """
    Save user data permanently in database and file system on VM1, if consent is given.
    """
    # No consent to save data to db, do nothing
    if save_to_db != 'yes':
        return
    # User consented, save
    user_folder = os.path.join(app.config['DOWNLOAD_FOLDER'], username, output_id)
    if not os.path.exists(user_folder):
        print(f"Folder not found: {user_folder}")
        return 
    ##############################################################################
    #                          SAVE TO FILE SYSTEM VM_1                          #                 
    ##############################################################################
    # Save only result files to file system in vm1
    statistics_files, peaks_files, other_result_files = get_result_files(user_folder)
    # Combine all paths
    all_files = []
    for f in statistics_files:
        all_files.append(os.path.join(user_folder, f['name']))
    for f in peaks_files:
        all_files.append(os.path.join(user_folder, f))
    for f in other_result_files:
        all_files.append(os.path.join(user_folder, f))
    # Prepare files to send
    files_to_send = []
    for path in all_files:
        if os.path.isfile(path):
            filename = os.path.basename(path)
            files_to_send.append(("files", (filename, open(path, "rb"))))
    data = {
        "username": username,
        "sample_id": output_id,
        "description": f"Results for submission {output_id}"
    }
    try:
        logging.info("Sending files to VM1...")
        response = requests.post(VM1_API_URL, files=files_to_send, data=data, timeout=10)
        logging.info("[save_data] VM1 response: %s %s", response.status_code, response.text)
    except requests.exceptions.RequestException as e:
        logging.info("[save_data] Error sending files to VM1: %s", e)
    finally:
        # Close all opened file
        for _, file_tuple in files_to_send:
            file_tuple[1].close()
    ##############################################################################
    #                          SAVE TO DATABASE VM_1                             #                 
    ##############################################################################
    # Save signal table, bp translation, ladder and metadata to database
    signal_table_path = os.path.join(user_folder, f"gel/signal_table.csv")
    bp_translation_path = os.path.join(user_folder, f"gel/qc/bp_translation.csv")
    metadata_path = os.path.join(user_folder, f"gel_meta_backup.csv")
    ladder_path = os.path.join(user_folder, f"gel_ladder.csv")
    save_data_to_db(output_id, username, signal_table_path, bp_translation_path, ladder_path, metadata_path)
