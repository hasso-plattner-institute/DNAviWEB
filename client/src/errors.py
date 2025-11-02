"""

File with error functions for the flask app / client interaction \n

Author: Anja Hess \n
Date: 2025-SEP-07 \n


"""
import re

def replaceTextBetween(originalText, delimeterA, delimterB, replacementText):
    leadingText = originalText.split(delimeterA)[0]
    trailingText = originalText.split(delimterB)[1]

    return leadingText + delimeterA + replacementText + delimterB + trailingText

def secure_error(error):
    """
    Remove sensitive information from the error message
    :return: str
    """

    error = error.split(" ")
    list = []
    for e in error:
        if "/" in e or "|" in e or "\\" in e or "also" in e or "see" in e or "_" in e or "Welcome" in e or "to" in e:
            e = ""
        list.append(e)
    out = " ".join(list)
    return out