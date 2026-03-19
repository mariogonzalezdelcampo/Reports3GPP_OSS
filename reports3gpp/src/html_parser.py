"""
HTML parser for finding ZIP files on the 3GPP website.
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional
import logging
import urllib.parse

logger = logging.getLogger(__name__)


def find_zip_file_in_html(url: str, meeting_number: int) -> Optional[str]:
    """
    Find the ZIP file name from the HTML content of a 3GPP page.
    
    This function parses the HTML content from the 3GPP website to locate
    the ZIP file containing meeting documentation. It searches for files
    matching the pattern TDoc_List_Meeting* and returns the first match.
    
    Args:
        url: The URL to fetch and parse (e.g., https://www.3gpp.org/ftp/tsg_sa/WG5_TM/TSGS5_165/Tdoclist)
        meeting_number: The meeting number to search for in the ZIP file name.
        
    Returns:
        The name of the ZIP file, or None if not found.
        
    Example:
        >>> find_zip_file_in_html("https://www.3gpp.org/ftp/tsg_sa/WG5_TM/TSGS5_165/Tdoclist", 165)
        "TDoc_List_Meeting165.zip"
    """
    logger.info("Fetching HTML content from %s", url)
    
    try:
        # For FTP URLs, we need to handle them differently
        if url.startswith("ftp://"):
            # For FTP, we'll return None to indicate we should use directory listing approach
            # The actual file name will be determined by directory listing
            return None
        else:
            # Handle HTTP URLs normally
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            html_content = response.text
    except requests.RequestException as e:
        logger.error("Failed to fetch HTML content from %s: %s", url, e)
        return None

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'lxml')
    
    # Method 1: Look for anchor tags with href containing TDoc_List_Meeting and ending with .zip
    zip_files = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'TDoc_List_Meeting' in href and href.endswith('.zip'):
            zip_files.append(href)
    
    # If we found ZIP files, return the first one that matches the meeting number pattern
    if zip_files:
        # Filter by meeting number and return the first match
        for zip_file in zip_files:
            if f'TDoc_List_Meeting{meeting_number}' in zip_file:
                logger.info("Found ZIP file: %s", zip_file)
                # Extract just the filename from the href
                return zip_file.split('/')[-1]

    # Method 2: Look for input elements with downloadInput class and value attribute
    for input_elem in soup.find_all('input', {'class': 'downloadInput'}, value=True):
        value = input_elem['value']
        if 'TDoc_List_Meeting' in value and value.endswith('.zip'):
            logger.info("Found ZIP file from input element: %s", value)
            return value.split('/')[-1]

    # Method 3: Look for any ZIP file that contains the meeting number in its name (fallback)
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.zip') and str(meeting_number) in href:
            logger.info("Found ZIP file containing meeting number: %s", href)
            return href.split('/')[-1]

    # Method 4: Look for any ZIP file in the page (last resort)
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('.zip'):
            logger.info("Found ZIP file (fallback): %s", href)
            return href.split('/')[-1]

    logger.warning("No ZIP file found in HTML content from %s", url)
    return None