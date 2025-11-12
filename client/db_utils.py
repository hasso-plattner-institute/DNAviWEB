"""
This module handles data saving into database and file system of vm_1.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import json
import logging
import os
from pathlib import Path
import re
import uuid

import chardet
import pandas as pd
import requests
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from database.config import engine
from database.schema.file import File
from database.schema.gel_electrophoresis_devices import GelElectrophoresisDevice
from database.schema.ladder import Ladder
from database.schema.ladder_peak import LadderPeak
from database.schema.ladder_pixel import LadderPixel
from database.schema.ontology_term import OntologyTerm
from database.schema.sample import Sample
from database.schema.sample_pixel import SamplePixel
from database.schema.subject import Subject
from database.schema.submission import Submission
from database.schema.user_details import UserDetails
from .src.client_constants import VM1_API_URL
from .src.tools import get_all_files_except_saved_in_db

def get_clean_value(row, column_name):
    """
    Extract from column_name the value in row. 
    Return None if value in column is None or nan or empty, else return the value striped
    from whitesapces.
    """
    value = None
    if column_name in row:
        value = row[column_name]
    else: 
        return None
    if value is None:
        return None 
    value = str(value).strip()
    if value == "" or value.lower() == "nan":
        return None
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

@lru_cache(maxsize=1)
def load_ontology_map():
    """
    Load ontology mapping from JSON file, cached for performance.
    """
    base_dir = Path(__file__).parent
    json_path = base_dir / "static" / "json" / "ontology_map.json"
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)
    
def detect_ontology(label_col):
    """
    Detects the ontology type based on label_col.
    """
    ontology_map = load_ontology_map()
    label_lower = label_col.lower()
    for key, value in ontology_map.items():
        if key in label_lower:
            return value
    return ""

def get_ontology_prefix(label_col):
    """
    Return the correct term id prefix for a column.
    """
    ontology = detect_ontology(label_col).lower()
    if ontology == "pathogen":
        return "ncbitaxon"
    return ontology

def query_term_id(label, ontology, limit=10):
    """
    Returns results of autocomplete search.
    """
    ontology_lower = ontology.lower()
    try:
        if ontology_lower == "pathogen":
            # ENA taxonomy suggest-for-search (filter pathogens)
            url = f"https://www.ebi.ac.uk/ena/taxonomy/rest/suggest-for-search/{label}?dataPortal=pathogen&limit={limit}"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            results = r.json()
            transformed = [
                {
                    "label": f"{item['scientificName']} ({item.get('commonName', '')})",
                    "termId": f"NCBITaxon:{item['taxId']}"
                } for item in results
            ]
            return transformed
        else:
            # OLS lookup
            url = "https://www.ebi.ac.uk/ols/api/search"
            params = {"q": label, "ontology": ontology, "type": "class", "rows": limit}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            transformed = [
                {
                    "label": doc.get("label"),
                    "termId": doc.get("obo_id") or doc.get("iri")
                }
                for doc in data.get("response", {}).get("docs", [])
            ]
            return transformed
    except Exception as e:
        print("Query error:", e)
        return []

def get_ols_term_id(label, label_col):
    """
    Query OLS for a label and return its ontology term id.
    If not found, return empty string.
    """
    ontology = detect_ontology(label_col)
    results = query_term_id(label, ontology, limit=1)
    if results:
        return results[0].get("termId", "")
    return ""

##############################################################################
#                           SAVE TO SUBMISSION TABLE                         #
##############################################################################    
def save_submission(session, username, submission_id):
    """
    Save the following submission info into database:
        - username: Username of the submitter.
        - submission_id: Submission ID (UUID string).
    The submission row will be inserted, skipping duplicates if the same submission_id
    already exists.
    """
    # Check if user exists in the database
    existing_user = session.execute(
        select(UserDetails).where(UserDetails.username == username)
    ).scalar_one_or_none()
    # If the user does not exist in the database, this indicates a guest submission.
    # In that case, we create a guest user entry in the database (is_guest=True, no password).
    # NOTE: Guest users are only saved if they choose to save their data.
    # If they do not choose to save, their username is not stored.
    # This differs from registered users, whose username and password are already saved in the database during registration.
    # Therefore, if a username is not found in the database at this point, it is for sure a guest.
    if not existing_user:
        guest_user = UserDetails(
            username=username,
            password_hash=None,
            is_guest=True
        )
        session.add(guest_user)
        session.flush() # Flush to ensure username exists as FK in submission (even if we did not commit yet)
    # Insert submission row
    stmt = insert(Submission).values(
        submission_id=submission_id,
        username=username
    ).on_conflict_do_nothing(index_elements=["submission_id"])
    session.execute(stmt)
    logging.info("Saved submission %s successfully.", submission_id)

##############################################################################
#                          SAVE TO FILE SYSTEM VM_1                          #                 
##############################################################################
def save_file_system(submission_folder, username, submission_id):
    """
    Save result files via http request from submission number: submission_id 
    of the user: username, to the file system on vm1. 
    Save all except already saved in DB.
    """
    # Save all files (except files that will be saved to db)to file system in vm1
    all_files_relative_path = get_all_files_except_saved_in_db(submission_folder)
    # Prepare files to send
    files_to_send = []
    for relative_path in all_files_relative_path:
        full_path = os.path.join(submission_folder, relative_path)
        if os.path.isfile(full_path):
            files_to_send.append(("files", (relative_path, open(full_path, "rb"))))
    data = {
        "username": username,
        "submission_id": submission_id,
        "description": f"Results for submission {submission_id}"
    }
    try:
        logging.info("Sending files to VM1...")
        # Send files via HTTP request to VM1, 10 sec connect timeout, 300 sec time to upload and process file transfer
        VM1_API_URL_UPLOAD = f"{VM1_API_URL}/upload"
        response = requests.post(VM1_API_URL_UPLOAD, files=files_to_send, data=data, timeout=(10, 300))
        response.raise_for_status()
        vm1_data = response.json()
        saved_files_paths = vm1_data.get("saved_files", [])
        logging.info("Success saving files to file system VM1.")
        return saved_files_paths
    except requests.exceptions.RequestException as e:
        if response is not None:
            logging.error("Failed to save to VM1. Status code: %s, Response: %s", 
                          response.status_code, response.text)
        logging.error("Exception while sending files to VM1: %s", e)
        raise RuntimeError("Failed to save files to VM1") from e
    finally:
        # Close all opened file
        for _, file_tuple in files_to_send:
            file_tuple[1].close()

##############################################################################
#                          DELETE FROM FILE SYSTEM                           #                 
##############################################################################
def delete_file_system(username, submission_id):
    """
    Delete from file system on vm1, for user: username and submission_id
    """
    # VM1 cleanup
    try:
        delete_url = f"{VM1_API_URL}/delete"
        data = {"username": username, "submission_id": str(submission_id)}
        requests.delete(delete_url, json=data, timeout=(10, 50))
        logging.info("Files deleted successfully on VM1 after DB failure.")
    except Exception as e:
        logging.error("Failed to delete files from VM1: %s", e)

##############################################################################
#                           SAVE TO SUBMISSION TABLE                         #
##############################################################################    
def save_file_paths_to_db(session, submission_id, saved_files_paths):
    """
    Save the following files info into database:
        - submission_id: What submission the files belong to.
        - saved_files_paths: Relative paths to files saved on file system on vm1.
    """
    if not saved_files_paths:
        raise ValueError("No file paths provided to save to database.")
    try:
        # Save each file path
        for path in saved_files_paths:
            file_record = File(
                file_id=uuid.uuid4(),
                submission_id=submission_id,
                file_name=os.path.basename(path),
                relative_path=path
            )
            session.add(file_record)
        logging.info("Saved file paths to db successfully.")
    except Exception as e:
        logging.error("Error saving file paths to database: %s", e)
        raise

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
    return new_ladder.ladder_id

##############################################################################
#                                 SAVE LADDER PIXEL                          #
##############################################################################   
def save_ladder_pixel(session, signal_table_path, bp_translation_path, ladder_id):
    # Load files
    signal_table_encoding = detect_file_encoding(signal_table_path)
    bp_translation_encoding = detect_file_encoding(bp_translation_path)
    signal_table = pd.read_csv(signal_table_path, encoding=signal_table_encoding, dtype=str)
    bp_translation = pd.read_csv(bp_translation_path, encoding=bp_translation_encoding, dtype=str)
    # Parse signal_table: first column 'Ladder' pixel intensity
    pixel_intensities = signal_table['Ladder'].values
    # Parse bp_translation: column 'Ladder' base_pair_position
    bp_positions = bp_translation['Ladder'].values
    n = max(len(bp_positions), len(pixel_intensities))
    ladder_pixels = [
        LadderPixel(
            ladder_id=ladder_id,
            pixel_order=i,
            pixel_intensity=to_decimal_safe(pixel_intensities[i]) if pd.notnull(pixel_intensities[i]) else None, 
            base_pair_position=to_decimal_safe(bp_positions[i]) if pd.notnull(bp_positions[i]) else None
        )
        for i in range(n)
    ]
    session.add_all(ladder_pixels)
    logging.info("Saved ladder pixels successfully.")

##############################################################################
#                           SAVE ONTOLOGY TERMS                              #
##############################################################################
def save_ontology_terms(session, metadata_path):
    """
    Save all ontology terms inside the metadata file to the database.
    Assume metadata file exists at metadata_path.
    Returns mappings: {ontology_column_name: {term_label: term_id}}
    """
    metadata_encoding = detect_file_encoding(metadata_path)
    meta_df = pd.read_csv(metadata_path, encoding=metadata_encoding)
    ontology_term_fields = [
        "Disease", "Cell Type", "Phenotypic Abnormality", "Treatment",
        "Ethnicity", "Organism", "Condition Under Study", "Material Anatomical Entity",
        "Infection Strain"
    ]
    ontology_label_to_id = {col: {} for col in ontology_term_fields}
    # Loop through each ontology terms column in metadata
    for label_col in ontology_term_fields:
        if label_col not in meta_df.columns:
            continue
        for raw_value in meta_df[label_col].dropna():
            labels = [lbl.strip() for lbl in str(raw_value).split(";") if lbl.strip()]
            for label in labels:
                # If this label already exists in DB do not save
                exists = session.query(OntologyTerm).filter(
                    func.lower(OntologyTerm.term_label) == label.lower()
                ).first()
                if exists:
                    term_id = exists.term_id
                # New label -> Store to DB
                else:
                    # Get term ID from OLS
                    term_id = get_ols_term_id(label, label_col)
                    if not term_id or not term_id.lower().startswith(get_ontology_prefix(label_col)):  # None or empty string or term_id not from the ontology
                        #term_id = str(uuid.uuid4())
                        continue
                    stmt = (
                        insert(OntologyTerm)
                        .values(term_id=term_id, term_label=label)
                        .on_conflict_do_nothing(index_elements=["term_id"])
                    )
                    session.execute(stmt)
                ontology_label_to_id[label_col][label] = term_id
    logging.info("Ontology terms saved successfully.")
    return ontology_label_to_id

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
    col_name = "Gel Electrophoresis Device"
    if "Gel Electrophoresis Device" not in meta_df.columns:
        return
    device_name_to_id = {col_name: {}}
    for raw_device in meta_df[col_name].dropna():
        devices_names = [d.strip() for d in str(raw_device).split(";") if d.strip()]
        for device_name in devices_names:
            # Check if device already exists
            exists = session.query(GelElectrophoresisDevice).filter(
                func.lower(GelElectrophoresisDevice.device_name) == device_name.lower()
            ).first()
            if exists:
                device_id = exists.device_id
            else:
                stmt = (
                    insert(GelElectrophoresisDevice)
                    .values(device_name=device_name)
                    .returning(GelElectrophoresisDevice.device_id)
                )
                result = session.execute(stmt)
                device_id = result.scalar()
            device_name_to_id[col_name][device_name] = device_id
    logging.info("Device terms saved successfully.")
    return device_name_to_id

##############################################################################
#                           SAVE SUBJECTS (SAMPLES DONORS)                   #
##############################################################################
def save_subjects(session, metadata_path, ontology_label_to_id):
    """
    Save all subjects appearing in the metadata file in the path provided.
    If a subject_name appears multiple times in the same metadata file,
    only insert it once. Each empty subject_name we assume the sample belongs to
    a new subject and give it a completely new ID.
    NOTE: Different files can use the same subject_name, but they will be treated
    as different subjects and inserted multiple times.
    Assume metadata file exists at metadata_path.
    """
    metadata_encoding = detect_file_encoding(metadata_path)
    meta_df = pd.read_csv(metadata_path, encoding=metadata_encoding)
    seen_subjects = {}
    sample_to_subject_id = {}
    for _, row in meta_df.iterrows():
        subject_name = get_clean_value(row, "Subject ID")
        sample_value = get_clean_value(row, "SAMPLE")
        biological_sex = get_clean_value(row, "Biological Sex")
        ethnicity_label = get_clean_value(row, "Ethnicity")
        ethnicity_term_id = None
        # Map ethnicity label to term_id
        if ethnicity_label:
            term = session.query(OntologyTerm)\
                .filter(func.lower(OntologyTerm.term_label) == ethnicity_label.lower())\
                .first()
            if term:
                ethnicity_term_id = term.term_id
        # Determine if we need to insert
        if subject_name:
            key = subject_name.lower()
            if key in seen_subjects:
                subject_id = seen_subjects[key]
            else:
                new_subject = Subject(
                    subject_id=uuid.uuid4(),
                    subject_name=subject_name,
                    biological_sex=biological_sex,
                    ethnicity_term_id=ethnicity_term_id,
                    organism_term_id = map_term("Organism", row.get("Organism"), ontology_label_to_id)
                )
                session.add(new_subject)
                session.flush()
                subject_id = new_subject.subject_id
                seen_subjects[key] = subject_id
        # No subject name found -> create new unique subject id and None name
        else:
            new_subject = Subject(
                subject_id=uuid.uuid4(),
                subject_name=None,
                biological_sex=biological_sex,
                ethnicity_term_id=ethnicity_term_id,
                organism_term_id = map_term("Organism", row.get("Organism"), ontology_label_to_id)
            )
            session.add(new_subject)
            session.flush()
            subject_id = new_subject.subject_id
        sample_to_subject_id[sample_value] = subject_id
    logging.info("Subjects saved successfully.")
    return sample_to_subject_id

def is_valid_metadata(metadata_path, expected_sample_count):
    """
    Checks if metadata file is valid for saving Sample table.
    Conditions:
    - File exists.
    - Contains 'SAMPLE' column.
    - Number of rows matches expected_sample_count.
    - All SAMPLE names are non-empty and unique.
    return: True if metadata file valid, else False.
    """
    if not metadata_path or not os.path.exists(metadata_path):
        return False
    try:
        metadata_encoding = detect_file_encoding(metadata_path)
        metadata = pd.read_csv(metadata_path, encoding=metadata_encoding)
    except Exception:
        return False
    if 'SAMPLE' not in metadata.columns:
        return False
    sample_names = metadata['SAMPLE'].astype(str).str.strip().tolist()
    if len(sample_names) != expected_sample_count:
        return False
    if any(name is None or str(name).strip() == "" for name in sample_names):
        return False
    if len(set(sample_names)) != expected_sample_count:
        return False
    return True

def map_term(col_name, label, label_to_id):
    """
    Return the term_id according to OLS of the label (i.e. Cancer) 
    and col_name (i.e. Disease) in the dictionary label_to_id.
    Map labels to term_ids using the dictionary
    """
    if label is None or pd.isna(label):
        return None
    if isinstance(label, str):
        key = label.strip()
    else:
        key = label
    return label_to_id.get(col_name, {}).get(key, None)

def yes_no_to_bool(val):
    """
    This method is for the boolean answers we receive from frontend.
    If the received answer val == 'Yes', return True; if val == 'No', return False.
    """
    if pd.isna(val):
        return None
    val_str = str(val).strip().lower()
    if val_str == "yes":
        return True
    elif val_str == "no":
        return False
    return None

##############################################################################
#                                 SAVE SAMPLE                                #
##############################################################################
def save_samples(session, signal_table_path, metadata_path, submission_id,
                 ladder_id, ontology_label_to_id=None, device_name_to_id=None,
                 sample_to_subject_id=None):
    """
    Save Sample entries to the database.
    - Always determine number of samples from signal_table.
    - If metadata exists and contains 'SAMPLE', use its unique values as sample names.
    - If metadata missing or invalid, fall back to signal table column names (numbers 1,2,3).
    """
    # Read signal table to find number of samples
    signal_encoding = detect_file_encoding(signal_table_path)
    signal_table = pd.read_csv(signal_table_path, encoding=signal_encoding)
    signal_sample_names = [col for col in signal_table.columns if col != "Ladder"]
    sample_names = signal_sample_names
    metadata = None
    if is_valid_metadata(metadata_path, expected_sample_count=len(signal_sample_names)):
        metadata_encoding = detect_file_encoding(metadata_path)
        metadata = pd.read_csv(metadata_path, encoding=metadata_encoding)
        sample_names = metadata['SAMPLE'].tolist()
    if ontology_label_to_id is None:
        ontology_label_to_id = {}
    if device_name_to_id is None:
        device_name_to_id = {}
    if sample_to_subject_id is None:
        sample_to_subject_id = {}
    predefined_columns = [
        "SAMPLE", "Subject ID", "Disease", "Phenotypic Abnormality", "Cell Type",
        "Sample Type", "Sample Collection Date", "Age", "Material Anatomical Entity",
        "Case vs Control", "Condition Under Study", "Is Deceased?", "Is Pregnant?",
        "Is Infection Suspected?", "Infection Strain", "Hospitalization Status",
        "Extraction Kit (DNA Isolation Method)", "DNA Mass", "DNA Mass Units", "Ladder Type",
        "Carrying Liquid Volume", "Carrying Liquid Volume Unit", "Gel Electrophoresis Device",
        "In vitro / In vivo", "Treatment", "Ethnicity", "Biological Sex", "Organism", "Actions"
    ]
    sample_ids_in_order = []
    for i, col_name in enumerate(signal_sample_names):
        # Pick sample name from metadata if available
        sample_name = sample_names[i] if i < len(sample_names) else col_name
        sample_data = {
            "sample_name": str(sample_name),
            "submission_id": submission_id,
            "ladder_id": ladder_id
        }
        if metadata is not None and i < len(metadata):
            row = metadata.iloc[i]
            # Find subject id if exists
            sample_name = row.get("SAMPLE")
            subject_id = sample_to_subject_id.get(str(sample_name).strip()) if sample_name else None
            sample_data.update({
                "subject_id": subject_id,
                "disease_term_id": map_term("Disease", row.get("Disease"), ontology_label_to_id),
                "phenotypic_abnormality_term_id": map_term("Phenotypic Abnormality", row.get("Phenotypic Abnormality"), ontology_label_to_id),
                "treatment_term_id": map_term("Treatment", row.get("Treatment"), ontology_label_to_id),
                "cell_type_term_id": map_term("Cell Type", row.get("Cell Type"), ontology_label_to_id),
                "sample_type": row.get("Sample Type"),
                "sample_collection_date": (datetime.strptime(row.get("Sample Collection Date"), "%Y-%m-%d").date() 
                           if pd.notnull(row.get("Sample Collection Date")) and re.match(r"\d{4}-\d{2}-\d{2}$", str(row.get("Sample Collection Date"))) 
                           else None),
                "age_at_collection": float(row.get("Age")) if pd.notnull(row.get("Age")) else None,
                "sampling_site_term_id": map_term("Material Anatomical Entity", row.get("Material Anatomical Entity"), ontology_label_to_id),
                "case_vs_control": row.get("Case vs Control"),
                "condition_under_study_term_id": map_term("Condition Under Study", row.get("Condition Under Study"), ontology_label_to_id),
                "is_deceased": yes_no_to_bool(row.get("Is Deceased?")),
                "is_pregnant": yes_no_to_bool(row.get("Is Pregnant?")),
                "is_infection_suspected": yes_no_to_bool(row.get("Is Infection Suspected?")),
                "infection_strain": map_term("Infection Strain", row.get("Infection Strain"), ontology_label_to_id),
                "hospitalization_status": row.get("Hospitalization Status"),
                "extraction_kit": row.get("Extraction Kit (DNA Isolation Method)"),
                "dna_mass": float(row.get("DNA Mass")) if pd.notnull(row.get("DNA Mass")) else None,
                "dna_mass_units": row.get("DNA Mass Units"),
                "carrying_liquid_volume": float(row.get("Carrying Liquid Volume")) if pd.notnull(row.get("Carrying Liquid Volume")) else None,
                "carrying_liquid_volume_unit": row.get("Carrying Liquid Volume Unit"),
                "in_vitro_in_vivo": row.get("In vitro / In vivo"),
                # TODO: DO NOT ALLOW IN A SUBMISSION MULTIPLE DEVICE ID
                "gel_electrophoresis_device_id": map_term("Gel Electrophoresis Device", row.get("Gel Electrophoresis Device"), device_name_to_id)
            })
            # Add custom attributes for all extra columns
            custom_attributes = {}
            for col in row.index:
                if col not in predefined_columns:
                    val = row[col]
                    if pd.notnull(val):
                        custom_attributes[col] = val
            if custom_attributes:
                sample_data["custom_sample_attributes"] = custom_attributes
        sample = Sample(**sample_data)
        # Save sample
        session.add(sample)
        session.flush()  # ensure sample_id is populated
        sample_ids_in_order.append(sample.sample_id)
    logging.info("Saved %d samples successfully.", len(sample_ids_in_order))
    return sample_ids_in_order

def to_decimal_safe(value):
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None
    
##############################################################################
#                                 SAVE SAMPLE PIXEL                          #
##############################################################################   
def save_sample_pixel(session, signal_table_path, bp_translation_path, sample_ids_in_order):
    """
    Save sample pixels from signal table and bp translation table into the database.
    - signal_table: CSV with columns ['Ladder', 1, 2, ...] representing pixel intensities.
    - bp_translation: CSV with columns ['','Ladder', 1, 2, ...] representing base pair positions.
    - sample_ids_in_order: List of sample IDs in the order corresponding to columns in signal_table (excluding 'Ladder').
    Assumes signal_table and bp_translation have the same number of sample columns and rows.
    """
    logging.info("Start saving sample pixels")
    # Load files
    signal_table_encoding = detect_file_encoding(signal_table_path)
    bp_translation_encoding = detect_file_encoding(bp_translation_path)
    signal_table = pd.read_csv(signal_table_path, encoding=signal_table_encoding, dtype=str).iloc[:, 1:] # remove first col
    bp_translation = pd.read_csv(bp_translation_path, encoding=bp_translation_encoding, dtype=str).iloc[:, 2:] # remove first two col 
    if signal_table.shape[1] != len(sample_ids_in_order):
        raise ValueError(f"Number of samples in signal table {signal_table.shape[1]} does not match provided sample IDs {len(sample_ids_in_order)}.")
    # Loop over samples
    for i, sample_id in enumerate(sample_ids_in_order):
        pixel_intensities = signal_table.iloc[:, i].values
        bp_positions = bp_translation.iloc[:, i].values
        n = max(len(bp_positions), len(pixel_intensities))
        sample_pixels = [
            SamplePixel(
                sample_id=sample_id,
                pixel_order=j,
                pixel_intensity=to_decimal_safe(pixel_intensities[j]) if pd.notnull(pixel_intensities[j]) else None, 
                base_pair_position = to_decimal_safe(bp_positions[j]) if pd.notnull(bp_positions[j]) else None
            )
            for j in range(n)
        ]
        session.add_all(sample_pixels)
    logging.info("Saved %d sample pixels successfully.", len(sample_ids_in_order))

##############################################################################
#                          SAVE ANALYSIS TO DB                               #                 
##############################################################################
def save_data_to_db(submission_id, username, signal_table_path, bp_translation_path, ladder_path, metadata_path, saved_files_paths):
    """
    Save signal table, bp translation, ladder and metadata to database VM1.
    """
    logging.info("Starting saving to database.")
    try:
        with Session(engine) as session:
            # Save submisson
            save_submission(session, username, submission_id)
            # Save file paths to File table
            save_file_paths_to_db(session, submission_id, saved_files_paths)
            # Save ladder
            ladder_id = save_ladder(session, ladder_path)
            save_ladder_pixel(session, signal_table_path, bp_translation_path, ladder_id)
            ontology_label_to_id = None
            device_name_to_id = None
            sample_to_subject_id = None
            # Save metadata
            if os.path.exists(metadata_path):
                ontology_label_to_id = save_ontology_terms(session, metadata_path)
                device_name_to_id = save_devices(session, metadata_path)
                sample_to_subject_id = save_subjects(session, metadata_path, ontology_label_to_id)
            # Save sample table
            sample_ids_in_order = save_samples(session, signal_table_path, metadata_path,
                                               submission_id,ladder_id, ontology_label_to_id,
                                               device_name_to_id, sample_to_subject_id)
            save_sample_pixel(session, signal_table_path, bp_translation_path, sample_ids_in_order)
            # Commit all together to ensure all or nothing writes (Atomicity)
            session.commit()
            logging.info("Saved all data to database successfully!")
    except Exception as e:
        logging.info("Error saving files to database: %s", e)
        # Revert all changes on exception
        with Session(engine) as session:
            session.rollback()
        # Delete from file system all saved files on exception
        delete_file_system(username, submission_id)

def save_data(app, submission_id, username, save_to_db):
    """
    Save user data permanently in database and file system on VM1, if consent is given.
    """
    # No consent to save data to db, do nothing
    if save_to_db != 'yes':
        return
    # User consented, save
    submission_folder = os.path.join(app.config['DOWNLOAD_FOLDER'], username, submission_id)
    if not os.path.exists(submission_folder):
        logging.info(f"Folder not found: {submission_folder}")
        return 
    ##############################################################################
    #                          SAVE TO FILE SYSTEM VM_1                          #                 
    ##############################################################################
    # Save files to file system and return the paths on vm_1 to store in DB
    # If saving to file system failed, skip saving.
    #saved_files_paths = ["file_path1", "file_path_2"]
    try:
        saved_files_paths = save_file_system(submission_folder, username, submission_id)
    except Exception as e:
        logging.info("Failed to save to file system: %s", e)
        return
    ##############################################################################
    #                          SAVE TO DATABASE VM_1                             #                 
    ##############################################################################
    # Save signal table, bp translation, ladder and metadata to database
    signal_table_csv = os.path.join(submission_folder, "electropherogram", "signal_table.csv")
    # If signal_table.csv exists (image uploaded)-> save it
    if os.path.isfile(signal_table_csv):
        signal_table_path = signal_table_csv
    # else (csv uploaded)-> save the uploaded csv
    else:
        signal_table_path = os.path.join(submission_folder, "electropherogram.csv")
    bp_translation_path = os.path.join(submission_folder, f"electropherogram/qc/bp_translation.csv")
    metadata_path = os.path.join(submission_folder, f"electropherogram_meta_all.csv")
    ladder_path = os.path.join(submission_folder, f"electropherogram_ladder.csv")
    save_data_to_db(submission_id, username, signal_table_path, bp_translation_path, ladder_path, metadata_path, saved_files_paths)

def rebuild_electropherogram_and_bp_translation(submission_id, submission_folder):
    """
    Rebuild the signal table and bp_translation from DB and save as csv
    """
    try:
        with Session(engine) as session:
            # Get all samples for this submission in order
            samples = session.query(Sample).filter(Sample.submission_id == submission_id).order_by(Sample.sample_id).all()
            if not samples:
                logging.warning(f"No samples found for submission {submission_id}")
                return None
            sample_ids = [s.sample_id for s in samples]
            sample_names = [s.sample_name for s in samples]
            # Get ladder_id from first sample (assume all samples in a submission use same ladder)
            ladder_id = samples[0].ladder_id
            ladder_pixels = session.query(LadderPixel).filter(LadderPixel.ladder_id == ladder_id).order_by(LadderPixel.pixel_order).all()
            ladder_values = [p.pixel_intensity for p in ladder_pixels]
            bp_positions = [p.base_pair_position for p in ladder_pixels]
            max_pixels = len(ladder_values)
            # Fetch all sample pixels
            pixels_query = session.query(SamplePixel).filter(SamplePixel.sample_id.in_(sample_ids)).order_by(SamplePixel.pixel_order).all()
            # Build electropherogram.csv (pixel intensities)
            df_signal = pd.DataFrame(index=range(max_pixels))
            df_signal['Ladder'] = ladder_values
            for i, sample_id in enumerate(sample_ids):
                col_pixels = [None]*max_pixels
                for p in pixels_query:
                    if p.sample_id == sample_id and p.pixel_order < max_pixels:
                        col_pixels[p.pixel_order] = p.pixel_intensity
                df_signal[sample_names[i]] = col_pixels
            # Build bp_translation.csv (base pair positions)
            df_bp = pd.DataFrame(index=range(max_pixels))
            df_bp['Ladder'] = bp_positions
            for i, sample_id in enumerate(sample_ids):
                col_bp = [None]*max_pixels
                for p in pixels_query:
                    if p.sample_id == sample_id and p.pixel_order < max_pixels:
                        col_bp[p.pixel_order] = p.base_pair_position
                df_bp[sample_names[i]] = col_bp
            # Save both files
            electro_path = os.path.join(submission_folder, "electropherogram.csv")
            df_signal.to_csv(electro_path, index=False)
            bp_dir = os.path.join(submission_folder, "electropherogram", "qc")
            os.makedirs(bp_dir, exist_ok=True)
            bp_path = os.path.join(bp_dir, "bp_translation.csv")
            df_bp.to_csv(bp_path, index=False)
            logging.info(f"Rebuilt electropherogram.csv and bp_translation.csv from DB for submission {submission_id}")
            return electro_path, bp_path
    except Exception as e:
        logging.error(f"Error rebuilding electropherogram and bp_translation CSVs for submission {submission_id}: {e}")
        return None, None
