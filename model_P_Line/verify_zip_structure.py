"""
Verify that zip includes ALL signs and their structure
"""
import os
import zipfile
from collections import defaultdict

def analyze_zip_structure(zip_path):
    """Analyze the structure of a zip file"""
    print(f"Analyzing: {zip_path}\n")
    
    if not os.path.exists(zip_path):
        print(f"ERROR: {zip_path} does not exist!")
        return
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        all_files = zipf.namelist()
        
        # Count by sign
        sign_counts = defaultdict(int)
        
        for file in all_files:
            parts = file.split('/')
            if len(parts) >= 2:
                # Structure: contributor_email/sign/...
                sign = parts[1]
                sign_counts[sign] += 1
        
        # Display results
        print(f"Total files in zip: {len(all_files)}")
        print(f"\nFiles per sign:")
        print("-" * 40)
        
        for sign in sorted(sign_counts.keys()):
            print(f"  {sign:15s} : {sign_counts[sign]:4d} files")
        
        print("\n" + "=" * 40)
        print(f"Total signs found: {len(sign_counts)}")
        print(f"Expected signs: 4 (what, where, who, why)")
        
        if len(sign_counts) == 4:
            print("✓ All signs are present!")
        else:
            print("✗ MISSING SIGNS!")
            expected = {'what', 'where', 'who', 'why'}
            found = set(sign_counts.keys())
            missing = expected - found
            if missing:
                print(f"  Missing: {missing}")
        
        # Show sample files
        print("\nSample files (first 5):")
        for i, file in enumerate(all_files[:5]):
            info = zipf.getinfo(file)
            print(f"  {file} ({info.file_size} bytes)")

# Test with the actual zip that would be created
source_dir = 'MP_Data'
test_zip = 'test_full_structure.zip'
contributor = 'test_user@email.com'

print("Creating test zip...")
with zipfile.ZipFile(test_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, source_dir)
            arcname = os.path.join(contributor, arcname)
            zipf.write(file_path, arcname)

print("✓ Zip created\n")

analyze_zip_structure(test_zip)

# Cleanup
if os.path.exists(test_zip):
    os.remove(test_zip)
    print(f"\nCleaned up {test_zip}")
