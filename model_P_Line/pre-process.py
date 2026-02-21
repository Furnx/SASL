# # # # # # # # import io
# # # # # # # # import zipfile
# # # # # # # # import os
# # # # # # # # from googleapiclient.http import MediaIoBaseDownload
# # # # # # # # from config import ACTIVE_WEEK, PROJECT_ROOT_ID
# # # # # # # from upload_data import get_drive_service

"""
- This file is to be used before training, running train/_transformer.py and predict/_transformer.py
- THis file downloads data from the drive, saves data locally, unzips and standarises the data for training
- Creates a folder for the week in the local directory, and saves all data in that folder.
"""

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