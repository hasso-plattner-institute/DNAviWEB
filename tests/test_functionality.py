"""
This module was implemented following the DigitalOcean guide: https://www.digitalocean.com/community/tutorials/unit-test-in-flask
tests the web server.
"""
# Run one test: PYTHONPATH=$(pwd) pytest  --html=report.html --self-contained-html tests/test_dnaviweb.py::test_home_page
# Run all tests: PYTHONPATH=$(pwd) pytest --html=report.html --self-contained-html tests/
from datetime import datetime
from pathlib import Path
import re
import sys
import os
from io import BytesIO
from uuid import uuid4
import pytest

from database.config import SessionLocal
from database.schema.sample import Sample
from database.schema.submission import Submission
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from client.app import app


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

# First part of the testing is checking basic page retrievals
def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Welcome to DNAvi' in response.data
    
def test_citation(client):
    response = client.get('/citation')
    assert response.status_code == 200
    assert b'About DNAvi' in response.data

# Second part of the testing is creating a test user and logging in
# then creating different scenarios with this user and checking web server
# and database responses
def test_registration_login_success(client):
    # First register as a new user
    response = client.post('/register', data={
        'username': 'testuser',
        'pw': 'testpassword'
    })
    # If successful registration, should redirect to login page (302)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')
    # Login
    response = client.post('/login', data={
        'username': 'testuser',
        'pw': 'testpassword'
    })
    # If login successful, should redirect to submissions dashboard (302)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/submissions_dashboard')
    
# Test registering with existing username
# Or login with wrong credentials
def test_registration_login_fail(client):
    # Must not register with an existing username
    response = client.post('/register', data={
        'username': 'testuser',
        'pw': 'testpassword'
    })
    # If NOT successful registration -> 200 (Flask success)
    assert response.status_code == 200
    assert b"User already exists" in response.data
    # Login with wrong password
    response = client.post('/login', data={
        'username': 'testuser',
        'pw': 'wrongpassword'
    })
    # If login NOT successful -> 200 (Flask success)
    assert response.status_code == 200
    assert b"Login failed: incorrect username or password" in response.data

# In this section we are logged in as the test user, the next part is testing the analysis submission
# with different scenarios.
#client.tests.electropherogram.csv
#client.tests.size_standard.csv
#data.metadata_same_subject_different_sex.csv
def test_protect_valid_inputs(client):
    login_response = client.post(
        '/login',
        data={'username': 'testuser', 'pw': 'testpassword'},
        follow_redirects=False
    )
    assert login_response.status_code == 302
    base_path = Path(__file__).parent.parent
    electropherogram_path = base_path / 'client' / 'static' / 'tests' / 'electropherogram.csv'
    metadata_path = base_path / 'tests' / 'data' / 'metadata_success.csv'
    with electropherogram_path.open('rb') as f1, \
         metadata_path.open('rb') as f3:
        data = {
            'save_to_db': 'yes',
            'data_file': (BytesIO(f1.read()), 'electropherogram.csv'),
            'ladder_file': ['HSD5000'],
            'meta_file': (BytesIO(f3.read()), 'metadata.csv'),
        }
        response = client.post(
            '/protect',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )
    # check is the response the results page
    assert response.status_code == 200
    assert b"View your analysis interactively" in response.data
    html = response.data.decode('utf-8')
    match = re.search(r'/results/([0-9a-f-]{36})', html)
    submission_id = match.group(1)
    db = SessionLocal()
    # Check that the submission id exists in the database
    try:
        db.query(Sample).delete()
        db.query(Submission).delete()
        db.commit()
        sub = db.query(Submission).filter_by(submission_id=submission_id).first()
        assert sub is not None
        assert sub.username == 'testuser'
        # check 6 new samples added with this submission id
        samples_count = db.query(Sample).filter_by(submission_id=submission_id).count()
        assert samples_count == 6
        # Check that these 6 samples belong to 3 distinct subjects
        subjects = db.query(Sample.subject_id).filter_by(submission_id=submission_id).distinct().all()
        assert len(subjects) == 3
    finally:
        db.close()

# Check if diseases are invalid (according to OLS MONDO ontology), they are not saved in the database
def test_protect_invalid_disease(client):
    login_response = client.post(
        '/login',
        data={'username': 'testuser', 'pw': 'testpassword'},
        follow_redirects=False
    )
    assert login_response.status_code == 302
    base_path = Path(__file__).parent.parent
    electropherogram_path = base_path / 'client' / 'static' / 'tests' / 'electropherogram.csv'
    metadata_csv = b"""SAMPLE,Disease
                    Sample_1,invaliddisease
                    Sample_2,invaliddisease
                    Sample_3,invaliddisease
                    Sample_4,invaliddisease
                    Sample_5,invaliddisease
                    Sample_6,invaliddisease
                    """
    with electropherogram_path.open('rb') as f1:
        data = {
            'save_to_db': 'yes',
            'data_file': (BytesIO(f1.read()), 'electropherogram.csv'),
            'ladder_file': ['HSD5000'],
            'meta_file': (BytesIO(metadata_csv), 'metadata.csv')
        }
        response = client.post(
            '/protect',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )
    # check is the response the results page
    assert response.status_code == 200
    assert b"View your analysis interactively" in response.data
    html = response.data.decode('utf-8')
    match = re.search(r'/results/([0-9a-f-]{36})', html)
    submission_id = match.group(1)
    db = SessionLocal()
    # Check that the submission id exists in the database
    try:
        sub = db.query(Submission).filter_by(submission_id=submission_id).first()
        assert sub is not None
        assert sub.username == 'testuser'
        # check 6 new samples added with this submission id
        samples_count = db.query(Sample).filter_by(submission_id=submission_id).count()
        assert samples_count == 6
        # Check that the invalid diseases were not saved at all in the sample table (ALL NONE)
        diseases = db.query(Sample.disease_term_id).filter_by(submission_id=submission_id).distinct().all()
        disease_values = [d[0] for d in diseases]
        assert all(d is None for d in disease_values)
    finally:
        db.close()

def test_dashboard_displays_submissions_and_delete_status(client):
    sub_id_1 = str(uuid4())
    sub_id_2 = str(uuid4())
    login_response = client.post('/login', data={
        'username': 'testuser',
        'pw': 'testpassword'
    }, follow_redirects=True)
    assert login_response.status_code == 200
    db = SessionLocal()
    try:
        # Delete all existing submissions for testuser and add two new ones
        db.query(Submission).filter_by(username='testuser').delete()
        sub1 = Submission(
            submission_id=sub_id_1,
            username='testuser',
            created_at=datetime.now(),
            delete_status='NONE'
        )
        sub2 = Submission(
            submission_id=sub_id_2,
            username='testuser',
            created_at=datetime.now(),
            delete_status='NONE'
        )
        db.add_all([sub1, sub2])
        db.commit()
        db.refresh(sub1)
        db.refresh(sub2)
    finally:
        db.close()
    response = client.get('/submissions_dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    # Check that both submissions appear in the dashboard
    assert sub_id_1 in html
    assert sub_id_2 in html
    #num_submissions == 2
    assert '<span class="info-box-number">2</span>' in html
    # Simulate clicking the delete button by directly changing the status
    # Button click can only be tested from the vm since emails for delete 
    # are only sent from there (this test is for local testing only).
    try:
        sub = db.query(Submission).filter_by(submission_id=sub_id_1).first()
        sub.delete_status = 'PENDING'
        db.commit()
    finally:
        db.close()
    # Check does dashboard also have reflect this change
    response = client.get('/submissions_dashboard')
    html = response.data.decode('utf-8')
    assert sub_id_1 in html
    assert 'bi-hourglass-split' in html

# Remove submission from the database and check 
# is dashboard going to mistakingly show it because it 
# exists in the temporary file system folder
def test_dashboard_shows_only_db_submissions(client):
    sub_id_1 = str(uuid4())
    client.post('/login', data={
        'username': 'testuser',
        'pw': 'testpassword'
    }, follow_redirects=True)
    db = SessionLocal()
    # Add sub1
    try:
        # Delete all existing submissions for testuser and add new one
        db.query(Submission).filter_by(username='testuser').delete()
        sub1 = Submission(
            submission_id=sub_id_1,
            username='testuser',
            created_at=datetime.now(),
            delete_status='NONE'
        )
        db.add(sub1)
        db.commit()
        db.refresh(sub1)
    finally:
        db.close()
    response = client.get('/submissions_dashboard')
    assert response.status_code == 200
    html = response.data.decode('utf-8')
    # Check that the submissions appears in the dashboard
    assert sub_id_1 in html
    try:
        # Delete sub1
        db.query(Submission).filter_by(submission_id=sub_id_1).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()
    # Dashboard should no longer show sub1 (even if it is in the temporary file system)
    response = client.get('/submissions_dashboard')
    html = response.data.decode('utf-8')
    assert sub_id_1 not in html
