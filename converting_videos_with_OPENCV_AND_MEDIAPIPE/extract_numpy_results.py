import cv2
import os
import numpy as np
import mediapipe as mp

# ====== INPUT / OUTPUT ROOTS ======
INPUT_ROOT  = "C:/365_days/converting_videos_with_OPENCV_AND_MEDIAPIPE/Demonstration_videos/Week_1_Greetings" #"Demonstration_videos"
OUTPUT_ROOT = "numpy_results_2_week1"

# ====== TUNING ======
HAND_HOLD_FRAMES = 25   # frames to hold last known hand position if both detectors lose it

# ====== MEDIAPIPE SETUP ======
mp_holistic = mp.solutions.holistic
mp_hands    = mp.solutions.hands

holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=2,
    smooth_landmarks=True,
    refine_face_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

# ====== FEATURE DIMENSIONS (matches your SASL config) ======
# Pose:       33 landmarks × 4 values (x, y, z, visibility) = 132
# Face:      468 landmarks × 3 values (x, y, z)             = 1404
# Left hand:  21 landmarks × 3 values (x, y, z)             =   63
# Right hand: 21 landmarks × 3 values (x, y, z)             =   63
# Total per frame: 1662
POSE_DIM       = 33  * 4
FACE_DIM       = 468 * 3
HAND_DIM       = 21  * 3
TOTAL_DIM      = POSE_DIM + FACE_DIM + HAND_DIM + HAND_DIM   # 1662


def get_hands_from_dedicated(frame_rgb):
    """Dedicated hand detector — fallback when Holistic misses a hand."""
    result      = hands_detector.process(frame_rgb)
    left_lm     = None
    right_lm    = None
    left_score  = 0.0
    right_score = 0.0

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_lm, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = handedness.classification[0].label
            score = handedness.classification[0].score
            if label == "Left":
                if score > left_score:
                    left_lm    = hand_lm
                    left_score = score
            else:
                if score > right_score:
                    right_lm    = hand_lm
                    right_score = score

    return left_lm, right_lm


def extract_pose(landmarks):
    """33 landmarks × (x, y, z, visibility) → flat array of 132."""
    if landmarks is None:
        return np.zeros(POSE_DIM)
    return np.array([[lm.x, lm.y, lm.z, lm.visibility]
                     for lm in landmarks.landmark]).flatten()


def extract_face(landmarks):
    """468 landmarks × (x, y, z) → flat array of 1404."""
    if landmarks is None:
        return np.zeros(FACE_DIM)
    return np.array([[lm.x, lm.y, lm.z]
                     for lm in landmarks.landmark]).flatten()


def extract_hand(landmarks):
    """21 landmarks × (x, y, z) → flat array of 63."""
    if landmarks is None:
        return np.zeros(HAND_DIM)
    return np.array([[lm.x, lm.y, lm.z]
                     for lm in landmarks.landmark]).flatten()


def extract_from_video(video_path):
    """
    Process one video and return an array of shape (num_frames, 1662).
    Uses dual-detector strategy + caching to maximise hand coverage.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [ERROR] Could not open: {video_path}")
        return None

    frames = []

    cached_left        = None
    cached_right       = None
    frames_since_left  = HAND_HOLD_FRAMES + 1
    frames_since_right = HAND_HOLD_FRAMES + 1

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Primary detector
        results  = holistic.process(frame_rgb)

        left_lm  = results.left_hand_landmarks
        right_lm = results.right_hand_landmarks

        # Dedicated fallback — runs every frame
        ded_left, ded_right = get_hands_from_dedicated(frame_rgb)

        if left_lm  is None and ded_left  is not None: left_lm  = ded_left
        if right_lm is None and ded_right is not None: right_lm = ded_right

        # Cache management
        if left_lm is not None:
            cached_left        = left_lm
            frames_since_left  = 0
        else:
            frames_since_left += 1

        if right_lm is not None:
            cached_right       = right_lm
            frames_since_right = 0
        else:
            frames_since_right += 1

        if left_lm  is None and frames_since_left  <= HAND_HOLD_FRAMES:
            left_lm  = cached_left
        if right_lm is None and frames_since_right <= HAND_HOLD_FRAMES:
            right_lm = cached_right

        # Build 1662-dim feature vector for this frame
        frame_vector = np.concatenate([
            extract_pose(results.pose_landmarks),   # 132
            extract_face(results.face_landmarks),   # 1404
            extract_hand(left_lm),                  # 63
            extract_hand(right_lm),                 # 63
        ])

        frames.append(frame_vector)

    cap.release()
    return np.array(frames)   # shape: (num_frames, 1662)


# ====== WALK THROUGH ALL SUBFOLDERS ======
processed = 0
skipped   = 0

for root, dirs, files in os.walk(INPUT_ROOT):
    for file in files:
        if not file.endswith(".mp4"):
            continue

        video_path    = os.path.join(root, file)
        relative_path = os.path.relpath(root, INPUT_ROOT)
        output_dir    = os.path.join(OUTPUT_ROOT, relative_path)
        os.makedirs(output_dir, exist_ok=True)

        filename_no_ext = os.path.splitext(file)[0]
        save_path       = os.path.join(output_dir, f"{filename_no_ext}.npy")

        if os.path.exists(save_path):
            print(f"  [SKIP] Already exists: {save_path}")
            skipped += 1
            continue

        print(f"Processing: {video_path}")
        data = extract_from_video(video_path)

        if data is not None and len(data) > 0:
            np.save(save_path, data)
            print(f"  [SAVED] {save_path} | shape: {data.shape}")
            processed += 1
        else:
            print(f"  [WARN] No frames extracted from {video_path}")

holistic.close()
hands_detector.close()
print(f"\nDone. {processed} video(s) processed, {skipped} skipped.")