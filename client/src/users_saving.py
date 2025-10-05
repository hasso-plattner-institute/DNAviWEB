import json
import os
from flask_login import current_user
from flask import g
from uuid import uuid4
from .client_constants import USERS_FILE

USERS = {}

def get_email():
    """
    Returns the current user's email if logged in,
    otherwise generates a temporary guest ID for this flask request.
    """
    if current_user.is_authenticated:
        return current_user.id
    else:
        # Only generate a guest ID once per request
        if not hasattr(g, 'email'):
            g.email = f"guest_{uuid4().hex[:8]}"
        return g.email

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
