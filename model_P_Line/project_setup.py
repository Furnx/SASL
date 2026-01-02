"""
SASL Project - Automated Setup Script
======================================
This script will automatically:
1. Detect your operating system (Windows/Mac/Linux)
2. Check Python version
3. Create virtual environment
4. Activate virtual environment
5. Install all required packages
6. Verify installation
7. Test configuration alignment
8. Check camera and permissions

Just run: python project_setup.py

Author: WeThinkCode_Cohort_2025_SASL Team
"""

import os
import sys
import subprocess
import platform
import shutil

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def run_command(command, shell=True, check=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def detect_os():
    """Detect the operating system"""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "mac"
    elif system == "Linux":
        return "linux"
    else:
        return "unknown"

def check_python_version():
    """Check if Python version is 3.7 or higher"""
    print_header("STEP 1: Checking Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print_info(f"Python version: {version_str}")
    print_info(f"Python executable: {sys.executable}")
    
    if version < (3, 7):
        print_error(f"Python 3.7 or higher is required. You have {version_str}")
        return False
    
    print_success(f"Python version {version_str} is compatible!")
    return True

def create_virtual_environment(os_type):
    """Create a virtual environment"""
    print_header("STEP 2: Checking Virtual Environment")

    venv_name = "venv"

    # Check if venv already exists
    if os.path.exists(venv_name):
        print_success(f"Virtual environment '{venv_name}' already exists - using it!")
        return True, venv_name

    print_info(f"Creating virtual environment '{venv_name}'...")

    # Create virtual environment
    success, stdout, stderr = run_command(f"{sys.executable} -m venv {venv_name}")

    if success:
        print_success(f"Virtual environment '{venv_name}' created successfully!")
        return True, venv_name
    else:
        print_error(f"Failed to create virtual environment: {stderr}")
        return False, None

def get_activation_command(os_type, venv_name):
    """Get the command to activate virtual environment based on OS"""
    if os_type == "windows":
        return f"{venv_name}\\Scripts\\activate"
    else:  # mac or linux
        return f"source {venv_name}/bin/activate"

def get_pip_command(os_type, venv_name):
    """Get the pip command for the virtual environment"""
    if os_type == "windows":
        return f"{venv_name}\\Scripts\\pip"
    else:  # mac or linux
        return f"{venv_name}/bin/pip"

def get_python_command(os_type, venv_name):
    """Get the python command for the virtual environment"""
    if os_type == "windows":
        return f"{venv_name}\\Scripts\\python"
    else:  # mac or linux
        return f"{venv_name}/bin/python"

def install_requirements(os_type, venv_name):
    """Install required packages from requirements.txt"""
    print_header("STEP 3: Installing/Verifying Required Packages")

    requirements_file = "requirements.txt"

    if not os.path.exists(requirements_file):
        print_error(f"Requirements file '{requirements_file}' not found!")
        return False

    print_info(f"Reading requirements from '{requirements_file}'...")

    # Get pip command for the virtual environment
    pip_cmd = get_pip_command(os_type, venv_name)

    # Get absolute path to pip
    pip_cmd = os.path.abspath(pip_cmd)

    # Upgrade pip first
    print_info("Upgrading pip...")
    try:
        result = subprocess.run(
            [pip_cmd, "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print_success("Pip upgraded successfully!")
        else:
            print_warning("Failed to upgrade pip, but continuing...")
    except Exception as e:
        print_warning(f"Failed to upgrade pip: {e}, but continuing...")

    # Read requirements file and parse it
    with open(requirements_file, 'r') as f:
        requirements = f.readlines()

    # Parse requirements (handle both "package==version" and "package: >=version, <version" formats)
    packages_to_install = []
    for req in requirements:
        req = req.strip()
        if req and not req.startswith('#'):
            # Convert "package: >=version, <version" to "package>=version,<version"
            if ':' in req:
                package, version = req.split(':', 1)
                package = package.strip()
                version = version.strip().replace(' ', '')
                packages_to_install.append(f"{package}{version}")
            else:
                packages_to_install.append(req)

    print_info(f"Installing/verifying {len(packages_to_install)} packages...")
    print_info("This may take several minutes, please be patient...")

    # Install all packages at once (faster and handles dependencies better)
    try:
        print_info("Installing all packages...")
        result = subprocess.run(
            [pip_cmd, "install"] + packages_to_install,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for all packages
        )

        if result.returncode == 0:
            print_success("All packages installed/verified successfully!")
            return True
        else:
            # If batch install failed, try one by one
            print_warning("Batch install had issues, trying packages individually...")

            failed_packages = []
            for i, package in enumerate(packages_to_install, 1):
                print_info(f"[{i}/{len(packages_to_install)}] Installing {package}...")

                try:
                    result = subprocess.run(
                        [pip_cmd, "install", package],
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minutes timeout per package
                    )

                    if result.returncode == 0:
                        print_success(f"Installed {package}")
                    else:
                        # Check if it's already installed
                        check_result = subprocess.run(
                            [pip_cmd, "show", package.split('>')[0].split('=')[0].split('<')[0]],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )

                        if check_result.returncode == 0:
                            print_success(f"{package} already installed")
                        else:
                            print_error(f"Failed to install {package}")
                            if result.stderr:
                                print_error(f"Error: {result.stderr[:200]}")
                            failed_packages.append(package)
                except subprocess.TimeoutExpired:
                    print_error(f"Timeout installing {package}")
                    failed_packages.append(package)
                except Exception as e:
                    print_error(f"Error installing {package}: {e}")
                    failed_packages.append(package)

            if failed_packages:
                print_error(f"Failed to install {len(failed_packages)} packages:")
                for pkg in failed_packages:
                    print(f"   - {pkg}")
                print_warning("Continuing anyway - verification step will check if packages work...")
                # Don't return False here - let verification step determine if it's OK
                return True

            print_success("All packages installed successfully!")
            return True

    except subprocess.TimeoutExpired:
        print_error("Installation timeout - this might be due to slow internet")
        print_warning("Continuing anyway - verification step will check if packages work...")
        return True
    except Exception as e:
        print_error(f"Installation error: {e}")
        print_warning("Continuing anyway - verification step will check if packages work...")
        return True

def verify_installation(os_type, venv_name):
    """Verify that all required packages are installed"""
    print_header("STEP 4: Verifying Installation")

    python_cmd = get_python_command(os_type, venv_name)
    python_cmd = os.path.abspath(python_cmd)

    # Test imports - avoid Unicode characters for Windows compatibility
    test_script = """import sys
missing = []

try:
    import cv2
    print("   [OK] OpenCV")
except ImportError:
    print("   [FAIL] OpenCV")
    missing.append("opencv-python")

try:
    import numpy
    print("   [OK] NumPy")
except ImportError:
    print("   [FAIL] NumPy")
    missing.append("numpy")

try:
    import mediapipe
    print("   [OK] MediaPipe")
except ImportError:
    print("   [FAIL] MediaPipe")
    missing.append("mediapipe")

try:
    import tensorflow
    print("   [OK] TensorFlow")
except ImportError:
    print("   [FAIL] TensorFlow")
    missing.append("tensorflow")

try:
    import sklearn
    print("   [OK] Scikit-learn")
except ImportError:
    print("   [FAIL] Scikit-learn")
    missing.append("scikit-learn")

try:
    import matplotlib
    print("   [OK] Matplotlib")
except ImportError:
    print("   [FAIL] Matplotlib")
    missing.append("matplotlib")

if missing:
    print(f"Missing packages: {', '.join(missing)}")
    sys.exit(1)
else:
    print("[OK] All packages verified!")
    sys.exit(0)
"""

    try:
        result = subprocess.run(
            [python_cmd, "-c", test_script],
            capture_output=True,
            text=True,
            timeout=120,  # Increased timeout for TensorFlow import
            encoding='utf-8',
            errors='replace'
        )
        print(result.stdout)

        if result.returncode != 0:
            print_error("Package verification failed!")
            if result.stderr:
                print_error(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print_warning("Verification timed out (TensorFlow can be slow to import)")
        print_info("Trying quick package check instead...")

        # Try a simpler check using pip list
        pip_cmd = get_pip_command(os_type, venv_name)
        pip_cmd = os.path.abspath(pip_cmd)

        try:
            result = subprocess.run(
                [pip_cmd, "list"],
                capture_output=True,
                text=True,
                timeout=30
            )

            installed = result.stdout.lower()
            packages = {
                "opencv-python": "opencv" in installed,
                "numpy": "numpy" in installed,
                "mediapipe": "mediapipe" in installed,
                "tensorflow": "tensorflow" in installed,
                "scikit-learn": "scikit-learn" in installed,
                "matplotlib": "matplotlib" in installed
            }

            all_installed = all(packages.values())

            for pkg, is_installed in packages.items():
                if is_installed:
                    print_success(f"{pkg} is installed")
                else:
                    print_error(f"{pkg} is NOT installed")

            if not all_installed:
                return False

            print_success("All packages appear to be installed!")
            return True

        except Exception as e2:
            print_error(f"Package check failed: {e2}")
            return False

    except Exception as e:
        print_error(f"Verification failed: {e}")
        return False

    print_success("All required packages are installed and working!")
    return True

def check_permissions():
    """Check file permissions"""
    print_header("STEP 5: Checking File Permissions")

    try:
        test_dir = "TEST_FOLDER_DELETE_ME"
        os.makedirs(test_dir, exist_ok=True)
        with open(os.path.join(test_dir, "test.txt"), "w") as f:
            f.write("test")
        shutil.rmtree(test_dir)
        print_success("File permissions OK!")
        return True
    except Exception as e:
        print_error(f"Permission error: {e}")
        print_warning("Try running as Administrator (Windows) or with sudo (Mac/Linux)")
        return False

def check_camera(os_type, venv_name):
    """Check if camera is accessible"""
    print_header("STEP 6: Checking Camera Access")

    python_cmd = get_python_command(os_type, venv_name)
    python_cmd = os.path.abspath(python_cmd)

    camera_test = """import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    cap.release()
    if ret:
        print("[OK] Camera is working!")
        exit(0)
    else:
        print("[WARNING] Camera opened but returned no image")
        exit(1)
else:
    print("[FAIL] Cannot access camera")
    print("   - Is Zoom/Teams using your camera?")
    print("   - Check your privacy settings")
    exit(1)
"""

    try:
        result = subprocess.run(
            [python_cmd, "-c", camera_test],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        print(result.stdout)

        if result.returncode != 0:
            print_warning("Camera check failed - you may need to fix this before data collection")
            return False
    except Exception as e:
        print_warning(f"Camera check failed: {e}")
        return False

    print_success("Camera is accessible!")
    return True

def test_config_alignment(os_type, venv_name):
    """Test configuration alignment"""
    print_header("STEP 7: Testing Configuration Alignment")

    python_cmd = get_python_command(os_type, venv_name)
    python_cmd = os.path.abspath(python_cmd)

    config_test = """import os
import sys

# Test imports
try:
    from config import (
        ACTIONS,
        DATA_PATH,
        MODEL_PATH,
        LOGS_PATH,
        EPOCHS,
        BATCH_SIZE,
        LSTM_UNITS,
        DENSE_UNITS,
        DROPOUT_RATE,
        SEQUENCE_LENGTH,
        TOTAL_FEATURES,
        MIN_DETECTION_CONFIDENCE,
        MIN_TRACKING_CONFIDENCE,
        create_directories,
        get_model_path,
        ACTIVE_WEEK
    )
    print("   [OK] All config variables imported successfully")
except ImportError as e:
    print(f"   [FAIL] Config import failed: {e}")
    sys.exit(1)

# Test helper functions
try:
    model_path = get_model_path()
    create_directories()
    print("   [OK] Helper functions working")
except Exception as e:
    print(f"   [FAIL] Helper functions failed: {e}")
    sys.exit(1)

# Display configuration
print(f"   Active Week: {ACTIVE_WEEK}")
print(f"   Number of Signs: {len(ACTIONS)}")
print(f"   Signs: {list(ACTIONS)}")
print(f"   Model Path: {model_path}")

# Check for data
if os.path.exists(DATA_PATH):
    found = []
    missing = []
    for action in ACTIONS:
        action_path = os.path.join(DATA_PATH, action)
        if os.path.exists(action_path):
            sequences = [d for d in os.listdir(action_path) if os.path.isdir(os.path.join(action_path, d))]
            found.append((action, len(sequences)))
        else:
            missing.append(action)

    if found:
        print(f"   [OK] Found data for {len(found)} signs:")
        for action, count in found[:3]:  # Show first 3
            print(f"      - {action}: {count} sequences")
        if len(found) > 3:
            print(f"      ... and {len(found) - 3} more")

    if missing:
        print(f"   [WARNING] Missing data for {len(missing)} signs")
        print(f"      Run data_collection.py to collect data")
else:
    print(f"   [WARNING] No data collected yet")
    print(f"      Run data_collection.py to start collecting")

print("   [OK] Configuration is properly aligned!")
"""

    try:
        result = subprocess.run(
            [python_cmd, "-c", config_test],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        print(result.stdout)

        if result.returncode != 0:
            print_error("Configuration alignment test failed!")
            if result.stderr:
                print_error(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Configuration test failed: {e}")
        return False

    print_success("Configuration is properly aligned!")
    return True

def print_next_steps(os_type, venv_name):
    """Print instructions for next steps"""
    print_header("🎉 SETUP COMPLETE!")

    activation_cmd = get_activation_command(os_type, venv_name)

    print_success("Your SASL project environment is ready!")
    print()
    print_info("To start working on the project:")
    print()

    if os_type == "windows":
        print(f"   1. Activate the virtual environment:")
        print(f"      {activation_cmd}")
        print()
        print(f"   2. Run data collection:")
        print(f"      python data_collection.py")
        print()
        print(f"   3. Train the model:")
        print(f"      python train.py")
        print()
        print(f"   4. Test the model:")
        print(f"      python predict.py")
    else:  # mac or linux
        print(f"   1. Activate the virtual environment:")
        print(f"      {activation_cmd}")
        print()
        print(f"   2. Run data collection:")
        print(f"      python data_collection.py")
        print()
        print(f"   3. Train the model:")
        print(f"      python train.py")
        print()
        print(f"   4. Test the model:")
        print(f"      python predict.py")

    print()
    print_warning("Remember to activate the virtual environment every time you work on the project!")
    print()

def main():
    """Main setup function"""
    print_header("🚀 SASL PROJECT - AUTOMATED SETUP")

    # Detect OS
    os_type = detect_os()
    print_info(f"Detected OS: {os_type.upper()}")

    if os_type == "unknown":
        print_error("Unsupported operating system!")
        sys.exit(1)

    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)

    # Step 2: Create virtual environment
    success, venv_name = create_virtual_environment(os_type)
    if not success:
        sys.exit(1)

    # Step 3: Install requirements
    if not install_requirements(os_type, venv_name):
        print_error("Failed to install requirements!")
        sys.exit(1)

    # Step 4: Verify installation
    if not verify_installation(os_type, venv_name):
        print_error("Installation verification failed!")
        sys.exit(1)

    # Step 5: Check permissions
    if not check_permissions():
        print_warning("Permission check failed, but continuing...")

    # Step 6: Check camera
    if not check_camera(os_type, venv_name):
        print_warning("Camera check failed, but continuing...")

    # Step 7: Test configuration
    if not test_config_alignment(os_type, venv_name):
        print_error("Configuration alignment test failed!")
        sys.exit(1)

    # Print next steps
    print_next_steps(os_type, venv_name)

if __name__ == "__main__":
    main()

