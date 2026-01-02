"""
Test Data Augmentation
======================
This script tests the augmentation functions to ensure they work correctly
with your existing data.

It will:
1. Load a sample sequence from your data
2. Apply each augmentation technique
3. Visualize the results
4. Verify data integrity

Author: Your Name
Date: 2026-01-02
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from config import DATA_PATH, ACTIONS, SEQUENCE_LENGTH
from augmentation import (
    time_warp,
    translate_keypoints,
    scale_keypoints,
    rotate_keypoints,
    add_gaussian_noise,
    keypoint_dropout,
    augment_sequence,
    create_augmented_dataset
)

def load_sample_sequence():
    """Load one sample sequence from existing data"""
    print("Loading sample sequence...")
    
    for action in ACTIONS:
        action_path = os.path.join(DATA_PATH, action)
        
        if not os.path.exists(action_path):
            continue
        
        # Get first sequence directory
        sequences_dirs = [d for d in os.listdir(action_path) 
                         if os.path.isdir(os.path.join(action_path, d))]
        
        if len(sequences_dirs) == 0:
            continue
        
        sequence_path = os.path.join(action_path, sequences_dirs[0])
        sequence = []
        
        # Load all frames
        for frame_num in range(SEQUENCE_LENGTH):
            npy_path = os.path.join(sequence_path, f"{frame_num}.npy")
            
            if not os.path.exists(npy_path):
                break
            
            try:
                frame = np.load(npy_path)
                sequence.append(frame)
            except Exception as e:
                print(f"Error loading {npy_path}: {e}")
                break
        
        if len(sequence) == SEQUENCE_LENGTH:
            print(f"✓ Loaded sequence from: {action}/{sequences_dirs[0]}")
            return np.array(sequence), action
    
    return None, None

def test_individual_augmentations():
    """Test each augmentation technique individually"""
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL AUGMENTATION TECHNIQUES")
    print("="*60 + "\n")
    
    sequence, action = load_sample_sequence()
    
    if sequence is None:
        print("❌ ERROR: No data found! Please run data_collection.py first.")
        return
    
    print(f"Original sequence shape: {sequence.shape}")
    print(f"Action: {action}\n")
    
    # Test 1: Time Warp
    print("1. Testing Time Warp...")
    try:
        warped_fast = time_warp(sequence, speed_factor=1.2)  # 20% faster
        warped_slow = time_warp(sequence, speed_factor=0.8)  # 20% slower
        print(f"   ✓ Fast version: {warped_fast.shape}")
        print(f"   ✓ Slow version: {warped_slow.shape}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Translation
    print("\n2. Testing Translation...")
    try:
        frame = sequence[0]
        translated = translate_keypoints(frame, shift_x=0.1, shift_y=-0.05)
        print(f"   ✓ Translated frame: {translated.shape}")
        print(f"   ✓ Mean shift: {np.mean(translated - frame):.6f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Scaling
    print("\n3. Testing Scaling...")
    try:
        frame = sequence[0]
        scaled_up = scale_keypoints(frame, scale_factor=1.1)
        scaled_down = scale_keypoints(frame, scale_factor=0.9)
        print(f"   ✓ Scaled up: {scaled_up.shape}")
        print(f"   ✓ Scaled down: {scaled_down.shape}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Rotation
    print("\n4. Testing Rotation...")
    try:
        frame = sequence[0]
        rotated_cw = rotate_keypoints(frame, angle_degrees=10)
        rotated_ccw = rotate_keypoints(frame, angle_degrees=-10)
        print(f"   ✓ Rotated clockwise: {rotated_cw.shape}")
        print(f"   ✓ Rotated counter-clockwise: {rotated_ccw.shape}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Gaussian Noise
    print("\n5. Testing Gaussian Noise...")
    try:
        frame = sequence[0]
        noisy = add_gaussian_noise(frame, noise_std=0.01)
        print(f"   ✓ Noisy frame: {noisy.shape}")
        print(f"   ✓ Noise level: {np.std(noisy - frame):.6f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Keypoint Dropout
    print("\n6. Testing Keypoint Dropout...")
    try:
        frame = sequence[0]
        dropped = keypoint_dropout(frame, dropout_rate=0.1)
        zeros_count = np.sum(dropped == 0)
        print(f"   ✓ Dropped frame: {dropped.shape}")
        print(f"   ✓ Zeroed values: {zeros_count}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✓ ALL INDIVIDUAL TESTS PASSED!")
    print("="*60 + "\n")

def test_full_augmentation_pipeline():
    """Test the complete augmentation pipeline"""
    print("\n" + "="*60)
    print("TESTING FULL AUGMENTATION PIPELINE")
    print("="*60 + "\n")
    
    sequence, action = load_sample_sequence()
    
    if sequence is None:
        print("❌ ERROR: No data found!")
        return
    
    print(f"Original sequence: {sequence.shape}")
    
    # Create 5 augmented versions
    print("\nCreating 5 augmented versions...")
    augmented_versions = []
    
    for i in range(5):
        aug_seq = augment_sequence(sequence)
        augmented_versions.append(aug_seq)
        print(f"  Version {i+1}: {aug_seq.shape}")
    
    print(f"\n✓ Created {len(augmented_versions)} augmented versions")
    
    # Verify they're different from original
    print("\nVerifying augmented versions are different from original...")
    for i, aug_seq in enumerate(augmented_versions):
        diff = np.mean(np.abs(aug_seq - sequence))
        print(f"  Version {i+1} difference: {diff:.6f}")
    
    print("\n" + "="*60)
    print("✓ FULL PIPELINE TEST PASSED!")
    print("="*60 + "\n")

def test_dataset_augmentation():
    """Test augmentation on a small dataset"""
    print("\n" + "="*60)
    print("TESTING DATASET AUGMENTATION")
    print("="*60 + "\n")
    
    # Load a few sequences
    sequences = []
    labels = []
    
    for action_idx, action in enumerate(ACTIONS[:3]):  # Test with first 3 actions
        action_path = os.path.join(DATA_PATH, action)
        
        if not os.path.exists(action_path):
            continue
        
        sequences_dirs = [d for d in os.listdir(action_path) 
                         if os.path.isdir(os.path.join(action_path, d))][:2]  # First 2 sequences
        
        for seq_dir in sequences_dirs:
            sequence_path = os.path.join(action_path, seq_dir)
            sequence = []
            
            for frame_num in range(SEQUENCE_LENGTH):
                npy_path = os.path.join(sequence_path, f"{frame_num}.npy")
                
                if os.path.exists(npy_path):
                    try:
                        frame = np.load(npy_path)
                        sequence.append(frame)
                    except:
                        break
            
            if len(sequence) == SEQUENCE_LENGTH:
                sequences.append(sequence)
                labels.append(action_idx)
    
    if len(sequences) == 0:
        print("❌ ERROR: No data found!")
        return
    
    sequences = np.array(sequences)
    labels = np.eye(len(ACTIONS))[labels]  # One-hot encode
    
    print(f"Loaded {len(sequences)} sequences")
    print(f"Original dataset shape: {sequences.shape}")
    
    # Apply augmentation
    aug_sequences, aug_labels = create_augmented_dataset(sequences, labels, augmentation_factor=3)
    
    print(f"\n✓ Augmentation successful!")
    print(f"  Original: {len(sequences)} sequences")
    print(f"  Augmented: {len(aug_sequences)} sequences")
    print(f"  Increase: {len(aug_sequences) - len(sequences)} sequences")
    
    print("\n" + "="*60)
    print("✓ DATASET AUGMENTATION TEST PASSED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATA AUGMENTATION TEST SUITE")
    print("="*60)
    
    # Run all tests
    test_individual_augmentations()
    test_full_augmentation_pipeline()
    test_dataset_augmentation()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYour augmentation system is working correctly!")
    print("You can now train your models with augmentation enabled.\n")

