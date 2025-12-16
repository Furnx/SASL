"""
Setup Verification Script
Run this file to check if your laptop is ready for the project.
"""
import os
import sys
import shutil

print("="*50)
print(" 🛠️  SASL PROJECT DIAGNOSTIC TOOL")
print("="*50)

# 1. CHECK PYTHON VERSION
print(f"\n[1/4] Checking Python... ", end="")
if sys.version_info < (3, 7):
    print("❌ FAIL")
    print("   -> You need Python 3.7 or higher.")
else:
    print(f"✅ PASS (v{sys.version_info.major}.{sys.version_info.minor})")

# 2. CHECK LIBRARIES
print("\n[2/4] Checking Libraries...")
missing_libs = []

try:
    import cv2
    print("   - OpenCV:      ✅")
except ImportError:
    print("   - OpenCV:      ❌ (pip install opencv-python)")
    missing_libs.append("opencv-python")

try:
    import numpy
    print("   - Numpy:       ✅")
except ImportError:
    print("   - Numpy:       ❌ (pip install numpy)")
    missing_libs.append("numpy")

try:
    import mediapipe
    print("   - MediaPipe:   ✅")
except ImportError:
    print("   - MediaPipe:   ❌ (pip install mediapipe)")
    missing_libs.append("mediapipe")

# 3. CHECK PERMISSIONS & FOLDERS
print("\n[3/4] Checking File Permissions... ", end="")
try:
    test_dir = "TEST_FOLDER_DELETE_ME"
    os.makedirs(test_dir, exist_ok=True)
    with open(os.path.join(test_dir, "test.txt"), "w") as f:
        f.write("test")
    shutil.rmtree(test_dir)
    print("✅ PASS")
except Exception as e:
    print(f"❌ FAIL ({e})")
    print("   -> Try running as Administrator.")

# 4. CHECK CAMERA
print("\n[4/4] Checking Camera... ", end="")
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print("✅ PASS")
    else:
        print("⚠️  WARNING (Camera opened but returned no image)")
    cap.release()
else:
    print("❌ FAIL")
    print("   -> Is Zoom/Teams using your camera?")
    print("   -> Check your privacy settings.")

# SUMMARY
print("\n" + "="*50)
if not missing_libs:
    print("🎉 YOU ARE READY TO START!")
    print("   Run: python data_collection_v2.py")
else:
    print("🚫 SETUP FAILED.")
    print("   Run this command to fix:")
    print(f"   pip install {' '.join(missing_libs)}")
print("="*50)