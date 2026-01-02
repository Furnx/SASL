"""
Data Augmentation for Sign Language Recognition
================================================
This module provides augmentation techniques for sign language keypoint sequences.

Augmentation happens during training, not during data collection.
It works with your existing collected data by mathematically transforming the keypoints.

Techniques:
1. Temporal: Time warping (speed changes)
2. Spatial: Translation, scaling, rotation
3. Noise: Gaussian noise, keypoint dropout

Author: WeThinkCode_Cohort_2025_SASL
Date: 2026-01-02
"""

import numpy as np
from scipy import interpolate
from config import AUGMENTATION_CONFIG, LANDMARK_STRUCTURE, SEQUENCE_LENGTH

# =============================================================================
# TEMPORAL AUGMENTATION (Time-based)
# =============================================================================

def time_warp(sequence, speed_factor):
    """
    Speed up or slow down the sequence by interpolating frames.
    
    Example:
        speed_factor = 1.2 → 20% faster (compress time)
        speed_factor = 0.8 → 20% slower (stretch time)
    
    Args:
        sequence: (sequence_length, features) - e.g., (30, 1662)
        speed_factor: float - speed multiplier
    
    Returns:
        warped_sequence: (sequence_length, features) - same shape as input
    """
    original_length = len(sequence)
    new_length = int(original_length / speed_factor)
    
    # Interpolate each feature dimension
    warped = np.zeros_like(sequence)
    
    for feature_idx in range(sequence.shape[1]):
        # Original indices
        x_original = np.arange(original_length)
        y_original = sequence[:, feature_idx]
        
        # New indices (warped time)
        x_new = np.linspace(0, original_length - 1, new_length)
        
        # Interpolate
        f = interpolate.interp1d(x_original, y_original, kind='linear', fill_value='extrapolate')
        y_new = f(x_new)
        
        # Pad or trim to original length
        if new_length < original_length:
            # Pad with last value
            padding = np.full(original_length - new_length, y_new[-1])
            y_new = np.concatenate([y_new, padding])
        else:
            # Trim to original length
            y_new = y_new[:original_length]
        
        warped[:, feature_idx] = y_new
    
    return warped


# =============================================================================
# SPATIAL AUGMENTATION (Position-based)
# =============================================================================

def translate_keypoints(keypoints, shift_x, shift_y):
    """
    Shift all keypoints by a fixed amount in x and y directions.
    Simulates different camera positions or user positions.
    
    Args:
        keypoints: (features,) - e.g., (1662,) for a single frame
        shift_x: float - horizontal shift
        shift_y: float - vertical shift
    
    Returns:
        shifted_keypoints: (features,) - same shape as input
    """
    shifted = keypoints.copy()
    
    # Process each landmark type
    for landmark_type, info in LANDMARK_STRUCTURE.items():
        start = info['start']
        count = info['count']
        features_per = info['features_per_landmark']
        
        # Shift x and y coordinates (not z or visibility)
        for i in range(count):
            base_idx = start + (i * features_per)
            shifted[base_idx] += shift_x      # x coordinate
            shifted[base_idx + 1] += shift_y  # y coordinate
            # Don't modify z (base_idx + 2) or visibility (if exists)
    
    return shifted


def scale_keypoints(keypoints, scale_factor):
    """
    Scale keypoints around their center point.
    Simulates different distances from camera.
    
    Args:
        keypoints: (features,) - e.g., (1662,)
        scale_factor: float - scale multiplier (1.0 = no change)
    
    Returns:
        scaled_keypoints: (features,) - same shape as input
    """
    scaled = keypoints.copy()
    
    # Find center of all keypoints (average x, y)
    x_coords = []
    y_coords = []
    
    for landmark_type, info in LANDMARK_STRUCTURE.items():
        start = info['start']
        count = info['count']
        features_per = info['features_per_landmark']
        
        for i in range(count):
            base_idx = start + (i * features_per)
            x_coords.append(keypoints[base_idx])
            y_coords.append(keypoints[base_idx + 1])
    
    center_x = np.mean(x_coords)
    center_y = np.mean(y_coords)
    
    # Scale around center
    for landmark_type, info in LANDMARK_STRUCTURE.items():
        start = info['start']
        count = info['count']
        features_per = info['features_per_landmark']
        
        for i in range(count):
            base_idx = start + (i * features_per)
            
            # Scale x and y
            x = keypoints[base_idx]
            y = keypoints[base_idx + 1]
            
            scaled[base_idx] = center_x + (x - center_x) * scale_factor
            scaled[base_idx + 1] = center_y + (y - center_y) * scale_factor
    
    return scaled


def rotate_keypoints(keypoints, angle_degrees):
    """
    Rotate keypoints around their center point.
    Simulates different camera angles.
    
    Args:
        keypoints: (features,) - e.g., (1662,)
        angle_degrees: float - rotation angle in degrees
    
    Returns:
        rotated_keypoints: (features,) - same shape as input
    """
    rotated = keypoints.copy()
    angle_rad = np.radians(angle_degrees)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    # Find center
    x_coords = []
    y_coords = []

    for landmark_type, info in LANDMARK_STRUCTURE.items():
        start = info['start']
        count = info['count']
        features_per = info['features_per_landmark']

        for i in range(count):
            base_idx = start + (i * features_per)
            x_coords.append(keypoints[base_idx])
            y_coords.append(keypoints[base_idx + 1])

    center_x = np.mean(x_coords)
    center_y = np.mean(y_coords)

    # Rotate around center
    # Rotation matrix: [x'] = [cos -sin] [x - cx] + [cx]
    #                  [y']   [sin  cos] [y - cy]   [cy]
    for landmark_type, info in LANDMARK_STRUCTURE.items():
        start = info['start']
        count = info['count']
        features_per = info['features_per_landmark']

        for i in range(count):
            base_idx = start + (i * features_per)

            # Get coordinates relative to center
            x = keypoints[base_idx] - center_x
            y = keypoints[base_idx + 1] - center_y

            # Apply rotation
            rotated[base_idx] = center_x + (x * cos_a - y * sin_a)
            rotated[base_idx + 1] = center_y + (x * sin_a + y * cos_a)

    return rotated


# =============================================================================
# NOISE AUGMENTATION
# =============================================================================

def add_gaussian_noise(keypoints, noise_std):
    """
    Add Gaussian noise to keypoints.
    Simulates MediaPipe detection jitter/instability.

    Args:
        keypoints: (features,) - e.g., (1662,)
        noise_std: float - standard deviation of noise

    Returns:
        noisy_keypoints: (features,) - same shape as input
    """
    noise = np.random.normal(0, noise_std, keypoints.shape)
    return keypoints + noise


def keypoint_dropout(keypoints, dropout_rate):
    """
    Randomly zero out some keypoints.
    Simulates partial occlusion or detection failure.

    Args:
        keypoints: (features,) - e.g., (1662,)
        dropout_rate: float - probability of zeroing each keypoint

    Returns:
        dropped_keypoints: (features,) - same shape as input
    """
    dropped = keypoints.copy()

    # For each landmark, decide whether to drop it
    for landmark_type, info in LANDMARK_STRUCTURE.items():
        start = info['start']
        count = info['count']
        features_per = info['features_per_landmark']

        for i in range(count):
            if np.random.random() < dropout_rate:
                # Zero out this landmark
                base_idx = start + (i * features_per)
                for j in range(features_per):
                    dropped[base_idx + j] = 0.0

    return dropped


# =============================================================================
# MAIN AUGMENTATION PIPELINE
# =============================================================================

def augment_sequence(sequence, config=None):
    """
    Apply multiple augmentations to a sequence.

    This is the main function you'll call during training.
    It randomly applies various augmentation techniques based on config.

    Args:
        sequence: (sequence_length, features) - e.g., (30, 1662)
        config: dict - augmentation configuration (uses AUGMENTATION_CONFIG if None)

    Returns:
        augmented_sequence: (sequence_length, features) - same shape as input
    """
    if config is None:
        config = AUGMENTATION_CONFIG

    aug_seq = sequence.copy()

    # 1. TEMPORAL AUGMENTATION (apply to whole sequence)
    if config['time_warp']['enabled']:
        if np.random.random() < config['time_warp']['probability']:
            speed_min, speed_max = config['time_warp']['speed_range']
            speed = np.random.uniform(speed_min, speed_max)
            aug_seq = time_warp(aug_seq, speed)

    # 2. SPATIAL AUGMENTATIONS (apply to each frame)
    for frame_idx in range(len(aug_seq)):
        frame = aug_seq[frame_idx]

        # Translation
        if config['translate']['enabled']:
            if np.random.random() < config['translate']['probability']:
                shift_min, shift_max = config['translate']['shift_range']
                shift_x = np.random.uniform(shift_min, shift_max)
                shift_y = np.random.uniform(shift_min, shift_max)
                frame = translate_keypoints(frame, shift_x, shift_y)

        # Scaling
        if config['scale']['enabled']:
            if np.random.random() < config['scale']['probability']:
                scale_min, scale_max = config['scale']['scale_range']
                scale = np.random.uniform(scale_min, scale_max)
                frame = scale_keypoints(frame, scale)

        # Rotation
        if config['rotate']['enabled']:
            if np.random.random() < config['rotate']['probability']:
                angle_min, angle_max = config['rotate']['angle_range']
                angle = np.random.uniform(angle_min, angle_max)
                frame = rotate_keypoints(frame, angle)

        # Gaussian noise
        if config['gaussian_noise']['enabled']:
            if np.random.random() < config['gaussian_noise']['probability']:
                noise_std = config['gaussian_noise']['noise_std']
                frame = add_gaussian_noise(frame, noise_std)

        # Keypoint dropout
        if config['keypoint_dropout']['enabled']:
            if np.random.random() < config['keypoint_dropout']['probability']:
                dropout_rate = config['keypoint_dropout']['dropout_rate']
                frame = keypoint_dropout(frame, dropout_rate)

        aug_seq[frame_idx] = frame

    return aug_seq


def create_augmented_dataset(sequences, labels, augmentation_factor):
    """
    Create augmented versions of the entire dataset.

    For each original sequence, creates N augmented versions.

    Args:
        sequences: (num_sequences, sequence_length, features) - e.g., (330, 30, 1662)
        labels: (num_sequences, num_classes) - one-hot encoded labels
        augmentation_factor: int - number of augmented versions per sequence

    Returns:
        augmented_sequences: Combined original + augmented sequences
        augmented_labels: Corresponding labels
    """
    print(f"\n{'='*60}")
    print(f"CREATING AUGMENTED DATASET")
    print(f"{'='*60}")
    print(f"Original sequences: {len(sequences)}")
    print(f"Augmentation factor: {augmentation_factor}")
    print(f"Expected total: {len(sequences) * (1 + augmentation_factor)}")
    print(f"{'='*60}\n")

    augmented_sequences = [sequences]  # Start with original data
    augmented_labels = [labels]

    # Create augmented versions
    for aug_idx in range(augmentation_factor):
        print(f"Creating augmented set {aug_idx + 1}/{augmentation_factor}...")

        aug_set = []
        for seq in sequences:
            aug_seq = augment_sequence(seq)
            aug_set.append(aug_seq)

        augmented_sequences.append(np.array(aug_set))
        augmented_labels.append(labels)  # Same labels as original

    # Combine all
    final_sequences = np.concatenate(augmented_sequences, axis=0)
    final_labels = np.concatenate(augmented_labels, axis=0)

    print(f"\n✓ Augmentation complete!")
    print(f"  Original: {len(sequences)} sequences")
    print(f"  Final: {len(final_sequences)} sequences")
    print(f"  Increase: {len(final_sequences) - len(sequences)} sequences ({((len(final_sequences) / len(sequences)) - 1) * 100:.0f}% more data)")
    print(f"{'='*60}\n")

    return final_sequences, final_labels
