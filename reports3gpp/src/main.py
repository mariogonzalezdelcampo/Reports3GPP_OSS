"""
Main entry point for the 3GPP report generator.
"""
import os
import sys
import logging
import re
from pathlib import Path
from typing import Optional

# Ensure the src directory is on the import path
sys.path.insert(0, str(Path(__file__).parent))

from config import AppConfig
from downloader import download_file, download_zip_ftp
from extractor import extract_zip
from excel_processor import excel_to_csv, filter_items
from tdoc_handler import process_tdoc
from summary import append_summary
from html_parser import find_zip_file_in_html
from ollama_client import query_ollama
from docx import Document

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper to persist LLM interactions
# ---------------------------------------------------------------------------
def _log_interaction(prompt: str, response: str, *, mode: str = "w") -> None:
    """Write the *prompt* and *response* to ``REQUEST.md`` and ``RESPONSE.md``.

    A separator line (``---``) is added after each entry so that multiple
    interactions are clearly delimited in both files. The ``mode`` argument
    determines whether the files are overwritten (``"w"``) or appended to
    (``"a"``).
    """
    request_path = Path("REQUEST.md")
    response_path = Path("RESPONSE.md")
    # Write the prompt and a separator
    with open(request_path, mode, encoding="utf-8") as f_req:
        f_req.write(prompt + "\n")
        f_req.write("---\n")
    # Write the response and a separator
    with open(response_path, mode, encoding="utf-8") as f_res:
        f_res.write(response + "\n")
        f_res.write("---\n")

# ---------------------------------------------------------------------------
# Text extraction / cleaning utilities for DOCX files
# ---------------------------------------------------------------------------
_IGNORE_HEADINGS = {
    "foreword",
    "scope",
    "references",
    "definition of terms",
    "change history",
    "versioning",
    "modal-verb conventions",
    "definitions",
    "symbols",
    "abbreviations",
}

def _clean_text(text: str) -> str:
    """Normalise whitespace and remove non‑printable characters."""
    text = re.sub(r"[\x00-\x1F\x7F]", " ", text)
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def _extract_docx_text(docx_path: Path) -> str:
    """Extract text from *docx_path* while skipping irrelevant headings."""
    doc = Document(str(docx_path))
    lines = []
    for para in doc.paragraphs:
        txt = para.text.strip()
        if not txt:
            continue
        if txt.lower() in _IGNORE_HEADINGS:
            continue
        lines.append(txt)
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------
def main(meeting_number: Optional[int] = None) -> None:
    cfg = AppConfig.load()
    if meeting_number is not None:
        if meeting_number <= 0:
            raise ValueError("Meeting number must be a positive integer")
        cfg.meeting_number = meeting_number

    mode = cfg.processing_mode.upper() if hasattr(cfg, "processing_mode") else "FULL"

    # -----------------------------------------------------------------------
    # BYPASS mode – only LLM calls, no FTP / Excel processing
    # -----------------------------------------------------------------------
    if mode == "BYPASS":
        logger.info("Processing mode BYPASS – skipping pipeline, invoking LLM only")
        # Simple test prompt
        prompt = "Hola, que tal estas?"
        logger.info(f"Prompt: {prompt}")
        response = query_ollama("http://10.95.118.26:11434", "gpt-oss:120b", prompt)
        logger.info(f"Response: {response}")

        # ---------------------------------------------------------------
        # Summarise the first DOCX in the FS_6G_CH folder (if it exists)
        # ---------------------------------------------------------------
        meeting_dir = cfg.documents_dir / f"3GPP_meeting_docs_{cfg.meeting_number}"
        fs_folder = meeting_dir / "FS_6G_CH"
        if fs_folder.is_dir():
            docx_files = sorted(fs_folder.glob("*.docx"))
            if docx_files:
                first_docx = docx_files[0]
                logger.info(f"Processing DOCX file: {first_docx.name}")
                raw_text = _extract_docx_text(first_docx)
                cleaned = _clean_text(raw_text)
                # Split into manageable chunks (≈200000 characters, ~50000 tokens)
                max_chunk = 200000

                chunks = [cleaned[i : i + max_chunk] for i in range(0, len(cleaned), max_chunk)]
                # Use the configurable fixed prompt from the configuration file.
                fixed_prompt = cfg.fixed_prompt or ""
                summary_parts = []
                for chunk in chunks:
                    prompt_chunk = fixed_prompt + chunk + "\n=== FIN DOCUMENTO ==="
                    chunk_resp = query_ollama("http://10.95.118.26:11434", "gpt-oss:120b", prompt_chunk, temperature=0.1)
                    summary_parts.append(chunk_resp.strip())
                    # Log each chunk interaction (append mode)
                    # Interaction logging removed as per user request
                # Include the DOCX filename at the top of the summary file
                final_summary = f"{first_docx.name}\n\n" + "\n\n".join(summary_parts)
                summary_path = fs_folder / "FS_6G_CH_summary.md"
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(final_summary)
                logger.info(f"Summary written to {summary_path}")
            else:
                logger.info("No DOCX files found in %s", fs_folder)
        else:
            logger.info("FS_6G_CH folder not present: %s", fs_folder)
        return

    # -----------------------------------------------------------------------
    # FULL processing – download ZIP, extract Excel, filter items, etc.
    # -----------------------------------------------------------------------
    logger.info("Starting report generation for meeting %s", cfg.meeting_number)

    # Build remote FTP path
    host = "ftp.3gpp.org"
    base_path = "/tsg_sa/WG5_TM/TSGS5_"
    remote_path = f"{base_path}{cfg.meeting_number}/Tdoclist/"

    # Locate the ZIP file on the FTP server
    try:
        from downloader import list_ftp_directory
        files = list_ftp_directory(host, remote_path)
        zip_files = [f for f in files if f.endswith('.zip') and 'TDoc_List_Meeting' in f]
        if zip_files:
            zip_name = zip_files[0]
        else:
            zip_files = [f for f in files if f.endswith('.zip')]
            if zip_files:
                zip_name = zip_files[0]
            else:
                raise RuntimeError(f"No ZIP files found in FTP directory {remote_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to find ZIP file in FTP directory {remote_path}: {e}")

    logger.info("Found ZIP file: %s", zip_name)

    # Download and extract the ZIP
    zip_url = f"{base_path}{cfg.meeting_number}/Tdoclist/{zip_name}"
    zip_path = cfg.documents_dir / zip_name
    download_zip_ftp(host, zip_url, zip_path)
    meeting_dir = cfg.documents_dir / f"3GPP_meeting_docs_{cfg.meeting_number}"
    extract_zip(zip_path, meeting_dir)

    # Locate the Excel file and convert it to CSV
    excel_file = next(meeting_dir.rglob("*.xls*"), None)
    if not excel_file:
        raise FileNotFoundError("No Excel file found in the extracted directory")
    csv_file = excel_file.with_suffix('.csv')
    excel_to_csv(excel_file, csv_file)

    # Filter the CSV rows according to the original business rules
    items = filter_items(csv_file)

    # Process each TDoc item
    for i, item in enumerate(items):
        try:
            doc_name = process_tdoc(item, meeting_dir, cfg.temp_dir)
            append_summary(
                meeting_dir / item["Related WIs"],
                item["Related WIs"],
                doc_name,
                item["Spec"],
            )
        except Exception as e:
            logger.error("Failed to process item %d: %s", i, e)
            continue

    logger.info("Report generation completed successfully")

    # -----------------------------------------------------------------------
    # OPTIONAL: final LLM call after the full pipeline (mirrors BYPASS behaviour)
    # -----------------------------------------------------------------------
    # Final LLM call after full processing removed per user request (no REQUEST/RESPONSE files needed)

if __name__ == "__main__":
    meeting_number = None
    if len(sys.argv) > 1:
        try:
            meeting_number = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid meeting number provided")
            sys.exit(1)
    main(meeting_number)