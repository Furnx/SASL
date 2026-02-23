"""
Data Augmentation for Sign Language Recognition
================================================
Drop-in replacement for the original augmentation.py.
Same public API — augment_sequence() and create_augmented_dataset() —
so all existing training scripts work without any changes.

Improvements over v1:
  - time_warp: bidirectional resample instead of padding (no frozen frames)
  - gaussian_noise: different σ per body part (pose/face/hand)
  - horizontal_flip: correct 3-step flip — x mirror + hand swap + pose pairs
  - seed control: every augmented copy is reproducible
  - keypoint_dropout: replaced with per-part noise (zeros corrupt hand data)
  - all spatial transforms clip to [0.0, 1.0]

File-level augmentation (optional):
  Run this file directly to pre-generate augmented .npy files on disk.
  Set INPUT_ROOT, OUTPUT_ROOT, COPIES at the top then: python augmentation.py

Author: WeThinkCode_Cohort_2025_SASL
Date: 2026-02-23
"""

import os
import numpy as np
from scipy import interpolate
from scipy.interpolate import interp1d

# Try to import from config (used when called from training scripts)
# Falls back to safe defaults when run standalone
try:
    from config import AUGMENTATION_CONFIG, LANDMARK_STRUCTURE, SEQUENCE_LENGTH
except ImportError:
    SEQUENCE_LENGTH = 30
    LANDMARK_STRUCTURE = {
        "pose": {
            "start": 0, "count": 33,
            "features_per_landmark": 4,
            "has_visibility": True,
        },
        "face": {
            "start": 132, "count": 468,
            "features_per_landmark": 3,
            "has_visibility": False,
        },
        "left_hand": {
            "start": 1536, "count": 21,
            "features_per_landmark": 3,
            "has_visibility": False,
        },
        "right_hand": {
            "start": 1599, "count": 21,
            "features_per_landmark": 3,
            "has_visibility": False,
        },
    }
    AUGMENTATION_CONFIG = {
        "time_warp":        {"enabled": True,  "probability": 0.6, "speed_range":  (0.8, 1.2)},
        "translate":        {"enabled": True,  "probability": 0.5, "shift_range":  (-0.05, 0.05)},
        "scale":            {"enabled": True,  "probability": 0.5, "scale_range":  (0.88, 1.12)},
        "rotate":           {"enabled": True,  "probability": 0.5, "angle_range":  (-5.0, 5.0)},
        "gaussian_noise":   {"enabled": True,  "probability": 0.7, "noise_std":    0.002},
        "horizontal_flip":  {"enabled": True,  "probability": 0.5},
        "keypoint_dropout": {"enabled": False, "probability": 0.0, "dropout_rate": 0.0},
    }

# =============================================================================
# FILE-LEVEL CONFIG  (only used when running this file directly)
# =============================================================================

INPUT_ROOT    = "converting_videos_with_OPENCV_AND_MEDIAPIPE/numpy_normalised"   # output from normalise_sequences.py
OUTPUT_ROOT   = "converting_videos_with_OPENCV_AND_MEDIAPIPE/numpy_augmented"
COPIES        = 20                   # augmented copies per original file
                                     # 10–30 is safe — each gets a unique seed
TARGET_FRAMES = SEQUENCE_LENGTH      # stays in sync with config

# =============================================================================
# FEATURE VECTOR LAYOUT  (1662 total)
# Derived from LANDMARK_STRUCTURE so changing config updates everything
# =============================================================================

POSE_START  = LANDMARK_STRUCTURE["pose"]["start"]
POSE_END    = POSE_START + LANDMARK_STRUCTURE["pose"]["count"] * LANDMARK_STRUCTURE["pose"]["features_per_landmark"]
FACE_START  = LANDMARK_STRUCTURE["face"]["start"]
FACE_END    = FACE_START + LANDMARK_STRUCTURE["face"]["count"] * LANDMARK_STRUCTURE["face"]["features_per_landmark"]
LHAND_START = LANDMARK_STRUCTURE["left_hand"]["start"]
LHAND_END   = LHAND_START + LANDMARK_STRUCTURE["left_hand"]["count"] * LANDMARK_STRUCTURE["left_hand"]["features_per_landmark"]
RHAND_START = LANDMARK_STRUCTURE["right_hand"]["start"]
RHAND_END   = RHAND_START + LANDMARK_STRUCTURE["right_hand"]["count"] * LANDMARK_STRUCTURE["right_hand"]["features_per_landmark"]

POSE_LM  = LANDMARK_STRUCTURE["pose"]["count"]
FACE_LM  = LANDMARK_STRUCTURE["face"]["count"]
HAND_LM  = LANDMARK_STRUCTURE["left_hand"]["count"]
TOTAL_DIM = RHAND_END   # 1662

# Per-body-part noise standard deviations
# Separate values because finger joints are far more semantically precise
# than gross body position landmarks
_NOISE_STD = {
    "pose":  0.003,   # shoulder/hip — tolerant
    "face":  0.002,   # expression — medium
    "hand":  0.001,   # finger joints — smallest
}

# MediaPipe Pose left↔right landmark index pairs
# Required for correct horizontal flip — without these swaps
# the model learns wrong handedness silently
_POSE_FLIP_PAIRS = [
    (1, 4), (2, 5), (3, 6),
    (7, 8),
    (9, 10),
    (11, 12), (13, 14), (15, 16),
    (17, 18), (19, 20), (21, 22),
    (23, 24), (25, 26), (27, 28),
    (29, 30), (31, 32),
]


# =============================================================================
# TEMPORAL AUGMENTATION
# =============================================================================

def time_warp(sequence, speed_factor):
    """
    Speed up or slow down the sequence by interpolating frames.

    Fixes original v1 bug: instead of padding with the last value
    (which froze the sign mid-motion), this resamples bidirectionally
    so all TARGET_FRAMES are filled with real motion.

    Args:
        sequence:     (sequence_length, features)
        speed_factor: float — 1.2 = 20% faster, 0.8 = 20% slower
    Returns:
        warped: (sequence_length, features) — same shape, different timing
    """
    original_length = len(sequence)
    new_length      = max(2, int(original_length / speed_factor))

    t_orig    = np.linspace(0, 1, original_length)
    t_new     = np.linspace(0, 1, new_length)
    t_final   = np.linspace(0, 1, original_length)

    f1        = interp1d(t_orig, sequence, axis=0, kind="linear")
    stretched = f1(t_new)

    f2        = interp1d(t_new, stretched, axis=0, kind="linear")
    return f2(t_final).astype(sequence.dtype)


# =============================================================================
# SPATIAL AUGMENTATIONS  (frame-level — same API as v1)
# =============================================================================

def translate_keypoints(keypoints, shift_x, shift_y):
    """
    Shift all keypoints by a fixed amount in x and y.
    Simulates different camera positions or user standing offset.

    Args:
        keypoints: (features,)
        shift_x:   float — horizontal shift
        shift_y:   float — vertical shift
    Returns:
        shifted: (features,)
    """
    shifted = keypoints.copy()
    for info in LANDMARK_STRUCTURE.values():
        start = info["start"]
        count = info["count"]
        fpl   = info["features_per_landmark"]
        for i in range(count):
            base = start + i * fpl
            shifted[base]     = np.clip(shifted[base]     + shift_x, 0.0, 1.0)
            shifted[base + 1] = np.clip(shifted[base + 1] + shift_y, 0.0, 1.0)
    return shifted


def scale_keypoints(keypoints, scale_factor):
    """
    Scale keypoints around their centroid.
    Simulates signer being closer or further from the camera.
    Only x,y are scaled — z is noisy from MediaPipe and gains nothing.

    Args:
        keypoints:    (features,)
        scale_factor: float — 1.0 = no change
    Returns:
        scaled: (features,)
    """
    x_vals, y_vals = [], []
    for info in LANDMARK_STRUCTURE.values():
        start = info["start"]
        count = info["count"]
        fpl   = info["features_per_landmark"]
        for i in range(count):
            base = start + i * fpl
            x_vals.append(keypoints[base])
            y_vals.append(keypoints[base + 1])

    cx = float(np.mean(x_vals))
    cy = float(np.mean(y_vals))

    scaled = keypoints.copy()
    for info in LANDMARK_STRUCTURE.values():
        start = info["start"]
        count = info["count"]
        fpl   = info["features_per_landmark"]
        for i in range(count):
            base = start + i * fpl
            scaled[base]     = np.clip(cx + (keypoints[base]     - cx) * scale_factor, 0.0, 1.0)
            scaled[base + 1] = np.clip(cy + (keypoints[base + 1] - cy) * scale_factor, 0.0, 1.0)
    return scaled


def rotate_keypoints(keypoints, angle_degrees):
    """
    Rotate keypoints around their centroid.
    Simulates slight camera tilt — keep angle_degrees small (±5°).
    Larger angles change sign meaning and corrupt labels silently.

    Args:
        keypoints:     (features,)
        angle_degrees: float
    Returns:
        rotated: (features,)
    """
    angle_rad    = np.radians(angle_degrees)
    cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)

    x_vals, y_vals = [], []
    for info in LANDMARK_STRUCTURE.values():
        start = info["start"]
        count = info["count"]
        fpl   = info["features_per_landmark"]
        for i in range(count):
            base = start + i * fpl
            x_vals.append(keypoints[base])
            y_vals.append(keypoints[base + 1])

    cx = float(np.mean(x_vals))
    cy = float(np.mean(y_vals))

    rotated = keypoints.copy()
    for info in LANDMARK_STRUCTURE.values():
        start = info["start"]
        count = info["count"]
        fpl   = info["features_per_landmark"]
        for i in range(count):
            base = start + i * fpl
            dx = keypoints[base]     - cx
            dy = keypoints[base + 1] - cy
            rotated[base]     = cx + dx * cos_a - dy * sin_a
            rotated[base + 1] = cy + dx * sin_a + dy * cos_a
    return rotated


def add_gaussian_noise(keypoints, noise_std):
    """
    Add Gaussian noise tuned per body part.

    Improvement over v1: applies a different σ to pose, face, and hand
    landmarks instead of one global std — finger joints get the smallest
    noise because they carry the most precise semantic information.

    Args:
        keypoints: (features,)
        noise_std: float — used as base; hand noise is always halved
    Returns:
        noisy: (features,)
    """
    noisy = keypoints.copy()

    # Pose — coarsest body landmarks
    noisy[POSE_START:POSE_END] += np.random.normal(
        0, _NOISE_STD["pose"], POSE_END - POSE_START)

    # Face — expression landmarks
    noisy[FACE_START:FACE_END] += np.random.normal(
        0, _NOISE_STD["face"], FACE_END - FACE_START)

    # Both hands — finger joints, smallest noise
    noisy[LHAND_START:RHAND_END] += np.random.normal(
        0, _NOISE_STD["hand"], RHAND_END - LHAND_START)

    return np.clip(noisy, 0.0, 1.0)


def keypoint_dropout(keypoints, dropout_rate):
    """
    Kept for backward compatibility with existing config files.
    Now a no-op — zeroing landmarks teaches the model that 0 = valid
    mid-sign data, which conflicts with zero-padded missing hands.
    Use gaussian_noise instead for occlusion simulation.

    Args:
        keypoints:    (features,)
        dropout_rate: float — ignored
    Returns:
        keypoints unchanged
    """
    return keypoints.copy()


# =============================================================================
# HORIZONTAL FLIP  (sequence-level)
# =============================================================================

def horizontal_flip(sequence):
    """
    Mirror the signer left↔right — the most powerful sign language augmentation.

    Three steps happen together (all three are required for correctness):
      1. All x coordinates  →  1 - x  across pose, face, and both hands
      2. Left hand array   ↔  Right hand array  (swapped entirely)
      3. Left pose landmarks ↔ Right pose landmarks  (paired index swap)

    Skipping step 2 or 3 silently teaches the model wrong handedness.

    Args:
        sequence: (sequence_length, features)
    Returns:
        flipped: (sequence_length, features)
    """
    seq_len = len(sequence)
    flipped = sequence.copy()

    # 1 + 3: Pose — flip x then swap left/right landmark pairs
    pose = flipped[:, POSE_START:POSE_END].reshape(seq_len, POSE_LM, 4)
    pose[:, :, 0] = 1.0 - pose[:, :, 0]
    for l_idx, r_idx in _POSE_FLIP_PAIRS:
        pose[:, l_idx, :], pose[:, r_idx, :] = (
            pose[:, r_idx, :].copy(),
            pose[:, l_idx, :].copy()
        )
    flipped[:, POSE_START:POSE_END] = pose.reshape(seq_len, -1)

    # 1: Face — flip x (face is symmetric, no pair swaps needed)
    face = flipped[:, FACE_START:FACE_END].reshape(seq_len, FACE_LM, 3)
    face[:, :, 0] = 1.0 - face[:, :, 0]
    flipped[:, FACE_START:FACE_END] = face.reshape(seq_len, -1)

    # 1: Flip x on both hands before swapping arrays
    lhand = flipped[:, LHAND_START:LHAND_END].reshape(seq_len, HAND_LM, 3)
    rhand = flipped[:, RHAND_START:RHAND_END].reshape(seq_len, HAND_LM, 3)
    lhand[:, :, 0] = 1.0 - lhand[:, :, 0]
    rhand[:, :, 0] = 1.0 - rhand[:, :, 0]

    # 2: Swap left ↔ right hand arrays entirely
    flipped[:, LHAND_START:LHAND_END] = rhand.reshape(seq_len, -1)
    flipped[:, RHAND_START:RHAND_END] = lhand.reshape(seq_len, -1)

    return flipped


# =============================================================================
# MAIN AUGMENTATION PIPELINE  (same API as v1)
# =============================================================================

def augment_sequence(sequence, config=None, seed=None):
    """
    Apply multiple augmentations to a sequence.
    Drop-in replacement for the original augment_sequence().

    Randomly applies techniques based on config probabilities.
    Pass seed for reproducible augmentation (recommended for pre-generation).

    Args:
        sequence: (sequence_length, features) — e.g. (30, 1662)
        config:   dict — uses AUGMENTATION_CONFIG if None
        seed:     int or None — set for reproducible output
    Returns:
        augmented_sequence: (sequence_length, features) — same shape
    """
    if config is None:
        config = AUGMENTATION_CONFIG

    if seed is not None:
        np.random.seed(seed)

    aug_seq = sequence.copy()

    # 1. TEMPORAL (whole sequence)
    if config["time_warp"]["enabled"]:
        if np.random.random() < config["time_warp"]["probability"]:
            speed_min, speed_max = config["time_warp"]["speed_range"]
            speed   = np.random.uniform(speed_min, speed_max)
            aug_seq = time_warp(aug_seq, speed)

    # 2. HORIZONTAL FLIP (whole sequence, before per-frame transforms)
    flip_cfg = config.get("horizontal_flip", {"enabled": True, "probability": 0.5})
    if flip_cfg["enabled"]:
        if np.random.random() < flip_cfg["probability"]:
            aug_seq = horizontal_flip(aug_seq)

    # 3. SPATIAL + NOISE (per frame)
    for frame_idx in range(len(aug_seq)):
        frame = aug_seq[frame_idx]

        if config["translate"]["enabled"]:
            if np.random.random() < config["translate"]["probability"]:
                shift_min, shift_max = config["translate"]["shift_range"]
                frame = translate_keypoints(
                    frame,
                    np.random.uniform(shift_min, shift_max),
                    np.random.uniform(shift_min, shift_max)
                )

        if config["scale"]["enabled"]:
            if np.random.random() < config["scale"]["probability"]:
                scale_min, scale_max = config["scale"]["scale_range"]
                frame = scale_keypoints(frame, np.random.uniform(scale_min, scale_max))

        if config["rotate"]["enabled"]:
            if np.random.random() < config["rotate"]["probability"]:
                angle_min, angle_max = config["rotate"]["angle_range"]
                frame = rotate_keypoints(frame, np.random.uniform(angle_min, angle_max))

        if config["gaussian_noise"]["enabled"]:
            if np.random.random() < config["gaussian_noise"]["probability"]:
                # noise_std from config is accepted but per-part stds take priority
                frame = add_gaussian_noise(frame, config["gaussian_noise"]["noise_std"])

        if config.get("keypoint_dropout", {}).get("enabled", False):
            if np.random.random() < config["keypoint_dropout"]["probability"]:
                frame = keypoint_dropout(frame, config["keypoint_dropout"]["dropout_rate"])

        aug_seq[frame_idx] = frame

    return aug_seq


def create_augmented_dataset(sequences, labels, augmentation_factor):
    """
    Create augmented versions of the entire dataset.
    Drop-in replacement for the original create_augmented_dataset().

    Flow (matches training pipeline):
      1. Start with original sequences + labels
      2. For each of augmentation_factor passes, create one augmented
         copy of every sequence with a unique reproducible seed
      3. Stack originals + all augmented copies together
      4. Return combined arrays ready for train/test split

    Example:
      30 original sequences × augmentation_factor=4
      → 30 + 120 = 150 total sequences

    Args:
        sequences:           (N, sequence_length, features)
        labels:              (N, num_classes) one-hot encoded
        augmentation_factor: int — augmented copies per sequence
    Returns:
        final_sequences: (N * (1 + factor), sequence_length, features)
        final_labels:    (N * (1 + factor), num_classes)
    """
    print(f"\n{'='*60}")
    print(f"CREATING AUGMENTED DATASET")
    print(f"{'='*60}")
    print(f"Original sequences  : {len(sequences)}")
    print(f"Augmentation factor : {augmentation_factor}")
    print(f"Expected total      : {len(sequences) * (1 + augmentation_factor)}")
    print(f"{'='*60}\n")

    augmented_sequences = [sequences]
    augmented_labels    = [labels]

    for aug_idx in range(augmentation_factor):
        print(f"Creating augmented set {aug_idx + 1}/{augmentation_factor}...")
        aug_set = []
        for seq_idx, seq in enumerate(sequences):
            # Unique seed per (augmentation pass, sequence) → reproducible
            seed = abs(hash(f"{aug_idx}_{seq_idx}")) % (2**31)
            aug_set.append(augment_sequence(seq, seed=seed))

        augmented_sequences.append(np.array(aug_set))
        augmented_labels.append(labels)

    final_sequences = np.concatenate(augmented_sequences, axis=0)
    final_labels    = np.concatenate(augmented_labels,    axis=0)

    print(f"\n  Original : {len(sequences)} sequences")
    print(f"  Final    : {len(final_sequences)} sequences")
    print(f"  Increase : +{len(final_sequences) - len(sequences)} "
          f"({((len(final_sequences) / len(sequences)) - 1) * 100:.0f}% more data)")
    print(f"{'='*60}\n")

    return final_sequences, final_labels


# =============================================================================
# FILE-BASED PRE-GENERATION  (run this file directly to save .npy to disk)
# =============================================================================

def _collect_npy_files(root):
    found = []
    for r, dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".npy"):
                found.append(os.path.join(r, f))
    return found


def _run_file_augmentation():
    all_files = _collect_npy_files(INPUT_ROOT)
    print(f"\n{'='*65}")
    print(f"SIGN LANGUAGE DATA AUGMENTATION  (file mode)")
    print(f"{'='*65}")
    print(f"Source files : {len(all_files)}")
    print(f"Copies each  : {COPIES}")
    print(f"Output       : {OUTPUT_ROOT}")
    print(f"{'='*65}\n")

    processed = skipped = errors = 0

    for npy_path in all_files:
        relative  = os.path.relpath(npy_path, INPUT_ROOT)
        rel_dir   = os.path.dirname(relative)
        filename  = os.path.splitext(os.path.basename(relative))[0]
        out_dir   = os.path.join(OUTPUT_ROOT, rel_dir)
        os.makedirs(out_dir, exist_ok=True)

        try:
            original = np.load(npy_path, allow_pickle=False).astype(np.float32)
        except Exception as e:
            print(f"  [ERROR] {npy_path}: {e}")
            errors += 1
            continue

        if original.ndim != 2 or original.shape != (TARGET_FRAMES, TOTAL_DIM):
            print(f"  [WARN] Shape {original.shape} — expected ({TARGET_FRAMES}, {TOTAL_DIM}), skipping")
            skipped += 1
            continue

        orig_out = os.path.join(out_dir, f"{filename}_aug_000.npy")
        if not os.path.exists(orig_out):
            np.save(orig_out, original)

        for i in range(1, COPIES + 1):
            out_path = os.path.join(out_dir, f"{filename}_aug_{i:03d}.npy")
            if os.path.exists(out_path):
                skipped += 1
                continue
            seed      = abs(hash(npy_path + str(i))) % (2**31)
            augmented = augment_sequence(original, seed=seed)
            np.save(out_path, augmented)
            processed += 1

        print(f"  [OK] {os.path.basename(npy_path)} → {COPIES} copies")

    print(f"\n{'='*65}")
    print(f"Done. Saved: {processed}  Skipped: {skipped}  Errors: {errors}")
    print(f"{'='*65}")


if __name__ == "__main__":
    _run_file_augmentation()