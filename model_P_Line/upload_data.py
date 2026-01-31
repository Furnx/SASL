"""
Google Drive Upload Module for SASL Sign Language Project
"""
import os
import zipfile
import logging
import time
from functools import wraps
from typing import Optional, Callable, Any

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# Assuming these are defined in your config.py
from config import ACTIVE_WEEK, GOOGLE_CREDENTIALS_FILE, PROJECT_ROOT_ID, GOOGLE_DRIVE_SCOPES

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
MAX_RETRIES = 3
RETRY_DELAY = 2
RETRY_BACKOFF = 2

def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY, backoff: float = RETRY_BACKOFF) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached for {func.__name__}")
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
    creds = None
    if os.path.exists('token.json'):
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        except Exception:
            # If reading the file fails, treat it as missing
            creds = None

    # If no valid credentials, we need to log in or refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                # 1. Try to refresh the token automatically
                creds.refresh(Request())
            except Exception as e:
                # 2. IF REFRESH FAILS: Print error and force a new login
                print(f"⚠️ Token refresh failed: {e}")
                print("🔄 Starting new login flow...")
                creds = None # Discard the broken credentials
        
        # If we still don't have valid creds (because we had none, or refresh failed)
        if not creds:
            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(f"{GOOGLE_CREDENTIALS_FILE} not found.")
            
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
            # 'access_type=offline' is CRITICAL to get a refresh_token for next time
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

        # Save the new/refreshed token
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def validate_folder_structure(service, folder_id: str) -> bool:
    try:
        folder = service.files().get(fileId=folder_id, fields='id, name, mimeType').execute()
        return folder.get('mimeType') == 'application/vnd.google-apps.folder'
    except Exception as e:
        logger.error(f"Folder validation failed for ID {folder_id}: {e}")
        return False

def create_or_get_contributor_folder(service, parent_folder_id: str, folder_name: str) -> str:
    # Clean folder name to prevent query errors
    folder_name = folder_name.replace("'", "\\'")
    query = (
        f"mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_folder_id}' in parents "
        f"and name='{folder_name}' "
        f"and trashed=false"
    )

    results = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
    folders = results.get('files', [])

    if not folders:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']
    return folders[0]['id']

@retry_on_failure()
def upload_zip_folder(service, folder_path: str, parent_folder_id: str) -> Optional[str]:
    """
    Upload a zip file to Google Drive with proper chunking and progress tracking.
    Uses resumable upload with smaller chunk size for better reliability.
    """
    filename = os.path.basename(folder_path)
    file_size = os.path.getsize(folder_path)
    
    file_metadata = {
        'name': filename,
        'parents': [parent_folder_id]
    }
    
    # Use smaller chunk size (5MB) for better reliability with large files
    # Default is 100MB which can timeout on slower connections
    chunk_size = 5 * 1024 * 1024  # 5MB chunks
    media = MediaFileUpload(
        folder_path, 
        mimetype='application/zip', 
        resumable=True,
        chunksize=chunk_size
    )
    
    logger.info(f"Starting upload of {filename} ({file_size / (1024*1024):.2f} MB)")
    
    try: 
        request = service.files().create(body=file_metadata, media_body=media, fields='id, size, name')
        
        response = None
        last_progress = -1
        
        while response is None:
            status, response = request.next_chunk()
            if status:
                current_progress = int(status.progress() * 100)
                # Only log every 5% to reduce noise
                if current_progress != last_progress and current_progress % 5 == 0:
                    logger.info(f"Upload progress: {current_progress}%")
                    last_progress = current_progress
        
        file_id = response.get('id')
        uploaded_size = response.get('size', 'unknown')
        logger.info(f"[OK] Upload completed! File ID: {file_id}, Size: {uploaded_size} bytes")
        
        return file_id
    except HttpError as e:
        logger.error(f'HTTP Error during upload: {e}')
        return None
    except Exception as e:
        logger.error(f'Upload failed: {e}')
        return None

def verify_upload(service, file_id: str, local_file_path: str) -> bool:
    """
    Verify that the uploaded file matches the local file in size.
    Returns True if sizes match, False otherwise.
    """
    try:
        file_info = service.files().get(fileId=file_id, fields='size, name').execute()
        remote_size = int(file_info.get('size', 0))
        remote_name = file_info.get('name', 'unknown')
        local_size = os.path.getsize(local_file_path)
        
        logger.info(f"Verification:")
        logger.info(f"  Local file:  {os.path.basename(local_file_path)} ({local_size:,} bytes)")
        logger.info(f"  Remote file: {remote_name} ({remote_size:,} bytes)")
        
        if remote_size == local_size:
            logger.info(f"[OK] File sizes match!")
            return True
        else:
            logger.error(f"✗ Size mismatch! Difference: {abs(remote_size - local_size):,} bytes")
            return False
            
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return False

def zip_mp_data(source_dir: str, output_file: str, target_sign_list: list, folder_name: Optional[str] = None) -> str:
    """
    Zips ONLY the folders matching the target_sign_list.
    """
    file_count = 0
    total_size = 0
    
    logger.info(f"Starting zip of {len(target_sign_list)} signs...")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Loop ONLY through the specific signs we want (e.g., ['hello', 'goodbye'])
        for sign in target_sign_list:
            sign_path = os.path.join(source_dir, sign)
            
            if not os.path.exists(sign_path):
                logger.warning(f"Skipping {sign} - folder not found!")
                continue

            # Walk through this specific sign's folder
            for root, dirs, files in os.walk(sign_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Calculate the internal zip path
                    rel_path = os.path.relpath(file_path, source_dir)
                    if folder_name:
                        arcname = os.path.join(folder_name, rel_path)
                    else:
                        arcname = rel_path
                    
                    zipf.write(file_path, arcname)
                    file_count += 1
                    total_size += os.path.getsize(file_path)

    zip_size = os.path.getsize(output_file)
    logger.info(f"[OK] Zipped {file_count} files ({total_size / (1024*1024):.2f} MB)")
    
    return output_file

def main() -> None:
    logger.info(f"{'='*30}\nStarting Upload: {ACTIVE_WEEK}\n{'='*30}")
    
    try:
        service = get_drive_service()
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        return
    
    if not validate_folder_structure(service, PROJECT_ROOT_ID):
        logger.error("Root ID invalid.")
        return
    
    contributor_email = input("Enter contributor email: ").strip()
    if not contributor_email:
        logger.error("No email provided.")
        return

    try:
        # Create/Get Weekly Folder under ROOT (ROOT/Week_X/)
        logger.info(f"Creating/getting folder for {ACTIVE_WEEK}...")
        weekly_folder_id = create_or_get_contributor_folder(service, PROJECT_ROOT_ID, ACTIVE_WEEK)
        
        mp_data_path = 'MP_Data'
        # Simple zip naming: username.zip
        zip_filename = f"{contributor_email}.zip"
        
        if not os.path.exists(mp_data_path):
            logger.error("Source MP_Data not found.")
            return

        logger.info(f"Zipping data to {zip_filename}...")
        logger.info(f"Organizing data under folder: {contributor_email}")
        zip_file_path = zip_mp_data(mp_data_path, zip_filename, folder_name=contributor_email)
        
        logger.info(f"Uploading to Google Drive folder: {ACTIVE_WEEK}...")
        file_id = upload_zip_folder(service, zip_file_path, weekly_folder_id)

        if file_id:
            logger.info(f"Success! Uploaded with ID: {file_id}")
            
            logger.info("Verifying upload...")
            if verify_upload(service, file_id, zip_file_path):
                logger.info("Upload verified successfully!")
                os.remove(zip_file_path)
                logger.info(f"Cleaned up temporary file: {zip_filename}")
            else:
                logger.warning("Upload verification failed - manual check recommended")
                logger.warning(f"Temporary file kept: {zip_filename}")
        else:
            logger.error(f"Upload failed. Temporary file kept: {zip_filename}")

    except Exception as e:
        logger.error(f"Process failed: {e}")

if __name__ == "__main__":
    main()