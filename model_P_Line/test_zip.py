"""
Test script to verify zip creation and contents
"""
import os
import zipfile

def count_files_in_directory(directory):
    """Count all files in directory recursively"""
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

def count_files_in_zip(zip_path):
    """Count all files in a zip archive"""
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        return len(zipf.namelist())

def test_zip_creation():
    source_dir = 'MP_Data'
    test_zip = 'test_mp_data.zip'
    
    # Count original files
    original_count = count_files_in_directory(source_dir)
    print(f"Files in {source_dir}: {original_count}")
    
    # Create zip
    print(f"\nCreating zip file: {test_zip}")
    with zipfile.ZipFile(test_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                arcname = os.path.join('test_folder', arcname)
                zipf.write(file_path, arcname)
                
    # Count files in zip
    zip_count = count_files_in_zip(test_zip)
    print(f"Files in {test_zip}: {zip_count}")
    
    # Compare
    if original_count == zip_count:
        print(f"\n✓ SUCCESS: All {original_count} files were zipped correctly!")
    else:
        print(f"\n✗ PROBLEM: Only {zip_count} of {original_count} files were zipped!")
        print(f"Missing: {original_count - zip_count} files")
    
    # Show some contents
    print("\nFirst 10 files in zip:")
    with zipfile.ZipFile(test_zip, 'r') as zipf:
        for i, name in enumerate(zipf.namelist()[:10]):
            info = zipf.getinfo(name)
            print(f"  {name} ({info.file_size} bytes)")
    
    # Cleanup
    if os.path.exists(test_zip):
        os.remove(test_zip)
        print(f"\nCleaned up {test_zip}")

if __name__ == "__main__":
    test_zip_creation()
