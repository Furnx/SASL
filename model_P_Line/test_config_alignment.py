"""
Test script to verify that config.py is properly aligned with train.py and predict.py
Run this before training or predicting to ensure everything is configured correctly.
"""

print("="*60)
print(" 🔍 TESTING CONFIG ALIGNMENT")
print("="*60)

# Test 1: Import all required variables from config.py
print("\n[1/5] Testing config.py imports...")
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
    print("   ✅ All required variables imported successfully!")
except ImportError as e:
    print(f"   ❌ FAILED: {e}")
    exit(1)

# Test 2: Verify data types
print("\n[2/5] Testing variable types...")
import numpy as np

checks = [
    (isinstance(ACTIONS, np.ndarray), "ACTIONS should be numpy array"),
    (isinstance(DATA_PATH, str), "DATA_PATH should be string"),
    (isinstance(MODEL_PATH, str), "MODEL_PATH should be string"),
    (isinstance(LOGS_PATH, str), "LOGS_PATH should be string"),
    (isinstance(EPOCHS, int), "EPOCHS should be integer"),
    (isinstance(BATCH_SIZE, int), "BATCH_SIZE should be integer"),
    (isinstance(LSTM_UNITS, list), "LSTM_UNITS should be list"),
    (isinstance(DENSE_UNITS, list), "DENSE_UNITS should be list"),
    (isinstance(DROPOUT_RATE, float), "DROPOUT_RATE should be float"),
    (isinstance(SEQUENCE_LENGTH, int), "SEQUENCE_LENGTH should be integer"),
    (isinstance(TOTAL_FEATURES, int), "TOTAL_FEATURES should be integer"),
]

all_passed = True
for check, message in checks:
    if check:
        print(f"   ✅ {message}")
    else:
        print(f"   ❌ {message}")
        all_passed = False

if not all_passed:
    exit(1)

# Test 3: Verify helper functions
print("\n[3/5] Testing helper functions...")
try:
    model_path = get_model_path()
    print(f"   ✅ get_model_path() works: {model_path}")
    
    create_directories()
    print(f"   ✅ create_directories() works")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    exit(1)

# Test 4: Verify configuration values
print("\n[4/5] Testing configuration values...")
print(f"   Active Week: {ACTIVE_WEEK}")
print(f"   Number of Actions: {len(ACTIONS)}")
print(f"   Actions: {ACTIONS}")
print(f"   Sequence Length: {SEQUENCE_LENGTH} frames")
print(f"   Total Features: {TOTAL_FEATURES}")
print(f"   LSTM Architecture: {LSTM_UNITS}")
print(f"   Dense Architecture: {DENSE_UNITS}")
print(f"   Epochs: {EPOCHS}")
print(f"   Batch Size: {BATCH_SIZE}")
print(f"   Dropout Rate: {DROPOUT_RATE}")
print(f"   Model Path: {model_path}")

# Test 5: Check if data exists
print("\n[5/5] Checking for collected data...")
import os

if not os.path.exists(DATA_PATH):
    print(f"   ⚠️  WARNING: Data folder '{DATA_PATH}' does not exist yet")
    print(f"      Run data_collection.py first!")
else:
    found_actions = []
    missing_actions = []
    
    for action in ACTIONS:
        action_path = os.path.join(DATA_PATH, action)
        if os.path.exists(action_path):
            sequences = [d for d in os.listdir(action_path) if os.path.isdir(os.path.join(action_path, d))]
            found_actions.append((action, len(sequences)))
        else:
            missing_actions.append(action)
    
    if found_actions:
        print(f"   ✅ Found data for {len(found_actions)} actions:")
        for action, count in found_actions:
            print(f"      - {action}: {count} sequences")
    
    if missing_actions:
        print(f"   ⚠️  Missing data for {len(missing_actions)} actions:")
        for action in missing_actions:
            print(f"      - {action}")
        print(f"      Run data_collection.py to collect these signs!")

print("\n" + "="*60)
print(" ✅ CONFIGURATION ALIGNMENT TEST COMPLETE!")
print("="*60)
print("\n📋 Summary:")
print(f"   - Config file: ✅ Properly configured")
print(f"   - Active week: {ACTIVE_WEEK}")
print(f"   - Signs to train: {len(ACTIONS)}")
print(f"   - Model will be saved to: {model_path}")
print("\n🚀 You're ready to:")
print(f"   1. Collect data: python data_collection.py")
print(f"   2. Train model: python train.py")
print(f"   3. Test model: python predict.py")
print("="*60)

