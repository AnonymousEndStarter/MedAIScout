import os
import re
import settings
from typing import Any
from settings import logger


def check_pdf_path(index: str) -> bool:
    """
    Check if the device summary document is present

    Args:
        index (str): Submission Number of the Denice

    Returns:
        bool: True if the pdf is present, False otherwise
    """
    path = "{}{}.pdf".format(settings.PDF_DIR, index)
    logger.debug("Checking for PDF at {}".format(path))
    if not os.path.exists(path):
        logger.error("PDF not found")
        return False
    return True


def check_presence(element: Any, array: list[Any]) -> bool:
    """
    Check for presence of element in an 2D array

    Args:
        element (Any): Element to search for
        array (list[Any]): Array to search on

    Returns:
        bool: True if found else False
    """
    for i in array:
        if element in i:
            return True
    return False


def regex_search(text: str, pattern: list[re.Pattern]) -> bool:
    """
    Do a regex search for the text on the list of patterns

    Args:
        text (str): Text to sear
        pattern (list[re.Pattern]): List of regex patterns to search for

    Returns:
        bool: True if any of the patterns are found in the text, False otherwise
    """
    for p in pattern:
        matching = p.search(text)
        if matching:
            return True
    return False
