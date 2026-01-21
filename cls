[33mcommit 9d62b310d8d28f5c6cffd4fb874a9c33a10a224c[m[33m ([m[1;36mHEAD -> [m[1;32mmain[m[33m, [m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m)[m
Author: Chantel Muthaphuli <chantelmuthaphuli@gmail.com>
Date:   Sun Jan 18 18:23:40 2026 +0200

    feat: automated upload to drive & updates gitignore & refactore datacollection

[1mdiff --git a/model_P_Line/data_collection.py b/model_P_Line/data_collection.py[m
[1mindex 2e815fd..a09e0a4 100644[m
[1m--- a/model_P_Line/data_collection.py[m
[1m+++ b/model_P_Line/data_collection.py[m
[36m@@ -18,12 +18,14 @@[m [mimport sys[m
 import time[m
 import shutil[m
 import zipfile[m
[32m+[m[32mfrom googleapiclient.errors import HttpError[m
 [m
 # --------------------------------------------------------------------------[m
 # IMPORT CONFIGURATION (Connects to config.py)[m
 # --------------------------------------------------------------------------[m
 # We import variables directly so you don't have to edit this file ever again.[m
 from config import ACTIONS, DATA_PATH, no_sequences, sequence_length, VOCAB_SCHEDULE, ACTIVE_WEEK, get_demo_video_path[m
[32m+[m[32mfrom upload_data import get_drive_service, create_or_get_contributor_folder, upload_zip_folder, zip_mp_data[m
 [m
 # --------------------------------------------------------------------------[m
 # MEDIAPIPE SETUP[m
[36m@@ -161,33 +163,6 @@[m [mdef is_week_complete(mp_data_path, vocab, active_week):[m
     return True if len(recorded) >= len(vocab[active_week]) else False[m
     [m
     [m
[31m-def zip_mp_data(source_dir, active_week, email):[m
[31m-    """[m
[31m-    Zip the MP_Data directory for easier upload.[m
[31m-    Folder zipped only when all signs for the active week are collected.[m
[31m-    [m
[31m-    args:[m
[31m-        source_dir: Path to the MP_Data directory[m
[31m-        output_file: Path for the output zip file[m
[31m-    """[m
[31m-[m
[31m-    base_dir = os.path.dirname(source_dir)[m
[31m-[m
[31m-    contributor_folder = os.path.join(base_dir, email)[m
[31m-    os.makedirs(contributor_folder, exist_ok=True)[m
[31m-[m
[31m-    # puts the zipped folder inside the contributor folder[m
[31m-    output_path = os.path.join(contributor_folder, f"{active_week}.zip")[m
[31m-[m
[31m-    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:[m
[31m-        for root, dirc, files in os.walk(source_dir):[m
[31m-            for file in files:[m
[31m-                file_path = os.path.join(root, file)[m
[31m-                arcname = os.path.relpath(file_path, source_dir)[m
[31m-                zipf.write(file_path, arcname)[m
[31m-    print(f"Data zipped successfully in {output_path}!")[m
[31m-    return output_path[m
[31m-[m
 [m
 # --------------------------------------------------------------------------[m
 # MAIN LOGIC[m
[36m@@ -493,9 +468,34 @@[m [mdef main():[m
     # If complete, zip the folder for easier upload[m
     if is_week_complete(mp_data_path, VOCAB_SCHEDULE, ACTIVE_WEEK):[m
         print(f"\n🎉 All signs for Week {ACTIVE_WEEK} have been collected!")[m
[31m-        zip_file_path = os.path.join(os.path.dirname(DATA_PATH), f"{ACTIVE_WEEK}.zip")[m
[31m-        zip_mp_data(mp_data_path, ACTIVE_WEEK, user_name)[m
[31m-        print(f"Please upload the zip file '{zip_file_path}' to Google Drive.")[m
[32m+[m[32m        try :[m
[32m+[m[32m            # build google drive service[m
[32m+[m[32m            service =get_drive_service()[m
[32m+[m[32m            # !!!! PLEASE MOVE ID TO DOTENV AFTER CRATING KEY!!!![m
[32m+[m[32m            parent_folder_id = '1xOUyOz1fiRocPXLqkjHCBaXtEreVTGt3'[m[41m [m
[32m+[m
[32m+[m[32m            # create or use existing contributor folder[m
[32m+[m[32m            contributor_folder_id = create_or_get_contributor_folder(service, parent_folder_id, user_name)[m
[32m+[m
[32m+[m[32m            # zip the mp_data folder[m
[32m+[m[32m            zip_file_path = os.path.join(os.path.dirname(mp_data_path), f"{ACTIVE_WEEK}.zip")[m
[32m+[m[32m            zip_mp_data(mp_data_path, zip_file_path)[m
[32m+[m
[32m+[m[32m            # upload the zip file to google drive[m
[32m+[m[32m            upload_zip_folder(service, zip_file_path, contributor_folder_id)[m
[32m+[m
[32m+[m[32m            print(f"Please upload the zip file '{zip_file_path}' to Google Drive.")[m
[32m+[m[32m        except FileNotFoundError as e:[m
[32m+[m[32m            print(f"Missing file: {e}")[m
[32m+[m[32m        except RuntimeError as e:[m
[32m+[m[32m            print(f"Authentication error: {e}")[m
[32m+[m[32m        except HttpError as e:[m
[32m+[m[32m            print(f"Google drive Api error. Please upload week.zip manually!")[m
[32m+[m[32m        except Exception as e:[m
[32m+[m[32m            print(f"An unexpected error occurred: {e}")[m
[32m+[m[32m    else:[m
[32m+[m[32m        print(f"\n⚠️  Not all signs for Week {ACTIVE_WEEK} have been collected yet.")[m
[32m+[m[32m        print("   Please complete all signs before uploading.")[m
 [m
 if __name__ == '__main__':[m
     main()[m
\ No newline at end of file[m
[1mdiff --git a/model_P_Line/requirements.txt b/model_P_Line/requirements.txt[m
[1mindex 1095e37..0d0ff93 100644[m
[1m--- a/model_P_Line/requirements.txt[m
[1m+++ b/model_P_Line/requirements.txt[m
[36m@@ -1,6 +1,10 @@[m
[31m-opencv-python: >=4.8, <5.0[m
[31m-numpy: >=1.23, <2.0[m
[31m-mediapipe: ==0.10.14[m
[31m-tensorflow: >=2.15, <2.18[m
[31m-scikit-learn: >=1.3, <1.6[m
[31m-matplotlib: >=3.7, <3.9[m
\ No newline at end of file[m
[32m+[m[32mopencv-python >=4.8[m
[32m+[m[32mnumpy >=1.23[m
[32m+[m[32mmediapipe ==0.10.14[m
[32m+[m[32mtensorflow >=2.15[m
[32m+[m[32mscikit-learn >=1.3[m
[32m+[m[32mmatplotlib >=3.7[m
[32m+[m[32mgoogle-api-python-client >=2.70[m
[32m+[m[32mgoogle-auth-httplib2 >=0.1.0[m
[32m+[m[32mgoogle-auth-oauthlib >=1.0.0[m
[41m+[m
[1mdiff --git a/model_P_Line/upload_data.py b/model_P_Line/upload_data.py[m
[1mindex 5392bbc..3bf0f36 100644[m
Binary files a/model_P_Line/upload_data.py and b/model_P_Line/upload_data.py differ
