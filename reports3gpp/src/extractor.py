"""
Extractor utilities for handling ZIP files.
"""
import zipfile
import logging
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Raised when an extraction fails."""
    pass


def extract_zip(zip_path: Path, target_dir: Path) -> None:
    """
    Extract a ZIP file to a target directory.
    
    Args:
        zip_path: The path to the ZIP file.
        target_dir: The directory to extract the ZIP contents to.
        
    Raises:
        ExtractionError: If the extraction fails.
    """
    logger.info("Extracting %s to %s", zip_path, target_dir)
    
    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check if the ZIP is valid
            bad_file = zip_ref.testzip()
            if bad_file:
                raise ExtractionError(f"Bad file in ZIP archive: {bad_file}")
            
            # Extract all contents
            zip_ref.extractall(target_dir)
            
        logger.info("Successfully extracted %s to %s", zip_path, target_dir)
    except zipfile.BadZipFile as e:
        raise ExtractionError(f"Invalid ZIP file {zip_path}: {e}") from e
    except Exception as e:
        raise ExtractionError(f"Failed to extract {zip_path}: {e}") from e