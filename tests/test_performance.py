# This module measure the response time of the /protect endpoint 
# in different scenarios using concurrent requests.
# This is a templare PLACEHOLDER must be replaced with real credentials before use.
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import time
import csv
results = {
    'login': {},
    'register': {},
    'protect_no_save': {},
    'protect_save': {},
    'results_temp': {},
    'dashboard': {}
}
base_path = Path(__file__).parent.parent
DATA_FILE = base_path / 'client' / 'static' / 'tests' / 'electropherogram.csv'
META_FILE = base_path / 'tests' / 'data' / 'metadata_success.csv'
################################################################
#                  LOGIN                                       #
################################################################
def run_login(user_id=0, user_count=1):
    data = {'username': 'PLACEHOLDER', 'pw': 'PLACEHOLDER'}
    start = time.time()
    response = requests.post('https://dnavi.sc.hpi.de/login', data=data)
    end = time.time()
    results['login'].setdefault(user_count, []).append(end - start)

for NUM_USERS in [1, 5, 10, 15, 20]:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            executor.submit(run_login, i, NUM_USERS)

################################################################
#                  REGISTER                                    #
################################################################
def run_register(user_id=0, user_count=1):
    data = {'username': f'PLACEHOLDER{user_id}', 'pw': 'PLACEHOLDER'}
    start = time.time()
    response = requests.post('https://dnavi.sc.hpi.de/register', data=data)
    end = time.time()
    results['register'].setdefault(user_count, []).append(end - start)

for NUM_USERS in [1, 5, 10, 15, 20]:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            executor.submit(run_register, i, NUM_USERS)
            
################################################################
#                  PROTECT NO SAVE                             #
################################################################
# Function to measure response time of /protect endpoint without saving to DB
# The time is from starting the analysis until receiving the response which is the results
# page.
def run_protect_no_saving(user_id=0, user_count=1):
    with DATA_FILE.open('rb') as f1, META_FILE.open('rb') as f3:
        files = {
            'data_file': ('electropherogram.csv', f1, 'text/csv'),
            'meta_file': ('metadata.csv', f3, 'text/csv')
        }
        data = {
            'ladder_file': 'HSD5000',
            'save_to_db': 'no'
        }
        start = time.time()
        response = requests.post(
            'https://dnavi.sc.hpi.de/protect',
            files=files,
            data=data,
            cookies={'session': 'PLACEHOLDER'}
        )
        end = time.time()
        results['protect_no_save'].setdefault(user_count, []).append(end - start)
        
for NUM_USERS in [1, 5, 10, 15, 20]:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            executor.submit(run_protect_no_saving, i, NUM_USERS)

################################################################
#                  PROTECT SAVE                             #
################################################################
# Function to measure response time of /protect endpoint with saving to DB
# The time is from starting the analysis, saving to db, until receiving the response which is the results
# page.
def run_protect_save(user_id=0, user_count=1):
    with DATA_FILE.open('rb') as f1, META_FILE.open('rb') as f3:
        files = {
            'data_file': ('electropherogram.csv', f1, 'text/csv'),
            'meta_file': ('metadata.csv', f3, 'text/csv')
        }
        data = {
            'ladder_file': 'HSD5000',
            'save_to_db': 'yes'
        }
        start = time.time()
        response = requests.post(
            'https://dnavi.sc.hpi.de/protect',
            files=files,
            data=data,
            cookies={'session': 'PLACEHOLDER'}
        )
        end = time.time()
        results['protect_save'].setdefault(user_count, []).append(end - start)
        
# Simulate 5 concurrent users
for NUM_USERS in [1, 5, 10, 15, 20]:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            executor.submit(run_protect_save, i, NUM_USERS)

################################################################
#                  RESULTS  (On VM2)                           #
################################################################
def run_results(user_id=0, user_count=1):
    start = time.time()
    response = requests.get('https://dnavi.sc.hpi.de/results/b1ce7fb7-e64b-44c5-bbe1-19a616035859', cookies={'session': 'PLACEHOLDER'})
    end = time.time()
    results['results_temp'].setdefault(user_count, []).append(end - start)

for NUM_USERS in [1, 5, 10, 15, 20]:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            executor.submit(run_results, i)

################################################################
#                  RESULTS  (On VM1)                           #
################################################################

# Submissions that for testing purposes were forced to be deleted from VM_2 and are only on VM_1
# username PLACEHOLDER
# first removed all those folders from vm2:
"""
rm -rf "subm_1" \
"subm_2" ...
]
"""
# after removing them from vm2, try to access those results
# replace here with the real submission ids
submission_ids = [
    # 1
    "subm_1",
    # 5
    "subm_2", "subm_3", "subm_4", "subm_5", "subm_6",
    # 10
    "subm_7", "subm_8", "subm_9", "subm_10", "subm_11",
    "subm_12", "subm_13", "subm_14", "subm_15", "subm_16",
    # 15
    "subm_17","subm_18","subm_19","subm_20","subm_21",
    "subm_22","subm_23","subm_24","subm_25","subm_26",
    "subm_27","subm_28","subm_29","subm_30","subm_31",
    # 20
    "subm_32","subm_33","subm_34","subm_35","subm_36",
    "subm_37","subm_38","subm_39","subm_40","subm_41",
    "subm_42","subm_43","subm_44","subm_45","subm_46",
    "subm_47","subm_48","subm_49","subm_50","subm_51"
]

# First log in
def create_logged_in_session():
    s = requests.Session()
    resp = s.post(
        "https://dnavi.sc.hpi.de/login",
        data={"username": "PLACEHOLDER", "pw": "PLACEHOLDER"}
    )
    if resp.status_code != 200:
        raise RuntimeError("Login failed")
    return s
# Now try via this user that has those submissions already deleted from vm2, to retrieve the results from vm1
def run_results_on_vm1(submission_id, user_count=1):
    session = create_logged_in_session()
    start = time.time()
    response = session.get(
        f'https://dnavi.sc.hpi.de/results/{submission_id}'
    )
    end = time.time()
    results['results_vm1'].setdefault(user_count, []).append(end - start)

user_batches = [1, 5, 10, 15, 20]
index = 0
for NUM_USERS in user_batches:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            submission_id = submission_ids[index]
            executor.submit(run_results_on_vm1, submission_id, NUM_USERS)
            index += 1
            
################################################################
#                 SUBMISSIONS                                 #
################################################################
def run_sub_dashboard(user_id=0, user_count=1):
    start = time.time()
    response = requests.get('https://dnavi.sc.hpi.de/submissions_dashboard', cookies={'session': 'PLACEHOLDER'})
    end = time.time()
    results['dashboard'].setdefault(user_count, []).append(end - start)
    
for NUM_USERS in [1, 5, 10, 15, 20]:
    with ThreadPoolExecutor(max_workers=NUM_USERS) as executor:
        for i in range(NUM_USERS):
            executor.submit(run_sub_dashboard, i, NUM_USERS)

################################################################
#                  WRITE ALL RESPONSE TIMES TO CSV             #
################################################################
def write_results_to_csv(results, filename='full_results.csv'):
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['category', 'concurrent_users', 'response_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for category, user_dict in results.items():
            for user_count, times in user_dict.items():
                for t in times:
                    writer.writerow({'category': category, 'concurrent_users': user_count, 'response_time': t})

write_results_to_csv(results)