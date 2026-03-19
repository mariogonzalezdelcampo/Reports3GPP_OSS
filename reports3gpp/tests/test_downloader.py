"""
Unit tests for the downloader module.
"""
import os
import tempfile
from pathlib import Path
import pytest
import requests
from unittest.mock import patch, mock_open

from src.downloader import download_file, download_zip, DownloadError


def test_download_file_success():
    """Test successful file download."""
    with patch("requests.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.raise_for_status.return_value = None
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / "test_file.txt"
            
            result = download_file("http://example.com/file.txt", dest)
            
            assert result == dest
            assert dest.exists()
            assert dest.read_text() == "test data"


def test_download_file_failure():
    """Test failed file download."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Network error")
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest = Path(tmp_dir) / "test_file.txt"
            
            with pytest.raises(DownloadError):
                download_file("http://example.com/file.txt", dest)


def test_download_zip():
    """Test downloading a ZIP file."""
    with patch("requests.get") as mock_get:
        mock_response = mock_get.return_value
        mock_response.iter_content.return_value = [b"zip data"]
        mock_response.raise_for_status.return_value = None
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_dir = Path(tmp_dir)
            
            result = download_zip("http://example.com/file.zip", dest_dir)
            
            assert result.name == "file.zip"
            assert result.parent == dest_dir
            assert result.exists()