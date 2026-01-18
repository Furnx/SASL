import os
import shutil
import zipfile
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# ----------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/drive']
# This MUST be the ID of the one main folder where you keep all Week folders
# You still need this ONE ID so the robot knows where to start looking.
PROJECT_ROOT_ID = '1_PLACEHOLDER_FOR_YOUR_PROJECT_ROOT_ID' 

def authenticate_drive():
    """ Validates the 'digital ID card'."""
    if os.path.exists('service_account.json'):
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', scopes=SCOPES)
        return build('drive', 'v3', credentials=creds)
    else:
        print("❌ Error: 'service_account.json' not found.")
        return None

def find_folder_by_name(service, folder_name, parent_id):
    """
    Searches for a specific folder name inside a parent folder.
    Returns the ID if found, None if not found.
    """
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])

    if files:
        return files[0]['id'] # Found it!
    else:
        return None # Not found

def get_or_create_folder(service, folder_name, parent_id):
    """Finds or creates a folder."""
    folder_id = find_folder_by_name(service, folder_name, parent_id)
    
    if folder_id:
        return folder_id
    else:
        print(f"✨ Creating Drive folder: '{folder_name}'")
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

def zip_folder(folder_path, output_path):
    """Zips a folder."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def upload_local_data_structure(mp_data_path, week_folder_name):
    """
    1. Finds the Week folder by NAME.
    2. Uploads data into it.
    """
    service = authenticate_drive()
    if not service:
        return

    print(f"\n🔍 Searching for Week Folder: '{week_folder_name}'...")
    
    # STEP 1: Find the Week Folder automatically
    week_folder_id = find_folder_by_name(service, week_folder_name, PROJECT_ROOT_ID)
    
    if not week_folder_id:
        print(f"❌ Error: Could not find a folder named '{week_folder_name}' in Google Drive.")
        print("   Please make sure you created it manually first!")
        return

    print(f"✅ Found '{week_folder_name}' (ID: {week_folder_id})")
    print(f"🚀 Starting Batch Upload...")

    # Loop through Sign folders (Hello, Yes, Alive...)
    if not os.path.exists(mp_data_path):
        print("No data found to upload.")
        return

    for sign_name in os.listdir(mp_data_path):
        sign_path = os.path.join(mp_data_path, sign_name)
        if not os.path.isdir(sign_path): continue

        print(f"\nProcessing Sign: {sign_name}...")
        
        # Get/Create 'Hello' folder inside 'Week_1_Greetings'
        drive_sign_folder_id = get_or_create_folder(service, sign_name, week_folder_id)

        # Zip and Upload User Folders
        for user_seq_folder in os.listdir(sign_path):
            user_seq_path = os.path.join(sign_path, user_seq_folder)
            if not os.path.isdir(user_seq_path): continue

            temp_zip_name = f"{user_seq_folder}.zip"
            temp_zip_path = os.path.join(sign_path, temp_zip_name)
            
            print(f"  - Uploading: {user_seq_folder}")
            zip_folder(user_seq_path, temp_zip_path)

            file_metadata = {'name': temp_zip_name, 'parents': [drive_sign_folder_id]}
            media = MediaFileUpload(temp_zip_path, mimetype='application/zip', resumable=True)

            try:
                service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print("    ✅ Done.")
            except Exception as e:
                print(f"    ❌ Failed: {e}")

            if os.path.exists(temp_zip_path):
                os.remove(temp_zip_path)

    print("\n🎉 All uploads finished!")