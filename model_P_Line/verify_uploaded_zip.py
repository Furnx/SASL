"""
Download and verify the uploaded zip file contents
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

def analyze_uploaded_zip(service, file_name, week_folder_id):
    """Download and analyze the most recent uploaded zip"""
    
    # Find the file
    query = f"name='{file_name}' and '{week_folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, 
        fields='files(id, name, size, createdTime)',
        orderBy='createdTime desc'
    ).execute()
    files = results.get('files', [])
    
    if not files:
        print(f"File '{file_name}' not found!")
        return
    
    file_info = files[0]
    file_id = file_info['id']
    file_size = int(file_info.get('size', 0))
    
    print(f"="*70)
    print(f"Downloading: {file_name}")
    print(f"Size: {file_size / (1024*1024):.2f} MB ({file_size:,} bytes)")
    print(f"Created: {file_info.get('createdTime')}")
    print(f"="*70)
    
    # Download to memory
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            if progress % 20 == 0:
                print(f"Download progress: {progress}%")
    
    print("\n" + "="*70)
    print("ZIP FILE ANALYSIS")
    print("="*70)
    
    # Analyze the zip
    fh.seek(0)
    with zipfile.ZipFile(fh, 'r') as zipf:
        all_files = zipf.namelist()
        
        # Organize by sign and sequence
        structure = defaultdict(lambda: defaultdict(list))
        
        for file_path in all_files:
            parts = file_path.split('/')
            if len(parts) >= 4:  # contributor/sign/sequence/frame.npy
                contributor = parts[0]
                sign = parts[1]
                sequence = parts[2]
                frame = parts[3]
                structure[sign][sequence].append(frame)
        
        print(f"\nTotal files in ZIP: {len(all_files)}")
        print(f"\n" + "-"*70)
        print(f"{'SIGN':<15} {'SEQUENCES':<12} {'TOTAL FILES':<15} {'FRAMES/SEQ':<15}")
        print("-"*70)
        
        total_sequences = 0
        total_files = 0
        
        for sign in sorted(structure.keys()):
            sequences = structure[sign]
            num_sequences = len(sequences)
            num_files = sum(len(frames) for frames in sequences.values())
            
            # Check frames per sequence
            frames_per_seq = [len(frames) for frames in sequences.values()]
            min_frames = min(frames_per_seq) if frames_per_seq else 0
            max_frames = max(frames_per_seq) if frames_per_seq else 0
            
            if min_frames == max_frames:
                frames_info = f"{min_frames} frames"
            else:
                frames_info = f"{min_frames}-{max_frames} frames"
            
            print(f"{sign:<15} {num_sequences:<12} {num_files:<15} {frames_info:<15}")
            
            total_sequences += num_sequences
            total_files += num_files
        
        print("-"*70)
        print(f"{'TOTAL':<15} {total_sequences:<12} {total_files:<15}")
        print("="*70)
        
        # Expected values
        expected_signs = 4
        expected_sequences_per_sign = 30
        expected_frames_per_sequence = 30
        expected_total_files = expected_signs * expected_sequences_per_sign * expected_frames_per_sequence
        
        print(f"\nEXPECTED vs ACTUAL:")
        print(f"  Signs:              Expected: {expected_signs}, Found: {len(structure)}")
        print(f"  Sequences per sign: Expected: {expected_sequences_per_sign}, Found: varies")
        print(f"  Frames per sequence:Expected: {expected_frames_per_sequence}, Found: varies")
        print(f"  Total files:        Expected: {expected_total_files}, Found: {len(all_files)}")
        
        if len(all_files) == expected_total_files and len(structure) == expected_signs:
            print(f"\n[OK] Complete upload! All data present.")
        else:
            print(f"\n[WARNING] Data mismatch detected!")
        
        # Show sample structure
        print(f"\n" + "="*70)
        print("SAMPLE STRUCTURE (first sign, first 3 sequences):")
        print("="*70)
        
        first_sign = sorted(structure.keys())[0] if structure else None
        if first_sign:
            sequences = sorted(structure[first_sign].keys())[:3]
            for seq in sequences:
                frames = sorted(structure[first_sign][seq])[:5]
                print(f"\n  {first_sign}/{seq}/")
                for frame in frames:
                    print(f"    - {frame}")
                if len(structure[first_sign][seq]) > 5:
                    print(f"    ... and {len(structure[first_sign][seq]) - 5} more frames")

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
    
    # Analyze the most recent upload
    print(f"Analyzing uploaded file for: {ACTIVE_WEEK}\n")
    analyze_uploaded_zip(service, 'TumoOlorato@gmail.com.zip', week_folder_id)

if __name__ == "__main__":
    main()
