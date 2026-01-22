"""
Check what files are currently on Google Drive
"""
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from config import GOOGLE_CREDENTIALS_FILE, PROJECT_ROOT_ID, GOOGLE_DRIVE_SCOPES, ACTIVE_WEEK

SCOPES = GOOGLE_DRIVE_SCOPES

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                raise FileNotFoundError(f"{GOOGLE_CREDENTIALS_FILE} not found.")
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')

        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(service, folder_id, folder_name="Root"):
    """List all files in a folder"""
    print(f"\n{'='*60}")
    print(f"Folder: {folder_name}")
    print(f"{'='*60}")
    
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, size, createdTime, modifiedTime)',
        orderBy='name'
    ).execute()
    
    files = results.get('files', [])
    
    if not files:
        print("  (empty)")
        return []
    
    for f in files:
        size = int(f.get('size', 0)) if f.get('size') else 0
        size_mb = size / (1024 * 1024)
        mime_type = f.get('mimeType', '')
        
        if 'folder' in mime_type:
            print(f"  📁 {f['name']}")
        else:
            print(f"  📄 {f['name']}")
            print(f"      Size: {size_mb:.2f} MB ({size:,} bytes)")
            print(f"      Created: {f.get('createdTime', 'unknown')}")
    
    return files

def main():
    print(f"Checking Google Drive for: {ACTIVE_WEEK}")
    print(f"Root Folder ID: {PROJECT_ROOT_ID}\n")
    
    try:
        service = get_drive_service()
        
        # List files in root
        root_files = list_files_in_folder(service, PROJECT_ROOT_ID, "Project Root")
        
        # Find the week folder
        week_folder = None
        for f in root_files:
            if f['name'] == ACTIVE_WEEK and 'folder' in f.get('mimeType', ''):
                week_folder = f
                break
        
        if week_folder:
            print(f"\n✓ Found {ACTIVE_WEEK} folder")
            week_files = list_files_in_folder(service, week_folder['id'], ACTIVE_WEEK)
            
            # Check zip files
            zip_files = [f for f in week_files if f['name'].endswith('.zip')]
            print(f"\n{'='*60}")
            print(f"Summary: {len(zip_files)} zip file(s) found")
            print(f"{'='*60}")
            
        else:
            print(f"\n✗ {ACTIVE_WEEK} folder not found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
