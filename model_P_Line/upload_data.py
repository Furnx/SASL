"""
Google Drive Upload Module for SASL Sign Language Project

This module handles uploading processed MediaPipe sign language data to Google Drive.
It provides automated upload, verification, and cleanup functionality with robust
error handling including retry logic and progress tracking.

Key Features:
    - OAuth2 authentication with Google Drive
    - Automatic folder structure creation per contributor
    - Progress tracking for large uploads
    - Retry logic with exponential backoff for network failures
    - Upload verification via file size comparison
    - Automatic cleanup of temporary zip files
    - Comprehensive logging

Usage:
    Run directly to upload MP_Data for the active week:
    $ python upload_data.py
    
    Or import and use individual functions:
    >>> from upload_data import get_drive_service, upload_zip_folder
    >>> service = get_drive_service()
    >>> file_id = upload_zip_folder(service, 'data.zip', 'parent_id')

Requirements:
    - Google Cloud credentials file (client_secret_*.json)
    - Active Google Drive API access
    - Proper configuration in config.py

Author: WeThinkCode_ SASL Project
"""
import os
import shutil
import zipfile
import logging
import time
from functools import wraps
from typing import Optional, Callable, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from googleapiclient.errors import HttpError
import json
from google.oauth2.credentials import Credentials
from config import ACTIVE_WEEK, GOOGLE_CREDENTIALS_FILE, PROJECT_ROOT_ID, GOOGLE_DRIVE_SCOPES
import io

# ----------------------------------------------------------------
# LOGGING CONFIGURATION
# ----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('upload_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------
SCOPES = GOOGLE_DRIVE_SCOPES

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RETRY_BACKOFF = 2  # exponential backoff multiplier


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY, backoff: float = RETRY_BACKOFF) -> Callable:
    '''
    Decorator to retry a function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_on_failure(max_retries=3, delay=2, backoff=2)
        def upload_file(...):
            ...
    '''
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
                except Exception as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            return None
        return wrapper
    return decorator


def get_drive_service():
        '''
        Handles authentication and returns a Google Drive service object.
        
        Checks for existing credentials in 'token.json', and if not found or invalid,
        initiates the OAuth2 flow to obtain new credentials.
        
        Returns:
            service: Authorized Google Drive service object
            
        Raises:
            FileNotFoundError: If credentials file is not found
            
        Example:
            service = get_drive_service()
            files = service.files().list().execute()
        '''
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        if os.path.exists('token.json'):
            # with open('token.json', 'rb') as token:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            # PUT CREDENTIALS FILE OR CLIENT SECRET PATH HERE
            # Make sure to download from Google Cloud Console
            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"{GOOGLE_CREDENTIALS_FILE} not found. Please download it from Google Cloud Console "
                    "and place it in the project root directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        # Build the Drive service
        service = build('drive', 'v3', credentials=creds)
        return service


def validate_folder_structure(service, folder_id: str) -> bool:
    '''
    Validates that a folder exists in Google Drive.
    
    Args:
        service: Google Drive service object
        folder_id: ID of the folder to validate
        
    Returns:
        True if folder exists and is valid, False otherwise
        
    Example:
        if validate_folder_structure(service, 'folder_id_123'):
            print("Folder is valid")
    '''
    try:
        folder = service.files().get(fileId=folder_id, fields='id, name, mimeType').execute()
        if folder.get('mimeType') == 'application/vnd.google-apps.folder':
            logger.info(f"Validated folder: {folder.get('name')} (ID: {folder_id})")
            return True
        else:
            logger.error(f"ID {folder_id} exists but is not a folder")
            return False
    except HttpError as e:
        logger.error(f"Folder validation failed for ID {folder_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during folder validation: {e}")
        return False


def create_or_get_contributor_folder(service, parent_folder_id: str, contributor_email: str) -> str:
    '''
    Creates a folder for a contributor if it doesn't exist, or returns the ID of the existing folder.
    
    Args:
        service: Google Drive service object
        parent_folder_id: ID of the parent folder (where contributor folders are stored)
        contributor_email: Email of the contributor (used as folder name)
        
    Returns:
        ID of the contributor's folder
        
    Example:
        folder_id = create_or_get_contributor_folder(service, 'parent_id', 'user@email.com')
    '''
    contributor_email = contributor_email.split('_')[0]
    query = (
        f'mimeType="application/vnd.google-apps.folder" '
        f'and "{parent_folder_id}" in parents '
        f'and name="{contributor_email}"'
    )
  
    # Execute the query to find existing contributor folder
    results = service.files().list(
        q=query, 
        spaces='drive', 
        fields='files(id)'
    ).execute()
    
    folders = results.get('files', [])

    # If folder doesn't exist, create it
    if not folders:
        folder_metadata = {
            'name': contributor_email,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = service.files().create(
            body=folder_metadata, 
            fields='id'
        ).execute()
        return folder['id']
    else:
        return folders[0]['id']


@retry_on_failure(max_retries=3, delay=2, backoff=2)
def upload_zip_folder(service, folder_path: str, parent_folder_id: str) -> Optional[str]:
    '''
    Uploads a zipped folder to Google Drive under the specified parent folder.
    Shows progress during upload. Automatically retries on network failures.
    
    Args:
        service: Google Drive service object
        folder_path: Path to the zipped folder to upload
        parent_folder_id: ID of the parent folder in Google Drive
        
    Returns:
        File ID of the uploaded file on Google Drive, or None if upload failed
        
    Example:
        file_id = upload_zip_folder(service, 'data.zip', 'parent_folder_id')
        if file_id:
            print(f"Uploaded successfully: {file_id}")
    '''
    # Prepare file metadata and media upload
    file_metadata = {
        'name': os.path.basename(folder_path),
        'parents': [parent_folder_id]
    }
    # Create MediaFileUpload object for the zipped folder
    media = MediaFileUpload(folder_path, mimetype='application/zip', 
                            resumable=True)
    try: 
        # Upload the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id')
        
        # Show progress
        response = None
        while response is None:
            status, response = file.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                logger.info(f"Upload progress: {progress}%")
        
        logger.info(f'Uploaded {folder_path} to Google Drive.')
        logger.info('Check if folder uploaded successfully!')
        return response['id']
    except HttpError as e:
        logger.error(f'Upload failed. Please upload manually: {e}')
        return None
    except Exception as e:
        logger.error(f'Unexpected error during upload: {e}')
        return None

def verify_upload(service, file_id: str, local_file_path: str) -> bool:
    '''
    Verifies that the uploaded file exists and has the correct size.
    
    Args:
        service: Google Drive service object
        file_id: ID of the uploaded file
        local_file_path: Path to the local file for size comparison
        
    Returns:
        True if verification successful, False otherwise
        
    Example:
        if verify_upload(service, 'file_id_123', 'local.zip'):
            print("Upload verified successfully")
    '''
    try:
        # Get file info from Drive
        file_info = service.files().get(fileId=file_id, fields='name, size, mimeType').execute()
        remote_size = int(file_info.get('size', 0))
        local_size = os.path.getsize(local_file_path)
        
        logger.info(f"Verifying upload: {file_info.get('name')}")
        logger.info(f"Local size: {local_size} bytes")
        logger.info(f"Remote size: {remote_size} bytes")
        
        if remote_size == local_size:
            logger.info("✓ File size verification passed!")
            return True
        else:
            logger.error(f"✗ Size mismatch! Local: {local_size}, Remote: {remote_size}")
            return False
    except HttpError as e:
        logger.error(f"Verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def zip_mp_data(source_dir: str, output_file: str, folder_name: Optional[str] = None) -> str:
    '''
    Zips the contents of the source directory into a zip file.
    
    Args:
        source_dir: Directory containing files to zip
        output_file: Path to the output zip file
        folder_name: Optional folder name to use as root in the zip (e.g., user email)
                     If None, files are added at zip root level
        
    Returns:
        Path to the created zip file
        
    Example:
        # Zip with custom folder name
        zip_path = zip_mp_data('MP_Data', 'output.zip', 'user@example.com')
        # Result: user@example.com/please/0/0.npy, etc.
        
        # Zip without folder name (old behavior)
        zip_path = zip_mp_data('MP_Data', 'output.zip')
        # Result: please/0/0.npy, etc.
    '''
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirc, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                
                # If folder_name provided, prepend it to the archive path
                if folder_name:
                    arcname = os.path.join(folder_name, arcname)
                
                zipf.write(file_path, arcname)
    logger.info("Data zipped successfully!")
    return output_file


def main() -> None:
    '''
    Main function to upload MP_Data for the active week to Google Drive.
    
    Uses ACTIVE_WEEK from config to determine which data to upload.
    Handles the complete workflow:
        1. Authenticates with Google Drive
        2. Validates folder structure
        3. Gets contributor information
        4. Zips the MP_Data
        5. Uploads to Google Drive
        6. Verifies upload
        7. Cleans up temporary files
        
    Example:
        Run from command line:
        $ python upload_data.py
    '''
    logger.info("=" * 60)
    logger.info("Starting upload process...")
    logger.info(f"Active Week: {ACTIVE_WEEK}")
    logger.info("=" * 60)
    
    
    # Get Google Drive service
    try:
        service = get_drive_service()
        logger.info("Successfully authenticated with Google Drive")
    except Exception as e:
        logger.error(f"Failed to authenticate: {e}")
        return
    
    # Validate PROJECT_ROOT_ID
    if not validate_folder_structure(service, PROJECT_ROOT_ID):
        logger.error("Cannot proceed - PROJECT_ROOT_ID validation failed")
        return
    
    # Ask for contributor email
    contributor_email = input("Enter contributor email: ").strip()
    if not contributor_email:
        logger.error("Contributor email cannot be empty")
        return
    
    logger.info(f"Processing upload for contributor: {contributor_email}")
    
    # Get or create weekly folder under PROJECT_ROOT_ID
    try:
        weekly_folder_id = create_or_get_contributor_folder(
            service, PROJECT_ROOT_ID, ACTIVE_WEEK
        )
        logger.info(f"Weekly folder ID ({ACTIVE_WEEK}): {weekly_folder_id}")
    except Exception as e:
        logger.error(f"Failed to create/get weekly folder: {e}")
        return
    
    # Create or get contributor folder inside the weekly folder
    try:
        contributor_folder_id = create_or_get_contributor_folder(
            service, weekly_folder_id, contributor_email
        )
        logger.info(f"Contributor folder ID: {contributor_folder_id}")
    except Exception as e:
        logger.error(f"Failed to create/get contributor folder: {e}")
        return
    
    # Prepare the data to upload
    mp_data_path = 'MP_Data'  # Source directory
    zip_filename = f'{ACTIVE_WEEK}.zip'
    
    if not os.path.exists(mp_data_path):
        logger.error(f"MP_Data directory not found: {mp_data_path}")
        return
    
    # Zip the MP_Data folder
    try:
        logger.info(f"Zipping {mp_data_path}...")
        zip_file_path = zip_mp_data(mp_data_path, zip_filename)
        logger.info(f"Created zip file: {zip_file_path}")
    except Exception as e:
        logger.error(f"Failed to zip data: {e}")
        return
    
    # Upload to Google Drive
    try:
        logger.info(f"Uploading {zip_filename} to Google Drive...")
        file_id = upload_zip_folder(service, zip_file_path, contributor_folder_id)
        if file_id:
            logger.info("=" * 60)
            logger.info("✓ Upload completed successfully!")
            logger.info(f"File ID: {file_id}")
            logger.info("=" * 60)
            
            # Verify the upload
            if verify_upload(service, file_id, zip_file_path):
                logger.info("✓ Upload verification successful!")
                
                # Cleanup: Delete the temporary zip file
                try:
                    os.remove(zip_file_path)
                    logger.info(f"✓ Cleaned up temporary file: {zip_file_path}")
                except Exception as cleanup_error:
                    logger.warning(f"⚠ Could not delete temporary file {zip_file_path}: {cleanup_error}")
            else:
                logger.warning("⚠ Upload verification failed - manual check recommended")
                logger.info(f"Temporary file kept for manual inspection: {zip_file_path}")
        else:
            logger.error("Upload failed")
            logger.info(f"Temporary file kept for troubleshooting: {zip_file_path}")
    except Exception as e:
        logger.error(f"Upload error: {e}")
        logger.info(f"Temporary file kept for troubleshooting: {zip_file_path}")


if __name__ == "__main__":
    main()

