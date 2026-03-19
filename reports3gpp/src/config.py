"""
Configuration module for the 3GPP report generator.
"""
import os
from dataclasses import dataclass
from pathlib import Path
import tomllib
import logging

logger = logging.getLogger(__name__)


@dataclass
class AppConfig:
    meeting_number: int
    documents_dir: Path
    temp_dir: Path = Path(os.path.join(os.path.expanduser("~"), ".cache", "3gpp_reports"))
    # Processing mode: FULL runs the whole pipeline, BYPASS skips to LLM only.
    # Processing mode: FULL runs the whole pipeline, BYPASS skips to LLM only.
    processing_mode: str = "FULL"
    # Fixed prompt for LLM summarisation; can be overridden via config.toml
    fixed_prompt: str = ""

    @staticmethod
    def load() -> "AppConfig":
        """
        Load configuration from environment variables or config file.
        Priority: environment > config file > defaults
        """
        env_meeting = os.getenv("MEETING_NUMBER")
        env_docs = os.getenv("DOCS_DIR")
        env_mode = os.getenv("PROCESSING_MODE")
        # Determine configuration file location. By default we look for a file named
        # ``config.toml`` in the current working directory. The project stores the
        # file inside the ``reports3gpp`` package, so we fall back to that location
        # when the default is not present.
        cfg_path = Path(os.getenv("CONFIG_PATH", "config.toml"))
        if not cfg_path.is_file():
            # Try the package‑relative path as a fallback (one level up from src).
            fallback_path = Path(__file__).parent.parent / "config.toml"
            if fallback_path.is_file():
                cfg_path = fallback_path

        try:
            if cfg_path.is_file():
                with open(cfg_path, "rb") as f:
                    data = tomllib.load(f)
            else:
                data = {}
        except Exception as e:
            logger.warning("Failed to load config file %s: %s. Using defaults.", cfg_path, e)
            data = {}

        try:
            meeting = int(env_meeting or data.get("meeting_number", 165))
            if meeting <= 0:
                raise ValueError("Meeting number must be a positive integer")
            # Reasonable upper limit to prevent excessively large numbers
            if meeting > 1000:
                logger.warning("Meeting number %d seems unusually large", meeting)
        except (ValueError, TypeError) as e:
            logger.error("Invalid meeting number in configuration: %s", e)
            raise ValueError("Meeting number must be a positive integer") from e

        try:
            # Resolve the documents directory relative to the *package* root (the
            # ``reports3gpp`` directory). Using ``parents[1]`` moves one level up
            # from ``src`` to the package directory, avoiding duplication of the
            # ``reports3gpp`` segment when the script is run from inside the
            # ``reports3gpp`` package.
            project_root = Path(__file__).resolve().parents[1]
            raw_path = env_docs or data.get("documents_dir", "./documents")
            docs = (project_root / raw_path).expanduser().resolve()
            # Validate that the directory path is not a file
            if docs.exists() and not docs.is_dir():
                raise ValueError("Documents directory path points to a file, not a directory")
        except Exception as e:
            logger.error("Invalid documents directory in configuration: %s", e)
            raise ValueError("Invalid documents directory") from e

        try:
            # Resolve temp directory relative to the *package* root as well, for
            # consistency with ``documents_dir``.
            project_root = Path(__file__).resolve().parents[1]
            raw_temp = data.get("temp_dir", os.path.join(os.path.expanduser("~"), ".cache", "3gpp_reports"))
            temp = (project_root / raw_temp).resolve()
            # Validate that the temp directory path is not a file
            if temp.exists() and not temp.is_dir():
                raise ValueError("Temp directory path points to a file, not a directory")
        except Exception as e:
            logger.error("Invalid temp directory in configuration: %s", e)
            raise ValueError("Invalid temp directory") from e

        # Determine processing mode (default BYPASS)
        mode = env_mode or data.get("processing_mode", "BYPASS")
        # Load optional fixed_prompt from config file (may be empty string)
        fixed_prompt = data.get("fixed_prompt", "")
        return AppConfig(
            meeting_number=meeting,
            documents_dir=docs,
            temp_dir=temp,
            processing_mode=mode,
            fixed_prompt=fixed_prompt,
        )