"""
TDoc handler for processing individual TDoc entries.
"""
import os
from pathlib import Path
from typing import Dict
import logging
import sys

# Ensure the src directory is on the import path for relative imports.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from downloader import download_zip_ftp, download_zip
from extractor import extract_zip

logger = logging.getLogger(__name__)


def process_tdoc(item: Dict, base_meeting_dir: Path, temp_dir: Path) -> str:
    """Process a single TDoc entry and return the extracted document name.

    The function downloads the ZIP referenced in the ``TDoc`` column, extracts
    it into the folder for the corresponding ``Related WIs`` and returns the
    name of the extracted ``.docx`` file (or the ZIP name if no docx is found).
    """
    logger.info("Processing TDoc: %s", item.get("TDoc", "Unknown"))

    related_wi = item.get("Related WIs", "")
    if not related_wi:
        logger.warning("Skipping TDoc with empty Related WIs: %s", item)
        return ""

    target_dir = base_meeting_dir / related_wi
    target_dir.mkdir(parents=True, exist_ok=True)

    tdoc_url = item.get("TDoc", "")
    if not tdoc_url:
        logger.warning("Skipping TDoc with empty TDoc URL: %s", item)
        return ""

    try:
        # Determine download method based on URL scheme
        if tdoc_url.startswith("ftp://"):
            from urllib.parse import urlparse
            parsed = urlparse(tdoc_url)
            host = parsed.hostname
            path = parsed.path
            temp_zip = temp_dir / f"temp_{os.path.basename(path)}"
            download_zip_ftp(host, path, temp_zip)
            extract_zip(temp_zip, target_dir)
            temp_zip.unlink()
        else:
            # HTTP/HTTPS download
            zip_path = download_zip(tdoc_url, temp_dir)
            extract_zip(zip_path, target_dir)
            zip_path.unlink()

        logger.info("Successfully processed TDoc for %s", related_wi)

        # Find a document file inside the extracted directory. Prefer .docx, then .doc.
        doc_files = list(target_dir.rglob("*.docx"))
        if not doc_files:
            doc_files = list(target_dir.rglob("*.doc"))
        if doc_files:
            return doc_files[0].name
        # Fallback to the original ZIP name if no document found
        return Path(tdoc_url).stem + ".zip"
    except Exception as e:
        logger.error("Failed to process TDoc for %s: %s", related_wi, e)
        raise