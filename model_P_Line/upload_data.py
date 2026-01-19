import os
import shutil
import zipfile
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import json
from google.oauth2.credentials import Credentials
from config import ACTIVE_WEEK

# ----------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------
# This MUST be the ID of the one main folder where you keep all Week folders
# You still need this ONE ID so the robot knows where to start looking.
PROJECT_ROOT_ID = '1xOUyOz1fiRocPXLqkjHCBaXtEreVTGt3'
SCOPES= ['https://www.googleapis.com/auth/drive']


def get_drive_service():
        '''
        This function handles authentication and returns a Google Drive service object.
        It checks for existing credentials in 'token.json', and if not found or invalid,
        it initiates the OAuth2 flow to obtain new credentials.
        Returns:
            service: Authorized Google Drive service object.
        '''
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        if os.path.exists('token.json'):
            # with open('token.json', 'rb') as token:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not creds or not creds.valid:
            # PUT CREDENTIALS FILE OR CLIENT SECRET PATH HERE
            # Make sure to download from Google Cloud Console
            credentials_file = 'client_secret_979724229670-4pi9if1lqghdih0iluq95fjeoc4dqpq2.apps.googleusercontent.com.json'
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"{credentials_file} not found. Please download it from Google Cloud Console "
                    "and place it in the project root directory."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        # Build the Drive service
        service = build('drive', 'v3', credentials=creds)
        return service


def create_or_get_contributor_folder(service, parent_folder_id, contributor_email):
    '''
    Creates a folder for a contributor if it doesn't exist, or returns the ID of the existing folder.
    Args:
        service: Google Drive service object
        parent_folder_id: ID of the parent folder (where contributor folders are stored)
        contributor_email: Email of the contributor (used as folder name)
    Returns:
        ID of the contributor's folder
    '''
    
    query = (
        f'mimeType="application/vnd.google-apps.folder" '
        f'and "{parent_folder_id}" in parents '
        f'and name="{contributor_email}" '
    )
  
    # Execute the query to find existing contributor folder
    results = service.files().list(
        q=query,spaces='drive',fields='files(id)').execute()
    
    folders = results.get('files',[])

    # If folder doesn't exist, create it
    if not folders:
        folder_metadata = {
            'name': contributor_email,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder['id']
    else:
        return folders[0]['id']


def upload_zip_folder(service, folder_path, parent_folder_id):
    '''
    Uploads a zipped folder to Google Drive under the specified parent folder.
    Args:
        service: Google Drive service object
        folder_path: Path to the zipped folder to upload
        parent_folder_id: ID of the parent folder in Google Drive
    Returns:
        file_id: ID of the uploaded file on Google Drive
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
            fields='id').execute()
        print(f'Uploaded {folder_path} to Google Drive.')
        print('Check if folder uploaded successfully!')
        return file['id']
    except HttpError as e:
        print(f'Upload failed. Please upload manually: {e}')
        return None
    except Exception as e:
        print(f'Unexpected error during upload: {e}')
        return None

def zip_mp_data(source_dir, output_file):
    '''
    Zips the contents of the source directory into a zip file.
    Args:
        source_dir: Directory containing files to zip
        output_file: Path to the output zip file
    Returns:
        Path to the created zip file 
    '''
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirc, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    print("Data zipped successfully!")
    return output_file

