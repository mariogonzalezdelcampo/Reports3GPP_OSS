"""
Summary writer for creating the Summary.md file.
"""
import os
from pathlib import Path
from typing import Union
import logging

logger = logging.getLogger(__name__)


def append_summary(meeting_dir: Path, related_wi: str, doc_name: str, spec: str) -> None:
    """
    Append an entry to the Summary.md file.
    
    Args:
        meeting_dir: The base directory for the meeting.
        related_wi: The Related WI value.
        doc_name: The name of the document.
        spec: The specification value.
    """
    summary_file = meeting_dir / "Summary.md"
    
    # Create the markdown entry
    entry = f"""- **Related WI**: {related_wi}
- **Document**: {doc_name}
- **Spec**: {spec}

"""
    
    try:
        # Append to the file
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write(entry)
        
        logger.info("Appended entry to %s", summary_file)
    except Exception as e:
        logger.error("Failed to append entry to %s: %s", summary_file, e)
        raise RuntimeError(f"Failed to write to summary file {summary_file}: {e}") from e