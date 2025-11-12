"""
Accessing DNAviWEB Programmatically:
This module shows how to programmatically submit example data to the /protect
DNAvi endpoint and get analysis results in raw HTML (no styling). 
"""

import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://dnavi.sc.hpi.de"
PROTECT_URL = f"{BASE_URL}/protect" 

# -----------------------------
# RUN ANALYSIS
# -----------------------------
def run_protect():
    """
    Run analysis on example files via /protect
    """
    form_data = {
        "Example": "on",
        "save_to_db": "no",
        "agree_terms": "on"
    }
    session = requests.Session()
    response = session.post(PROTECT_URL, data=form_data)
    if response.status_code == 200:
        print("/protect submission successful")
        return response.text
    else:
        print(f"ERROR /protect submission failed ({response.status_code})")
        return None

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    result_html = run_protect()
    if result_html:
        # Save result page locally in raw html format
        with open("results.html", "w", encoding="utf-8") as f:
            f.write(result_html)
        print("Results saved to results.html")