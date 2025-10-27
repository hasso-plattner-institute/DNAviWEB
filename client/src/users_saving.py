from uuid import uuid4

from flask import session
from flask_login import current_user
from werkzeug.security import generate_password_hash

from database.config import SessionLocal
from database.schema.user_details import UserDetails

def get_username():
    """
    Returns the current user's username if logged in,
    if the user is not logged in, generates a unique guest ID the first time 
    and stores it in the session, so subsequent requests from same session use the same guest ID
    
    """
    if current_user.is_authenticated:
        return current_user.id
    if 'guest_id' not in session:
        session['guest_id'] = f"guest_{uuid4().hex[:8]}"
    return session['guest_id']


def save_user(username: str, password: str):
    """
    Save a new user to the database.
    Password is hashed before saving.
    """
    db = SessionLocal()
    try:
        user = UserDetails(username=username, password_hash=generate_password_hash(password))
        db.add(user)
        db.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        db.close()
