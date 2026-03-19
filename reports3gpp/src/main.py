"""
Main entry point for the 3GPP report generator.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import AppConfig
from downloader import download_file, download_zip_ftp
from extractor import extract_zip
from excel_processor import excel_to_csv, filter_items
from tdoc_handler import process_tdoc
from summary import append_summary
from html_parser import find_zip_file_in_html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main(meeting_number: Optional[int] = None) -> None:
    """
    Main function to orchestrate the report generation.
    
    Args:
        meeting_number: The meeting number to process. If None, uses the config.
    """
    # Load configuration
    cfg = AppConfig.load()
    if meeting_number is not None:
        # Validate the provided meeting number
        if meeting_number <= 0:
            raise ValueError("Meeting number must be a positive integer")
        if meeting_number > 1000:
            logger.warning("Meeting number %d seems unusually large", meeting_number)
        cfg.meeting_number = meeting_number

    # ---------------------------------------------------------------------
    # Processing mode handling: BYPASS skips the whole pipeline and goes
    # directly to the LLM invocation. FULL runs the complete workflow.
    # ---------------------------------------------------------------------
    mode = cfg.processing_mode.upper() if hasattr(cfg, "processing_mode") else "FULL"
    if mode == "BYPASS":
        logger.info("Processing mode BYPASS – skipping pipeline, invoking LLM only")
        # Direct LLM call (same as at the end of the function)
        try:
            from ollama_client import query_ollama
            ollama_host = "http://10.95.118.26:11434"
            ollama_model = "gpt-oss:120b"
            prompt = "Hola, que tal estas?"
            print(f"Prompt: {prompt}")
            response = query_ollama(ollama_host, ollama_model, prompt)
            print(f"Response: {response}")
        except Exception as e:
            logger.error("Failed to query Ollama: %s", e)
        return
    
    logger.info("Starting report generation for meeting %s", cfg.meeting_number)
    
    # Validate meeting number
    if cfg.meeting_number <= 0:
        raise ValueError("Meeting number must be a positive integer")
    
    # Build the remote FTP path
    host = "ftp.3gpp.org"
    base_path = "/tsg_sa/WG5_TM/TSGS5_"
    remote_path = f"{base_path}{cfg.meeting_number}/Tdoclist/"
    
    # Get the ZIP file name by listing the FTP directory
    try:
        from downloader import list_ftp_directory
        files = list_ftp_directory(host, remote_path)
        zip_files = [f for f in files if f.endswith('.zip') and 'TDoc_List_Meeting' in f]
        if zip_files:
            zip_name = zip_files[0]
        else:
            # If no matching files found, try a more general approach
            zip_files = [f for f in files if f.endswith('.zip')]
            if zip_files:
                zip_name = zip_files[0]
            else:
                raise RuntimeError(f"No ZIP files found in FTP directory {remote_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to find ZIP file in FTP directory {remote_path}: {e}")
    
    logger.info("Found ZIP file: %s", zip_name)
    
    # Download the zip file using FTP
    try:
        zip_url = f"{base_path}{cfg.meeting_number}/Tdoclist/{zip_name}"
        zip_path = cfg.documents_dir / zip_name
        download_zip_ftp(host, zip_url, zip_path)
    except Exception as e:
        raise RuntimeError(f"Failed to download ZIP file {zip_name} via FTP: {e}")
    
    # Extract the zip file
    meeting_dir = cfg.documents_dir / f"3GPP_meeting_docs_{cfg.meeting_number}"
    try:
        extract_zip(zip_path, meeting_dir)
    except Exception as e:
        raise RuntimeError(f"Failed to extract ZIP file {zip_name}: {e}")
    
    # Verify extraction
    if not meeting_dir.is_dir():
        raise RuntimeError("Extraction failed – meeting folder missing")
    
    # Find the Excel file
    try:
        excel_file = next(meeting_dir.rglob("*.xls*"), None)
        if not excel_file:
            raise FileNotFoundError("No Excel file found in the extracted directory")
        # Validate that the Excel file exists and is readable
        if not excel_file.exists():
            raise FileNotFoundError(f"Excel file does not exist: {excel_file}")
        if not os.access(excel_file, os.R_OK):
            raise PermissionError(f"Insufficient permissions to read Excel file: {excel_file}")
    except Exception as e:
        raise RuntimeError(f"Error finding Excel file in extracted directory: {e}")
    
    # Convert Excel to CSV
    try:
        csv_file = excel_file.with_suffix(".csv")
        excel_to_csv(excel_file, csv_file)
    except Exception as e:
        raise RuntimeError(f"Failed to convert Excel to CSV: {e}")
    
    # Filter items
    try:
        items = filter_items(csv_file)
    except Exception as e:
        raise RuntimeError(f"Failed to filter items from CSV: {e}")

    # Process each item
    for i, item in enumerate(items):
        try:
            # Process the TDoc and obtain the actual extracted document name
            doc_name = process_tdoc(item, meeting_dir, cfg.temp_dir)
            append_summary(
                meeting_dir / item["Related WIs"],
                item["Related WIs"],
                doc_name,
                item["Spec"]
            )
        except Exception as e:
            logger.error("Failed to process item %d: %s", i, e)
            # Continue processing other items instead of stopping completely
            continue
    
    logger.info("Report generation completed successfully")

    # ------------------------------------------------------------
    # OPTIONAL: Query remote Ollama LLM after all processing is done.
    # ------------------------------------------------------------
    try:
        from ollama_client import query_ollama

        # Ollama server runs on the default port 11434
        ollama_host = "http://10.95.118.26:11434"
        ollama_model = "gpt-oss:120b"
        prompt = "Hola, que tal estas?"
        # Print prompt and response to console as requested.
        print(f"Prompt: {prompt}")
        response = query_ollama(ollama_host, ollama_model, prompt)
        print(f"Response: {response}")
    except Exception as e:
        # No error handling required per current spec; just log if something
        # unexpected happens so the user can see it.
        logger.error("Failed to query Ollama: %s", e)


if __name__ == "__main__":
    # Allow command-line override of meeting number
    meeting_number = None
    if len(sys.argv) > 1:
        try:
            meeting_number = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid meeting number provided")
            sys.exit(1)
    
    main(meeting_number)