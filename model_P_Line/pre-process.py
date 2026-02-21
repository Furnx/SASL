# # # # # # # # import io
# # # # # # # # import zipfile
# # # # # # # # import os
# # # # # # # # from googleapiclient.http import MediaIoBaseDownload
# # # # # # # # from config import ACTIVE_WEEK, PROJECT_ROOT_ID
# # # # # # # from upload_data import get_drive_service

# # # # # # # """
# # # # # # # - This file is to be used before training, running train/_transformer.py and predict/_transformer.py
# # # # # # # - THis file downloads data from the drive, saves data locally, unzips and standarises the data for training
# # # # # # # - Creates a folder for the week in the local directory, and saves all data in that folder.
# # # # # # # """


# # # # # # # # # THIRD ATTEMPT- MANUALLY DOWNLOAD DATA, THIS SCRPIT NORMALISES DATA IN TO MP_DATA FOLDER
# # # # # # # # import os
# # # # # # # # import zipfile
# # # # # # # # import shutil
# # # # # # # # from pathlib import Path


# # # # # # # # def ensure_dir(path: Path):
# # # # # # # #     path.mkdir(parents=True, exist_ok=True)


# # # # # # # # def unzip_if_needed(item: Path, extract_to: Path):
# # # # # # # #     if item.suffix == ".zip":
# # # # # # # #         with zipfile.ZipFile(item, "r") as z:
# # # # # # # #             z.extractall(extract_to)
# # # # # # # #         return extract_to
# # # # # # # #     return item


# # # # # # # # def move_video_safely(src: Path, dst_dir: Path):
# # # # # # # #     ensure_dir(dst_dir)

# # # # # # # #     target = dst_dir / src.name
# # # # # # # #     if not target.exists():
# # # # # # # #         shutil.move(str(src), str(target))
# # # # # # # #         return

# # # # # # # #     i = 1
# # # # # # # #     while True:
# # # # # # # #         new_target = dst_dir / f"{src.name}_{i}"
# # # # # # # #         if not new_target.exists():
# # # # # # # #             shutil.move(str(src), str(new_target))
# # # # # # # #             return
# # # # # # # #         i += 1


# # # # # # # # def is_sign_folder(folder: Path):
# # # # # # # #     # sign folder contains video folders
# # # # # # # #     return any(p.is_dir() for p in folder.iterdir())


# # # # # # # # def normalize_week(
# # # # # # # #     active_week: str,
# # # # # # # #     drive_data_root="drive_data",
# # # # # # # #     mp_data_root="MP_data"
# # # # # # # # ):
# # # # # # # #     drive_week = Path(drive_data_root) / active_week
# # # # # # # #     mp_week = Path(mp_data_root) / active_week

# # # # # # # #     ensure_dir(mp_week)

# # # # # # # #     print(f"\n🔄 Normalizing data for {active_week}\n")

# # # # # # # #     for item in drive_week.iterdir():
# # # # # # # #         temp_dir = drive_week / f"_tmp_{item.stem}"

# # # # # # # #         extracted = unzip_if_needed(item, temp_dir)
# # # # # # # #         extracted_items = list(extracted.iterdir())

# # # # # # # #         for top in extracted_items:

# # # # # # # #             # CASE 1: sign → videos
# # # # # # # #             if top.is_dir() and is_sign_folder(top):
# # # # # # # #                 sign = top.name
# # # # # # # #                 sign_target = mp_week / sign
# # # # # # # #                 ensure_dir(sign_target)

# # # # # # # #                 videos = [v for v in top.iterdir() if v.is_dir()]
# # # # # # # #                 for v in videos:
# # # # # # # #                     move_video_safely(v, sign_target)

# # # # # # # #                 print(f"✅ Sign merged: {sign} ({len(videos)} videos)")

# # # # # # # #             # CASE 2: user → signs → videos
# # # # # # # #             elif top.is_dir():
# # # # # # # #                 user_folder = top

# # # # # # # #                 for sign_folder in user_folder.iterdir():
# # # # # # # #                     if not sign_folder.is_dir():
# # # # # # # #                         continue

# # # # # # # #                     sign = sign_folder.name
# # # # # # # #                     sign_target = mp_week / sign
# # # # # # # #                     ensure_dir(sign_target)

# # # # # # # #                     videos = [v for v in sign_folder.iterdir() if v.is_dir()]
# # # # # # # #                     for v in videos:
# # # # # # # #                         move_video_safely(v, sign_target)

# # # # # # # #                     print(f"👤 User data merged: {sign} ({len(videos)} videos)")

# # # # # # # #         if temp_dir.exists():
# # # # # # # #             shutil.rmtree(temp_dir)

# # # # # # # #     print(f"\n🎉 Normalization complete for {active_week}")

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     normalize_week('Week_4_Grammar',drive_data_root="drive_data", mp_data_root="MP_Data")

# # # # # # # # SECOND ATTEMPT- MANUALLY DOWNLOAD DATA, THIS SCRPIT NORMALISES DATA IN TO MP_DATA FOLDER
# # # # # # # import os
# # # # # # # import shutil
# # # # # # # import zipfile

# # # # # # # # =========================
# # # # # # # # CONFIG
# # # # # # # # =========================

# # # # # # # DRIVE_DATA_ROOT = "drive_data"
# # # # # # # MP_DATA_ROOT = "MP_data"
# # # # # # # ACTIVE_WEEK = "Week_4_Grammar"   # 🔁 change this only

# # # # # # # # =========================
# # # # # # # # HELPERS
# # # # # # # # =========================

# # # # # # # def ensure_dir(path):
# # # # # # #     os.makedirs(path, exist_ok=True)

# # # # # # # def unzip_all(folder):
# # # # # # #     for item in os.listdir(folder):
# # # # # # #         if item.endswith(".zip"):
# # # # # # #             zip_path = os.path.join(folder, item)
# # # # # # #             extract_to = zip_path.replace(".zip", "")

# # # # # # #             if not os.path.exists(extract_to):
# # # # # # #                 print(f"📦 Unzipping {item}")
# # # # # # #                 with zipfile.ZipFile(zip_path, 'r') as z:
# # # # # # #                     z.extractall(extract_to)

# # # # # # # def move_video_safely(src, dst_dir):
# # # # # # #     ensure_dir(dst_dir)

# # # # # # #     video_name = os.path.basename(src)
# # # # # # #     dst = os.path.join(dst_dir, video_name)

# # # # # # #     counter = 1
# # # # # # #     while os.path.exists(dst):
# # # # # # #         dst = os.path.join(dst_dir, f"{video_name}_{counter}")
# # # # # # #         counter += 1

# # # # # # #     shutil.move(src, dst)

# # # # # # # # =========================
# # # # # # # # CORE NORMALIZATION
# # # # # # # # =========================

# # # # # # # def normalize_week():
# # # # # # #     week_drive_path = os.path.join(DRIVE_DATA_ROOT, ACTIVE_WEEK)
# # # # # # #     week_mp_path = os.path.join(MP_DATA_ROOT, ACTIVE_WEEK)

# # # # # # #     ensure_dir(week_mp_path)

# # # # # # #     # Step 1: unzip everything
# # # # # # #     unzip_all(week_drive_path)

# # # # # # #     # Step 2: walk through week folder
# # # # # # #     for item in os.listdir(week_drive_path):
# # # # # # #         item_path = os.path.join(week_drive_path, item)

# # # # # # #         if not os.path.isdir(item_path):
# # # # # # #             continue

# # # # # # #         # CASE 1: item IS a sign folder
# # # # # # #         if is_sign_folder(item_path):
# # # # # # #             process_sign_folder(item_path, week_mp_path)

# # # # # # #         # CASE 2: item is a user folder containing sign folders
# # # # # # #         else:
# # # # # # #             for sub in os.listdir(item_path):
# # # # # # #                 sub_path = os.path.join(item_path, sub)
# # # # # # #                 if os.path.isdir(sub_path) and is_sign_folder(sub_path):
# # # # # # #                     process_sign_folder(sub_path, week_mp_path)

# # # # # # #     print("✅ Normalization complete.")

# # # # # # # # =========================
# # # # # # # # SIGN PROCESSING
# # # # # # # # =========================

# # # # # # # def is_sign_folder(path):
# # # # # # #     # Heuristic: contains video folders
# # # # # # #     for item in os.listdir(path):
# # # # # # #         if os.path.isdir(os.path.join(path, item)):
# # # # # # #             return True
# # # # # # #     return False

# # # # # # # def process_sign_folder(sign_path, week_mp_path):
# # # # # # #     sign_name = os.path.basename(sign_path)
# # # # # # #     sign_dst = os.path.join(week_mp_path, sign_name)

# # # # # # #     ensure_dir(sign_dst)

# # # # # # #     for video in os.listdir(sign_path):
# # # # # # #         video_path = os.path.join(sign_path, video)

# # # # # # #         if os.path.isdir(video_path):
# # # # # # #             move_video_safely(video_path, sign_dst)

# # # # # # # # =========================
# # # # # # # # ENTRY POINT
# # # # # # # # =========================

# # # # # # # if __name__ == "__main__":
# # # # # # #     normalize_week()


# # # # # # # another attempt gain
# # # # # # import zipfile
# # # # # # import shutil
# # # # # # from pathlib import Path

# # # # # # def normalize_dataset(source_dir, output_dir, temp_extract_dir='temp_unzipped'):
# # # # # #     source_path = Path(source_dir)
# # # # # #     output_path = Path(output_dir)
# # # # # #     temp_path = Path(temp_extract_dir)

# # # # # #     # 1. Handle Zipped User Folders
# # # # # #     for zip_file in source_path.glob('*.zip'):
# # # # # #         print(f"Extracting {zip_file.name}...")
# # # # # #         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
# # # # # #             # Extract into a subfolder named after the zip file (User Name)
# # # # # #             zip_ref.extractall(temp_path / zip_file.stem)

# # # # # #     # 2. Process all data (Original Week folders + Extracted User folders)
# # # # # #     # Search in both source and temp directories
# # # # # #     for search_root in [source_path, temp_path]:
# # # # # #         if not search_root.exists():
# # # # # #             continue

# # # # # #         for file_path in search_root.rglob('*'):
# # # # # #             # Filter for frame files (adjust extension as needed, e.g., .jpg, .png)
# # # # # #             if file_path.is_file() and file_path.suffix.lower() in ['.np']:
                
# # # # # #                 parts = file_path.parts
# # # # # #                 # Structure: ... / [Root] / [Sign] / [VideoID] / [Frame]
# # # # # #                 # parts[-4]  parts[-3]  parts[-2]     parts[-1]
                
# # # # # #                 root_folder = parts[-4] 
# # # # # #                 sign_name = parts[-3]
# # # # # #                 video_id = parts[-2]
# # # # # #                 frame_name = parts[-1]

# # # # # #                 # Assign to a week. If the folder isn't a "week", 
# # # # # #                 # we'll label it "unassigned" or a specific week of your choice.
# # # # # #                 target_week = root_folder if "week" in root_folder.lower() else "week_user_contributions"

# # # # # #                 # Unique Video ID to prevent overwriting: User_VideoID
# # # # # #                 unique_video_name = f"{root_folder}_{video_id}"

# # # # # #                 # Construct: output/week/sign/user_video/frame
# # # # # #                 final_dest = output_path / target_week / sign_name / unique_video_name
# # # # # #                 final_dest.mkdir(parents=True, exist_ok=True)

# # # # # #                 shutil.copy2(file_path, final_dest / frame_name)

# # # # # #     # # 3. Cleanup temp files if desired
# # # # # #     # # shutil.rmtree(temp_path)
# # # # # #     # print(f"Successfully normalized to: {output_path.absolute()}")

# # # # # # # Run it
# # # # # # normalize_dataset('drive_data', 'mp_data')

# # # # # import zipfile
# # # # # import shutil
# # # # # import numpy as np
# # # # # from pathlib import Path

# # # # # def normalize_dataset(source_dir, output_dir):
# # # # #     source_path = Path(source_dir)
# # # # #     output_path = Path(output_dir)
# # # # #     temp_path = Path("temp_extraction")

# # # # #     # 1. Extract ZIPs first
# # # # #     for zip_file in source_path.rglob('*.zip'):
# # # # #         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
# # # # #             # Extract to a folder named after the zip file
# # # # #             zip_ref.extractall(temp_path / zip_file.stem)

# # # # #     # 2. Process all .npy files from both source and temp
# # # # #     for search_root in [source_path, temp_path]:
# # # # #         if not search_root.exists(): continue

# # # # #         for npy_path in search_root.rglob('*.npy'):
# # # # #             # Logic to find Week, Sign, and Video name
# # # # #             # This assumes a structure like: Week/Sign/Video.npy
# # # # #             parts = npy_path.parts
# # # # #             sign_name = parts[-2] 
# # # # #             file_name = parts[-1]
            
# # # # #             # Identify the Week (defaulting to 'Week_1' if not found)
# # # # #             week_folder = next((p for p in parts if "week" in p.lower()), "week_all")

# # # # #             # Validate the 30-frame requirement
# # # # #             try:
# # # # #                 data = np.load(npy_path)
# # # # #                 if data.shape[0] != 30:
# # # # #                     print(f"Skipping {file_name}: Invalid shape {data.shape}")
# # # # #                     continue
# # # # #             except Exception as e:
# # # # #                 print(f"Could not load {file_name}: {e}")
# # # # #                 continue

# # # # #             # PREPARE DESTINATION
# # # # #             # Structure: output/week_1/hello/user_video1.npy
# # # # #             unique_filename = f"{parts[-3]}_{file_name}" # Prefixes with parent folder
# # # # #             final_dest_dir = output_path / week_folder / sign_name
            
# # # # #             # THIS CREATES THE DIRECTORY AUTOMATICALLY
# # # # #             final_dest_dir.mkdir(parents=True, exist_ok=True)

# # # # #             # COPY FILE
# # # # #             shutil.copy2(npy_path, final_dest_dir / unique_filename)

# # # # #     # Cleanup temp folder
# # # # #     if temp_path.exists():
# # # # #         shutil.rmtree(temp_path)
    
# # # # #     print("Done! Your directories are created and files are moved.")

# # # # # Run: normalize_dataset('drive_data/Week_4_Grammar', 'normalized_data')

# # # # import zipfile
# # # # import shutil
# # # # import numpy as np
# # # # from pathlib import Path

# # # # def normalize_to_sign_folders(source_dir, output_dir):
# # # #     source_path = Path(source_dir)
# # # #     output_path = Path(output_dir)
# # # #     temp_path = Path("temp_extraction")

# # # #     # 1. Extract ZIPs (Users)
# # # #     for zip_file in source_path.rglob('*.zip'):
# # # #         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
# # # #             zip_ref.extractall(temp_path / zip_file.stem)

# # # #     # 2. Process everything
# # # #     for search_root in [source_path, temp_path]:
# # # #         if not search_root.exists(): continue

# # # #         for npy_path in search_root.rglob('*.npy'):
# # # #             parts = npy_path.parts
            
# # # #             # Extract names based on your structure: .../Sign/Video.npy
# # # #             # We assume the parent of the file is the Sign folder
# # # #             sign_name = npy_path.parent.name 
# # # #             file_name = npy_path.name
            
# # # #             # To keep them unique in the same folder, we use the "Grandparent" name
# # # #             # e.g., 'UserA_video1.npy' or 'Week1_video1.npy'
# # # #             folder_identifier = npy_path.parent.parent.name
# # # #             unique_name = f"{folder_identifier}_{file_name}"

# # # #             # TARGET: output / sign_name / unique_name.npy
# # # #             final_dest_dir = output_path / sign_name
            
# # # #             # This creates the Sign folder if it doesn't exist, 
# # # #             # or just moves on if it does.
# # # #             final_dest_dir.mkdir(parents=True, exist_ok=True)

# # # #             # Move or Copy
# # # #             shutil.copy2(npy_path, final_dest_dir / unique_name)

# # # #     # Cleanup
# # # #     if temp_path.exists(): shutil.rmtree(temp_path)
# # # #     print(f"Done! All videos are now inside their respective Sign folders in: {output_dir}")

# # # # normalize_to_sign_folders('drive_data/Week_4_Grammar', 'normalised_dataset')

# # # import zipfile
# # # import shutil
# # # from pathlib import Path

# # # def normalize_to_mp_data(active_week):
# # #     # Setup paths
# # #     source_root = Path('drive_data/Week_4_Grammar')
# # #     output_root = Path("MP_data")
# # #     temp_extract = Path("temp_unzip")
    
# # #     # 1. Unzip any user zip files
# # #     if source_root.exists():
# # #         for zip_item in source_root.glob("*.zip"):
# # #             user_id = zip_item.stem
# # #             with zipfile.ZipFile(zip_item, 'r') as z:
# # #                 z.extractall(temp_extract / user_id)

# # #     # 2. Define our search areas: the Week folder and the Temp Unzipped folder
# # #     search_areas = []
# # #     if source_root.exists(): search_areas.append(source_root)
# # #     if temp_extract.exists(): search_areas.append(temp_extract)

# # #     for root in search_areas:
# # #         # Loop through each 'User' or 'Week' folder
# # #         for source_folder in root.iterdir():
# # #             if not source_folder.is_dir(): continue
            
# # #             # source_folder is now 'UserA' or the week subfolder
# # #             user_label = source_folder.name 

# # #             # Loop through each 'Sign' folder (e.g., 'hello')
# # #             for sign_folder in source_folder.iterdir():
# # #                 if not sign_folder.is_dir(): continue
                
# # #                 sign_name = sign_folder.name
                
# # #                 # Create the Sign folder in MP_data
# # #                 target_sign_path = output_root / sign_name
# # #                 target_sign_path.mkdir(parents=True, exist_ok=True)

# # #                 # Loop through each 'Video' folder inside the Sign
# # #                 for video_folder in sign_folder.iterdir():
# # #                     if not video_folder.is_dir(): continue
                    
# # #                     # New name: UserA_video_1 (to keep it unique)
# # #                     new_video_name = f"{user_label}_{video_folder.name}"
# # #                     dest_path = target_sign_path / new_video_name

# # #                     # MOVE the whole video folder (including all its .npy frames)
# # #                     if not dest_path.exists():
# # #                         shutil.copytree(video_folder, dest_path)
# # #                     else:
# # #                         print(f"Skipping {new_video_name}, already exists in {sign_name}")

# # #     # Cleanup
# # #     if temp_extract.exists():
# # #         shutil.rmtree(temp_extract)
        
# # #     print(f"Done! All data is now in: {output_root.absolute()}")

# # # # Run it
# # # normalize_to_mp_data("week_1")

# # import zipfile
# # import shutil
# # import os
# # from pathlib import Path

# # def normalize_to_mp_data(active_week):
# #     # 1. Setup paths
# #     source_root = Path(active_week)
# #     output_root = Path("MP_data")
# #     temp_extract = Path("temp_unzip")
    
# #     # 2. Extract User Zips into the temp folder
# #     if source_root.exists():
# #         for zip_item in source_root.glob("*.zip"):
# #             user_id = zip_item.stem
# #             with zipfile.ZipFile(zip_item, 'r') as z:
# #                 # Extracts to: temp_unzip/UserA/
# #                 z.extractall(temp_extract / user_id)

# #     # 3. Create a list of all "Top-Level" source folders (Weeks and Unzipped Users)
# #     # We are looking for the folders that contain the 'Sign' folders
# #     search_paths = []
    
# #     # Add unzipped user folders
# #     if temp_extract.exists():
# #         search_paths.extend([f for f in temp_extract.iterdir() if f.is_dir()])
    
# #     # Add existing week subfolders if they aren't zips
# #     if source_root.exists():
# #         search_paths.extend([f for f in source_root.iterdir() if f.is_dir()])

# #     # 4. The Core Logic: Sign First
# #     for user_folder in search_paths:
# #         user_name = user_folder.name # e.g., 'UserA' or 'Week1'
        
# #         # Iterate through the Signs inside each user folder
# #         for sign_folder in user_folder.iterdir():
# #             if not sign_folder.is_dir(): continue
            
# #             sign_name = sign_folder.name # e.g., 'hello'
            
# #             # Create the SIGN folder as the MAIN category in MP_data
# #             target_sign_path = output_root / sign_name
# #             target_sign_path.mkdir(parents=True, exist_ok=True)

# #             # Move every Video Folder from this sign into the Main Sign folder
# #             for video_folder in sign_folder.iterdir():
# #                 if not video_folder.is_dir(): continue
                
# #                 # We rename the video folder to include the user's name
# #                 # This puts all "hello" videos from all users in one "hello" folder
# #                 unique_video_name = f"{user_name}_{video_folder.name}"
# #                 dest_path = target_sign_path / unique_video_name

# #                 # Copy the entire video folder (all .npy files)
# #                 if not dest_path.exists():
# #                     shutil.copytree(video_folder, dest_path)

# #     # 5. Cleanup
# #     if temp_extract.exists():
# #         shutil.rmtree(temp_extract)
        
# #     print(f"Success! '{output_root.absolute()}' is now organized by Sign.")

# # # Usage
# # normalize_to_mp_data("drive_data/Week_4_Grammar")# # # # # import io
# # # # # # # # import zipfile
# # # # # # # # import os
# # # # # # # # from googleapiclient.http import MediaIoBaseDownload
# # # # # # # # from config import ACTIVE_WEEK, PROJECT_ROOT_ID
# # # # # # # from upload_data import get_drive_service

# # # # # # # """
# # # # # # # - This file is to be used before training, running train/_transformer.py and predict/_transformer.py
# # # # # # # - THis file downloads data from the drive, saves data locally, unzips and standarises the data for training
# # # # # # # - Creates a folder for the week in the local directory, and saves all data in that folder.
# # # # # # # """


# # # # # # # # # THIRD ATTEMPT- MANUALLY DOWNLOAD DATA, THIS SCRPIT NORMALISES DATA IN TO MP_DATA FOLDER
# # # # # # # # import os
# # # # # # # # import zipfile
# # # # # # # # import shutil
# # # # # # # # from pathlib import Path


# # # # # # # # def ensure_dir(path: Path):
# # # # # # # #     path.mkdir(parents=True, exist_ok=True)


# # # # # # # # def unzip_if_needed(item: Path, extract_to: Path):
# # # # # # # #     if item.suffix == ".zip":
# # # # # # # #         with zipfile.ZipFile(item, "r") as z:
# # # # # # # #             z.extractall(extract_to)
# # # # # # # #         return extract_to
# # # # # # # #     return item


# # # # # # # # def move_video_safely(src: Path, dst_dir: Path):
# # # # # # # #     ensure_dir(dst_dir)

# # # # # # # #     target = dst_dir / src.name
# # # # # # # #     if not target.exists():
# # # # # # # #         shutil.move(str(src), str(target))
# # # # # # # #         return

# # # # # # # #     i = 1
# # # # # # # #     while True:
# # # # # # # #         new_target = dst_dir / f"{src.name}_{i}"
# # # # # # # #         if not new_target.exists():
# # # # # # # #             shutil.move(str(src), str(new_target))
# # # # # # # #             return
# # # # # # # #         i += 1


# # # # # # # # def is_sign_folder(folder: Path):
# # # # # # # #     # sign folder contains video folders
# # # # # # # #     return any(p.is_dir() for p in folder.iterdir())


# # # # # # # # def normalize_week(
# # # # # # # #     active_week: str,
# # # # # # # #     drive_data_root="drive_data",
# # # # # # # #     mp_data_root="MP_data"
# # # # # # # # ):
# # # # # # # #     drive_week = Path(drive_data_root) / active_week
# # # # # # # #     mp_week = Path(mp_data_root) / active_week

# # # # # # # #     ensure_dir(mp_week)

# # # # # # # #     print(f"\n🔄 Normalizing data for {active_week}\n")

# # # # # # # #     for item in drive_week.iterdir():
# # # # # # # #         temp_dir = drive_week / f"_tmp_{item.stem}"

# # # # # # # #         extracted = unzip_if_needed(item, temp_dir)
# # # # # # # #         extracted_items = list(extracted.iterdir())

# # # # # # # #         for top in extracted_items:

# # # # # # # #             # CASE 1: sign → videos
# # # # # # # #             if top.is_dir() and is_sign_folder(top):
# # # # # # # #                 sign = top.name
# # # # # # # #                 sign_target = mp_week / sign
# # # # # # # #                 ensure_dir(sign_target)

# # # # # # # #                 videos = [v for v in top.iterdir() if v.is_dir()]
# # # # # # # #                 for v in videos:
# # # # # # # #                     move_video_safely(v, sign_target)

# # # # # # # #                 print(f"✅ Sign merged: {sign} ({len(videos)} videos)")

# # # # # # # #             # CASE 2: user → signs → videos
# # # # # # # #             elif top.is_dir():
# # # # # # # #                 user_folder = top

# # # # # # # #                 for sign_folder in user_folder.iterdir():
# # # # # # # #                     if not sign_folder.is_dir():
# # # # # # # #                         continue

# # # # # # # #                     sign = sign_folder.name
# # # # # # # #                     sign_target = mp_week / sign
# # # # # # # #                     ensure_dir(sign_target)

# # # # # # # #                     videos = [v for v in sign_folder.iterdir() if v.is_dir()]
# # # # # # # #                     for v in videos:
# # # # # # # #                         move_video_safely(v, sign_target)

# # # # # # # #                     print(f"👤 User data merged: {sign} ({len(videos)} videos)")

# # # # # # # #         if temp_dir.exists():
# # # # # # # #             shutil.rmtree(temp_dir)

# # # # # # # #     print(f"\n🎉 Normalization complete for {active_week}")

# # # # # # # # if __name__ == "__main__":
# # # # # # # #     normalize_week('Week_4_Grammar',drive_data_root="drive_data", mp_data_root="MP_Data")

# # # # # # # # SECOND ATTEMPT- MANUALLY DOWNLOAD DATA, THIS SCRPIT NORMALISES DATA IN TO MP_DATA FOLDER
# # # # # # # import os
# # # # # # # import shutil
# # # # # # # import zipfile

# # # # # # # # =========================
# # # # # # # # CONFIG
# # # # # # # # =========================

# # # # # # # DRIVE_DATA_ROOT = "drive_data"
# # # # # # # MP_DATA_ROOT = "MP_data"
# # # # # # # ACTIVE_WEEK = "Week_4_Grammar"   # 🔁 change this only

# # # # # # # # =========================
# # # # # # # # HELPERS
# # # # # # # # =========================

# # # # # # # def ensure_dir(path):
# # # # # # #     os.makedirs(path, exist_ok=True)

# # # # # # # def unzip_all(folder):
# # # # # # #     for item in os.listdir(folder):
# # # # # # #         if item.endswith(".zip"):
# # # # # # #             zip_path = os.path.join(folder, item)
# # # # # # #             extract_to = zip_path.replace(".zip", "")

# # # # # # #             if not os.path.exists(extract_to):
# # # # # # #                 print(f"📦 Unzipping {item}")
# # # # # # #                 with zipfile.ZipFile(zip_path, 'r') as z:
# # # # # # #                     z.extractall(extract_to)

# # # # # # # def move_video_safely(src, dst_dir):
# # # # # # #     ensure_dir(dst_dir)

# # # # # # #     video_name = os.path.basename(src)
# # # # # # #     dst = os.path.join(dst_dir, video_name)

# # # # # # #     counter = 1
# # # # # # #     while os.path.exists(dst):
# # # # # # #         dst = os.path.join(dst_dir, f"{video_name}_{counter}")
# # # # # # #         counter += 1

# # # # # # #     shutil.move(src, dst)

# # # # # # # # =========================
# # # # # # # # CORE NORMALIZATION
# # # # # # # # =========================

# # # # # # # def normalize_week():
# # # # # # #     week_drive_path = os.path.join(DRIVE_DATA_ROOT, ACTIVE_WEEK)
# # # # # # #     week_mp_path = os.path.join(MP_DATA_ROOT, ACTIVE_WEEK)

# # # # # # #     ensure_dir(week_mp_path)

# # # # # # #     # Step 1: unzip everything
# # # # # # #     unzip_all(week_drive_path)

# # # # # # #     # Step 2: walk through week folder
# # # # # # #     for item in os.listdir(week_drive_path):
# # # # # # #         item_path = os.path.join(week_drive_path, item)

# # # # # # #         if not os.path.isdir(item_path):
# # # # # # #             continue

# # # # # # #         # CASE 1: item IS a sign folder
# # # # # # #         if is_sign_folder(item_path):
# # # # # # #             process_sign_folder(item_path, week_mp_path)

# # # # # # #         # CASE 2: item is a user folder containing sign folders
# # # # # # #         else:
# # # # # # #             for sub in os.listdir(item_path):
# # # # # # #                 sub_path = os.path.join(item_path, sub)
# # # # # # #                 if os.path.isdir(sub_path) and is_sign_folder(sub_path):
# # # # # # #                     process_sign_folder(sub_path, week_mp_path)

# # # # # # #     print("✅ Normalization complete.")

# # # # # # # # =========================
# # # # # # # # SIGN PROCESSING
# # # # # # # # =========================

# # # # # # # def is_sign_folder(path):
# # # # # # #     # Heuristic: contains video folders
# # # # # # #     for item in os.listdir(path):
# # # # # # #         if os.path.isdir(os.path.join(path, item)):
# # # # # # #             return True
# # # # # # #     return False

# # # # # # # def process_sign_folder(sign_path, week_mp_path):
# # # # # # #     sign_name = os.path.basename(sign_path)
# # # # # # #     sign_dst = os.path.join(week_mp_path, sign_name)

# # # # # # #     ensure_dir(sign_dst)

# # # # # # #     for video in os.listdir(sign_path):
# # # # # # #         video_path = os.path.join(sign_path, video)

# # # # # # #         if os.path.isdir(video_path):
# # # # # # #             move_video_safely(video_path, sign_dst)

# # # # # # # # =========================
# # # # # # # # ENTRY POINT
# # # # # # # # =========================

# # # # # # # if __name__ == "__main__":
# # # # # # #     normalize_week()


# # # # # # # another attempt gain
# # # # # # import zipfile
# # # # # # import shutil
# # # # # # from pathlib import Path

# # # # # # def normalize_dataset(source_dir, output_dir, temp_extract_dir='temp_unzipped'):
# # # # # #     source_path = Path(source_dir)
# # # # # #     output_path = Path(output_dir)
# # # # # #     temp_path = Path(temp_extract_dir)

# # # # # #     # 1. Handle Zipped User Folders
# # # # # #     for zip_file in source_path.glob('*.zip'):
# # # # # #         print(f"Extracting {zip_file.name}...")
# # # # # #         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
# # # # # #             # Extract into a subfolder named after the zip file (User Name)
# # # # # #             zip_ref.extractall(temp_path / zip_file.stem)

# # # # # #     # 2. Process all data (Original Week folders + Extracted User folders)
# # # # # #     # Search in both source and temp directories
# # # # # #     for search_root in [source_path, temp_path]:
# # # # # #         if not search_root.exists():
# # # # # #             continue

# # # # # #         for file_path in search_root.rglob('*'):
# # # # # #             # Filter for frame files (adjust extension as needed, e.g., .jpg, .png)
# # # # # #             if file_path.is_file() and file_path.suffix.lower() in ['.np']:
                
# # # # # #                 parts = file_path.parts
# # # # # #                 # Structure: ... / [Root] / [Sign] / [VideoID] / [Frame]
# # # # # #                 # parts[-4]  parts[-3]  parts[-2]     parts[-1]
                
# # # # # #                 root_folder = parts[-4] 
# # # # # #                 sign_name = parts[-3]
# # # # # #                 video_id = parts[-2]
# # # # # #                 frame_name = parts[-1]

# # # # # #                 # Assign to a week. If the folder isn't a "week", 
# # # # # #                 # we'll label it "unassigned" or a specific week of your choice.
# # # # # #                 target_week = root_folder if "week" in root_folder.lower() else "week_user_contributions"

# # # # # #                 # Unique Video ID to prevent overwriting: User_VideoID
# # # # # #                 unique_video_name = f"{root_folder}_{video_id}"

# # # # # #                 # Construct: output/week/sign/user_video/frame
# # # # # #                 final_dest = output_path / target_week / sign_name / unique_video_name
# # # # # #                 final_dest.mkdir(parents=True, exist_ok=True)

# # # # # #                 shutil.copy2(file_path, final_dest / frame_name)

# # # # # #     # # 3. Cleanup temp files if desired
# # # # # #     # # shutil.rmtree(temp_path)
# # # # # #     # print(f"Successfully normalized to: {output_path.absolute()}")

# # # # # # # Run it
# # # # # # normalize_dataset('drive_data', 'mp_data')

# # # # # import zipfile
# # # # # import shutil
# # # # # import numpy as np
# # # # # from pathlib import Path

# # # # # def normalize_dataset(source_dir, output_dir):
# # # # #     source_path = Path(source_dir)
# # # # #     output_path = Path(output_dir)
# # # # #     temp_path = Path("temp_extraction")

# # # # #     # 1. Extract ZIPs first
# # # # #     for zip_file in source_path.rglob('*.zip'):
# # # # #         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
# # # # #             # Extract to a folder named after the zip file
# # # # #             zip_ref.extractall(temp_path / zip_file.stem)

# # # # #     # 2. Process all .npy files from both source and temp
# # # # #     for search_root in [source_path, temp_path]:
# # # # #         if not search_root.exists(): continue

# # # # #         for npy_path in search_root.rglob('*.npy'):
# # # # #             # Logic to find Week, Sign, and Video name
# # # # #             # This assumes a structure like: Week/Sign/Video.npy
# # # # #             parts = npy_path.parts
# # # # #             sign_name = parts[-2] 
# # # # #             file_name = parts[-1]
            
# # # # #             # Identify the Week (defaulting to 'Week_1' if not found)
# # # # #             week_folder = next((p for p in parts if "week" in p.lower()), "week_all")

# # # # #             # Validate the 30-frame requirement
# # # # #             try:
# # # # #                 data = np.load(npy_path)
# # # # #                 if data.shape[0] != 30:
# # # # #                     print(f"Skipping {file_name}: Invalid shape {data.shape}")
# # # # #                     continue
# # # # #             except Exception as e:
# # # # #                 print(f"Could not load {file_name}: {e}")
# # # # #                 continue

# # # # #             # PREPARE DESTINATION
# # # # #             # Structure: output/week_1/hello/user_video1.npy
# # # # #             unique_filename = f"{parts[-3]}_{file_name}" # Prefixes with parent folder
# # # # #             final_dest_dir = output_path / week_folder / sign_name
            
# # # # #             # THIS CREATES THE DIRECTORY AUTOMATICALLY
# # # # #             final_dest_dir.mkdir(parents=True, exist_ok=True)

# # # # #             # COPY FILE
# # # # #             shutil.copy2(npy_path, final_dest_dir / unique_filename)

# # # # #     # Cleanup temp folder
# # # # #     if temp_path.exists():
# # # # #         shutil.rmtree(temp_path)
    
# # # # #     print("Done! Your directories are created and files are moved.")

# # # # # Run: normalize_dataset('drive_data/Week_4_Grammar', 'normalized_data')

# # # # import zipfile
# # # # import shutil
# # # # import numpy as np
# # # # from pathlib import Path

# # # # def normalize_to_sign_folders(source_dir, output_dir):
# # # #     source_path = Path(source_dir)
# # # #     output_path = Path(output_dir)
# # # #     temp_path = Path("temp_extraction")

# # # #     # 1. Extract ZIPs (Users)
# # # #     for zip_file in source_path.rglob('*.zip'):
# # # #         with zipfile.ZipFile(zip_file, 'r') as zip_ref:
# # # #             zip_ref.extractall(temp_path / zip_file.stem)

# # # #     # 2. Process everything
# # # #     for search_root in [source_path, temp_path]:
# # # #         if not search_root.exists(): continue

# # # #         for npy_path in search_root.rglob('*.npy'):
# # # #             parts = npy_path.parts
            
# # # #             # Extract names based on your structure: .../Sign/Video.npy
# # # #             # We assume the parent of the file is the Sign folder
# # # #             sign_name = npy_path.parent.name 
# # # #             file_name = npy_path.name
            
# # # #             # To keep them unique in the same folder, we use the "Grandparent" name
# # # #             # e.g., 'UserA_video1.npy' or 'Week1_video1.npy'
# # # #             folder_identifier = npy_path.parent.parent.name
# # # #             unique_name = f"{folder_identifier}_{file_name}"

# # # #             # TARGET: output / sign_name / unique_name.npy
# # # #             final_dest_dir = output_path / sign_name
            
# # # #             # This creates the Sign folder if it doesn't exist, 
# # # #             # or just moves on if it does.
# # # #             final_dest_dir.mkdir(parents=True, exist_ok=True)

# # # #             # Move or Copy
# # # #             shutil.copy2(npy_path, final_dest_dir / unique_name)

# # # #     # Cleanup
# # # #     if temp_path.exists(): shutil.rmtree(temp_path)
# # # #     print(f"Done! All videos are now inside their respective Sign folders in: {output_dir}")

# # # # normalize_to_sign_folders('drive_data/Week_4_Grammar', 'normalised_dataset')

# # # import zipfile
# # # import shutil
# # # from pathlib import Path

# # # def normalize_to_mp_data(active_week):
# # #     # Setup paths
# # #     source_root = Path('drive_data/Week_4_Grammar')
# # #     output_root = Path("MP_data")
# # #     temp_extract = Path("temp_unzip")
    
# # #     # 1. Unzip any user zip files
# # #     if source_root.exists():
# # #         for zip_item in source_root.glob("*.zip"):
# # #             user_id = zip_item.stem
# # #             with zipfile.ZipFile(zip_item, 'r') as z:
# # #                 z.extractall(temp_extract / user_id)

# # #     # 2. Define our search areas: the Week folder and the Temp Unzipped folder
# # #     search_areas = []
# # #     if source_root.exists(): search_areas.append(source_root)
# # #     if temp_extract.exists(): search_areas.append(temp_extract)

# # #     for root in search_areas:
# # #         # Loop through each 'User' or 'Week' folder
# # #         for source_folder in root.iterdir():
# # #             if not source_folder.is_dir(): continue
            
# # #             # source_folder is now 'UserA' or the week subfolder
# # #             user_label = source_folder.name 

# # #             # Loop through each 'Sign' folder (e.g., 'hello')
# # #             for sign_folder in source_folder.iterdir():
# # #                 if not sign_folder.is_dir(): continue
                
# # #                 sign_name = sign_folder.name
                
# # #                 # Create the Sign folder in MP_data
# # #                 target_sign_path = output_root / sign_name
# # #                 target_sign_path.mkdir(parents=True, exist_ok=True)

# # #                 # Loop through each 'Video' folder inside the Sign
# # #                 for video_folder in sign_folder.iterdir():
# # #                     if not video_folder.is_dir(): continue
                    
# # #                     # New name: UserA_video_1 (to keep it unique)
# # #                     new_video_name = f"{user_label}_{video_folder.name}"
# # #                     dest_path = target_sign_path / new_video_name

# # #                     # MOVE the whole video folder (including all its .npy frames)
# # #                     if not dest_path.exists():
# # #                         shutil.copytree(video_folder, dest_path)
# # #                     else:
# # #                         print(f"Skipping {new_video_name}, already exists in {sign_name}")

# # #     # Cleanup
# # #     if temp_extract.exists():
# # #         shutil.rmtree(temp_extract)
        
# # #     print(f"Done! All data is now in: {output_root.absolute()}")

# # # # Run it

# # # normalize_to_mp_data("week_1")

# # import zipfile
# # import shutil
# # import os
# # from pathlib import Path

# # def normalize_to_mp_data(active_week):
# #     # 1. Setup paths
# #     source_root = Path(active_week) / "mixed_data"
# #     output_root = Path("MP_data")
# #     temp_extract = Path("temp_unzip")
    
# #     # Ensure MP_data exists
# #     output_root.mkdir(parents=True, exist_ok=True)
    
# #     # 2. Extract User Zips
# #     if source_root.exists():
# #         for zip_item in source_root.glob("*.zip"):
# #             # Extract to a temp folder named after the user
# #             with zipfile.ZipFile(zip_item, 'r') as z:
# #                 z.extractall(temp_extract / zip_item.stem)

# #     # 3. Identify all folders that contain 'Signs' 
# #     # (The week subfolders and the unzipped user folders)
# #     search_paths = []
# #     if source_root.exists():
# #         search_paths.extend([f for f in source_root.iterdir() if f.is_dir()])
# #     if temp_extract.exists():
# #         search_paths.extend([f for f in temp_extract.iterdir() if f.is_dir()])

# #     # 4. The Loop: Focus on the Sign Name
# #     for user_folder in search_paths:
# #         user_name = user_folder.name 

# #         for sign_folder in user_folder.iterdir():
# #             if not sign_folder.is_dir(): continue
            
# #             # The name of the sign (e.g., 'hello')
# #             sign_name = sign_folder.name 
            
# #             # This points to: MP_data/hello/
# #             target_sign_dir = output_root / sign_name
# #             target_sign_dir.mkdir(parents=True, exist_ok=True)

# #             # Move every Video folder inside this user's sign folder
# #             for video_folder in sign_folder.iterdir():
# #                 if not video_folder.is_dir(): continue
                
# #                 # To make sure we don't overwrite "video1" from UserA with "video1" from UserB,
# #                 # we only rename the VIDEO folder itself, not the sign folder.
# #                 video_dest_name = f"{video_folder.name}"
# #                 video_dest_path = target_sign_dir / video_dest_name

# #                 # Copy the whole video folder (all 30 .npy files) into the Sign folder
# #                 if not video_dest_path.exists():
# #                     shutil.copytree(video_folder, video_dest_path)

# #     # 5. Cleanup
# #     if temp_extract.exists():
# #         shutil.rmtree(temp_extract)
        
# #     print(f"Done! All users' videos are now inside their respective Sign folders in {output_root.absolute()}")

# # # Run it
# # # normalize_to_mp_data("drive_data/Week_4_Grammar")

# import zipfile
# import shutil
# from pathlib import Path

# def normalize_to_mp_data(active_week):
#     source_root = Path(active_week)
#     output_root = Path("MP_data")
#     temp_extract = Path("temp_unzip")

#     output_root.mkdir(parents=True, exist_ok=True)

#     # 1. Extract all user zips
#     if source_root.exists():
#         for zip_item in source_root.glob("*.zip"):
#             with zipfile.ZipFile(zip_item, "r") as z:
#                 z.extractall(temp_extract / zip_item.stem)

#     # 2. Collect possible user roots
#     search_paths = []
#     if source_root.exists():
#         search_paths.extend([p for p in source_root.iterdir() if p.is_dir()])
#     if temp_extract.exists():
#         search_paths.extend([p for p in temp_extract.iterdir() if p.is_dir()])

#     # 3. Process each user
#     for user_root in search_paths:
#         user_name = user_root.name

#         # 🔧 FIX: handle user/user/sign structure
#         children = list(user_root.iterdir())
#         if len(children) == 1 and children[0].is_dir() and children[0].name.lower() == "user":
#             user_root = children[0]

#         # 4. Each folder here MUST be a sign
#         for sign_folder in user_root.iterdir():
#             if not sign_folder.is_dir():
#                 continue

#             # A valid sign folder must contain video folders
#             video_folders = [v for v in sign_folder.iterdir() if v.is_dir()]
#             if not video_folders:
#                 continue  # 🚫 skip junk folders

#             sign_name = sign_folder.name
#             target_sign_dir = output_root / sign_name
#             target_sign_dir.mkdir(parents=True, exist_ok=True)

#             # 5. Copy videos
#             for video_folder in video_folders:
#                 video_dest = target_sign_dir / f"{user_name}_{video_folder.name}"
#                 if not video_dest.exists():
#                     shutil.copytree(video_folder, video_dest)

#     # 6. Cleanup
#     if temp_extract.exists():
#         shutil.rmtree(temp_extract)

#     print(f"✅ Done! MP_data normalized correctly at {output_root.resolve()}") 

# normalize_to_mp_data('drive_data/Week_4_Grammar')

import zipfile
import shutil
from pathlib import Path

def normalize_to_mp_data(active_week):
    source_root = Path(active_week) 
    output_root = Path("MP_data")
    temp_extract = Path("temp_unzip")

    output_root.mkdir(parents=True, exist_ok=True)

    # 1️⃣ Extract all zip files
    if source_root.exists():
        for zip_file in source_root.glob("*.zip"):
            with zipfile.ZipFile(zip_file, 'r') as z:
                z.extractall(temp_extract / zip_file.stem)

    # 2️⃣ Collect ALL possible roots (week folders + extracted zips)
    search_roots = []

    if source_root.exists():
        search_roots.extend([p for p in source_root.iterdir() if p.is_dir()])

    if temp_extract.exists():
        search_roots.extend([p for p in temp_extract.iterdir() if p.is_dir()])

    # 3️⃣ Traverse deeply and find actual SIGN folders
    for root in search_roots:

        # walk through everything under this root
        for sign_folder in root.rglob("*"):

            # A sign folder is one that contains video folders
            if not sign_folder.is_dir():
                continue

            video_folders = [v for v in sign_folder.iterdir() if v.is_dir()]
            if not video_folders:
                continue

            # If the subfolders contain .npy files → this is a video folder
            if not any(list(v.glob("*.npy")) for v in video_folders):
                continue

            sign_name = sign_folder.name
            target_sign_dir = output_root / sign_name
            target_sign_dir.mkdir(parents=True, exist_ok=True)

            # 4️⃣ Copy videos directly into MP_data/sign/
            for video_folder in video_folders:
                destination = target_sign_dir / video_folder.name

                # avoid overwriting duplicates
                counter = 1
                while destination.exists():
                    destination = target_sign_dir / f"{video_folder.name}_{counter}"
                    counter += 1

                shutil.copytree(video_folder, destination)

    # 5️⃣ Cleanup
    if temp_extract.exists():
        shutil.rmtree(temp_extract)

    print("✅ Done. Structure is now:")
    print("MP_data > sign > video folders (ALL users merged)")

normalize_to_mp_data('drive_data/Week_4_Grammar')