import json
import os
from flask_login import current_user
from flask import g, session
from uuid import uuid4
from .client_constants import USERS_FILE

USERS = {}

def get_email():
    """
    Returns the current user's email if logged in,
    if the user is not logged in, generates a unique guest ID the first time 
    and stores it in the session, so subsequent requests from same session use the same guest ID.
    """
    if current_user.is_authenticated:
        return current_user.id
    else:
        if 'guest_id' not in session:
            session['guest_id'] = f"guest_{uuid4().hex[:8]}"
        return session['guest_id']

def load_users():
    """
    Load all emails and password from the users.json file when starting the flask app.
    """
    global USERS
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            USERS = json.load(f)
    else:
        USERS = {"tester@tester.com": {"pw": "gellyfish"}}
        
def save_users():
    """
    Save all emails and password from the users.json file when starting the flask app.
    """
    global USERS
    with open(USERS_FILE, 'w') as f:
        json.dump(USERS, f, indent=4)
    os.chmod(USERS_FILE, 0o770)
