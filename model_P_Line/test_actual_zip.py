"""
Test what actually gets zipped when upload_data runs
"""
import os
import zipfile
from collections import defaultdict

def test_actual_zip():
    """Test the actual zip creation that upload_data.py would do"""
    
    source_dir = 'MP_Data'
    output_file = 'test_actual_upload.zip'
    contributor_email = 'test_user@test.com'
    
    print(f"Testing zip creation for: {source_dir}\n")
    
    # First, check what's in MP_Data
    print("="*60)
    print("Checking MP_Data contents:")
    print("="*60)
    
    for root, dirs, files in os.walk(source_dir):
        level = root.replace(source_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        folder_name = os.path.basename(root)
        if level == 0:
            folder_name = source_dir
        print(f'{indent}{folder_name}/')
        
        # Show first few subdirs
        subindent = ' ' * 2 * (level + 1)
        if level == 0:
            for d in sorted(dirs)[:10]:
                print(f'{subindent}{d}/')
            if len(dirs) > 10:
                print(f'{subindent}... and {len(dirs)-10} more folders')
        
        if level == 1:
            file_count = sum([len(files) for r, d, f in os.walk(root)])
            print(f'{subindent}({file_count} total files in subdirectories)')
            break  # Don't show deeper levels
    
    print("\n" + "="*60)
    print("Creating ZIP file...")
    print("="*60)
    
    file_count = 0
    total_size = 0
    sign_counts = defaultdict(int)
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                
                # Track which sign this belongs to
                parts = arcname.split(os.sep)
                if len(parts) > 0:
                    sign = parts[0]
                    sign_counts[sign] += 1
                
                # Add contributor folder
                arcname = os.path.join(contributor_email, arcname)
                
                zipf.write(file_path, arcname)
                file_count += 1
                total_size += os.path.getsize(file_path)
                
                if file_count % 500 == 0:
                    print(f"  Zipped {file_count} files...")
    
    zip_size = os.path.getsize(output_file)
    
    print(f"\n✓ Zipping complete!")
    print(f"\nResults:")
    print("="*60)
    print(f"Total files zipped: {file_count}")
    print(f"Total size (uncompressed): {total_size / (1024*1024):.2f} MB")
    print(f"Zip file size: {zip_size / (1024*1024):.2f} MB")
    print(f"Compression ratio: {total_size / zip_size:.2f}x")
    
    print(f"\nFiles per sign:")
    print("-"*60)
    for sign in sorted(sign_counts.keys()):
        print(f"  {sign:15s} : {sign_counts[sign]:4d} files")
    
    print("\n" + "="*60)
    print("Verifying ZIP contents:")
    print("="*60)
    
    with zipfile.ZipFile(output_file, 'r') as zipf:
        all_files = zipf.namelist()
        print(f"Files in ZIP: {len(all_files)}")
        
        # Verify structure
        zip_sign_counts = defaultdict(int)
        for f in all_files:
            parts = f.split('/')
            if len(parts) >= 2:
                sign = parts[1]  # contributor/sign/...
                zip_sign_counts[sign] += 1
        
        print(f"\nZIP structure check:")
        for sign in sorted(zip_sign_counts.keys()):
            print(f"  {sign:15s} : {zip_sign_counts[sign]:4d} files")
        
        if len(all_files) == file_count:
            print(f"\n✓ All {file_count} files confirmed in ZIP!")
        else:
            print(f"\n✗ MISMATCH: Zipped {file_count} but ZIP contains {len(all_files)}")
    
    # Cleanup
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"\nCleaned up {output_file}")

if __name__ == "__main__":
    test_actual_zip()
