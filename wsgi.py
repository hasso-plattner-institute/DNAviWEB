"""
This file is the entry point to DNAvi app. This tells
Gunicorn server how to interact with the app.
"""
# Import is necessary for production to expose flask object so
# Gunicorn can run it. The exact instruction for Gunicorn
# in production environemnt are located in DNAvi.service
from client.app import app

# Ignored in production
# Only for testing
if __name__ == "__main__":
    # Connects to flask built in server on default port 5000: python wsgi.py
    app.run(host="0.0.0.0")
