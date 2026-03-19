"""
Downloader utilities for fetching files from the web.
"""
import requests
from pathlib import Path
from typing import Union
import logging
import ftplib
import os

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    """Raised when a download fails."""
    pass


def download_file(url: str, dest: Path) -> Path:
    """
    Download a file from a URL to a local destination.
    
    Args:
        url: The URL to download from.
        dest: The local path to save the file to.
        
    Returns:
        The path to the downloaded file.
        
    Raises:
        DownloadError: If the download fails.
    """
    logger.info("Downloading %s to %s", url, dest)
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Ensure the directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        logger.info("Downloaded %s to %s", url, dest)
        return dest
    except requests.RequestException as e:
        raise DownloadError(f"Failed to download {url}: {e}") from e
    except Exception as e:
        raise DownloadError(f"Unexpected error while downloading {url}: {e}") from e


def list_ftp_directory(host: str, remote_path: str) -> list:
    """
    List files in an FTP directory.
    
    Args:
        host: The FTP server hostname.
        remote_path: The remote directory path.
        
    Returns:
        List of filenames in the directory.
        
    Raises:
        DownloadError: If the listing fails.
    """
    logger.info("Listing FTP directory %s:%s", host, remote_path)
    try:
        files = []
        with ftplib.FTP(host) as ftp:
            ftp.login()
            if remote_path != '/':
                ftp.cwd(remote_path)
            files = ftp.nlst()
        logger.info("Found %d files in FTP directory %s:%s", len(files), host, remote_path)
        return files
    except Exception as e:
        raise DownloadError(f"Failed to list FTP directory {host}:{remote_path}: {e}") from e


def download_zip_ftp(host: str, remote_path: str, local_path: Path) -> None:
    """
    Download a ZIP file from an FTP server.
    
    Args:
        host: The FTP server hostname.
        remote_path: The remote path to the ZIP file (e.g., /tsg_sa/WG5_TM/TSGS5_165/Tdoclist/TDoc_List_Meeting165.zip).
        local_path: The local path to save the file to.
        
    Raises:
        DownloadError: If the download fails.
    """
    logger.info("Downloading ZIP from FTP %s:%s to %s", host, remote_path, local_path)
    try:
        # Ensure the directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to FTP server
        with ftplib.FTP(host) as ftp:
            # Login (anonymous login)
            ftp.login()
            
            # If the remote_path is a directory, list files and find the ZIP file
            if remote_path.endswith('/'):
                # List directory contents to find ZIP file
                files = list_ftp_directory(host, remote_path)
                zip_files = [f for f in files if f.endswith('.zip') and 'TDoc_List_Meeting' in f]
                
                if not zip_files:
                    raise DownloadError(f"No TDoc_List_Meeting*.zip files found in FTP directory {remote_path}")
                
                # Use the first matching ZIP file
                zip_filename = zip_files[0]
                full_remote_path = f"{remote_path}{zip_filename}"
                
                logger.info("Found ZIP file %s in directory %s", zip_filename, remote_path)
                
                # Download the file
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {zip_filename}', f.write)
            else:
                # Direct file download
                # Extract directory and filename
                dir_path = os.path.dirname(remote_path)
                filename = os.path.basename(remote_path)
                
                if dir_path and dir_path != '/':
                    ftp.cwd(dir_path)
                
                # Download the file
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                
        logger.info("Downloaded ZIP from FTP %s:%s to %s", host, remote_path, local_path)
    except Exception as e:
        raise DownloadError(f"Failed to download ZIP from FTP {host}:{remote_path}: {e}") from e


def download_zip(url: str, dest_dir: Path) -> Path:
    """
    Download a ZIP file from a URL to a local directory.
    
    Args:
        url: The URL to download from.
        dest_dir: The local directory to save the ZIP file to.
        
    Returns:
        The path to the downloaded ZIP file.
        
    Raises:
        DownloadError: If the download fails.
    """
    # Extract filename from URL
    filename = url.split("/")[-1]
    dest = dest_dir / filename
    
    return download_file(url, dest)