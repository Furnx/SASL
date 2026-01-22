"""
Download and analyze the existing zip from Google Drive
"""
import os
import zipfile
import io
from collections import defaultdict
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload
from config import GOOGLE_CREDENTIALS_FILE, PROJECT_ROOT_ID, GOOGLE_DRIVE_SCOPES, ACTIVE_WEEK

def get_drive_service():
    creds = Credentials.from_authorized_user_file('token.json', GOOGLE_DRIVE_SCOPES)
    return build('drive', 'v3', credentials=creds)

def analyze_drive_zip(service, file_name, week_folder_id):
    """Download and analyze a zip file from Google Drive"""
    
    # Find the file
    query = f"name='{file_name}' and '{week_folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id, name, size)').execute()
    files = results.get('files', [])
    
    if not files:
        print(f"File '{file_name}' not found!")
        return
    
    file_info = files[0]
    file_id = file_info['id']
    file_size = int(file_info.get('size', 0))
    
    print(f"Downloading: {file_name}")
    print(f"Size: {file_size / (1024*1024):.2f} MB ({file_size:,} bytes)\n")
    
    # Download to memory
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"Download progress: {int(status.progress() * 100)}%")
    
    print("\n" + "="*60)
    print("Analyzing ZIP contents:")
    print("="*60)
    
    # Analyze the zip
    fh.seek(0)
    with zipfile.ZipFile(fh, 'r') as zipf:
        all_files = zipf.namelist()
        
        sign_counts = defaultdict(int)
        for f in all_files:
            parts = f.split('/')
            if len(parts) >= 2:
                sign = parts[1]  # contributor/sign/...
                sign_counts[sign] += 1
        
        print(f"Total files in ZIP: {len(all_files)}")
        print(f"\nFiles per sign:")
        print("-"*60)
        
        for sign in sorted(sign_counts.keys()):
            print(f"  {sign:15s} : {sign_counts[sign]:4d} files")
        
        print("\n" + "="*60)
        expected_per_sign = 900
        total_expected = 3600
        
        if len(all_files) == total_expected:
            print(f"✓ Complete! All {total_expected} files present")
        else:
            print(f"✗ INCOMPLETE!")
            print(f"  Expected: {total_expected} files")
            print(f"  Found:    {len(all_files)} files")
            print(f"  Missing:  {total_expected - len(all_files)} files")
            
            missing_signs = []
            for sign in ['what', 'where', 'who', 'why']:
                if sign_counts[sign] < expected_per_sign:
                    missing_signs.append(sign)
            
            if missing_signs:
                print(f"\n  Signs with missing files: {', '.join(missing_signs)}")

def main():
    service = get_drive_service()
    
    # Get week folder
    query = f"name='{ACTIVE_WEEK}' and '{PROJECT_ROOT_ID}' in parents and trashed=false"
    results = service.files().list(q=query, fields='files(id)').execute()
    folders = results.get('files', [])
    
    if not folders:
        print(f"{ACTIVE_WEEK} folder not found!")
        return
    
    week_folder_id = folders[0]['id']
    
    # Analyze your uploaded file
    analyze_drive_zip(service, 'tumomogame9.co.za.zip', week_folder_id)

if __name__ == "__main__":
    main()
