import cv2
import os
import mediapipe as mp

# ====== INPUT / OUTPUT ROOTS ======
INPUT_ROOT  = "Demonstration_videos"
OUTPUT_ROOT = "pose_visualized_videos"

# ====== TUNING ======
# Hold last known hand position for this many frames when both detectors lose it
# Increase this further if hands still disappear during transitions
HAND_HOLD_FRAMES = 25

# ====== MEDIAPIPE SETUP ======
mp_holistic = mp.solutions.holistic
mp_hands    = mp.solutions.hands
mp_drawing  = mp.solutions.drawing_utils

# Primary: full body + face + hands
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=2,           # max accuracy
    smooth_landmarks=True,
    refine_face_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Secondary: dedicated hand model — runs on EVERY frame alongside holistic
# Lower thresholds so it catches hands that holistic misses
hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=1,
    min_detection_confidence=0.3,
    min_tracking_confidence=0.3
)

# ====== DRAWING STYLES ======
POSE_LM   = mp_drawing.DrawingSpec(color=(0, 255, 0),   thickness=3, circle_radius=3)
POSE_CONN = mp_drawing.DrawingSpec(color=(0, 220, 220), thickness=2)
HAND_LM   = mp_drawing.DrawingSpec(color=(255, 80, 0),  thickness=2, circle_radius=4)
HAND_CONN = mp_drawing.DrawingSpec(color=(255, 200, 0), thickness=2)
FACE_LM   = mp_drawing.DrawingSpec(color=(180, 0, 255), thickness=1, circle_radius=1)
FACE_CONN = mp_drawing.DrawingSpec(color=(120, 0, 180), thickness=1)


def get_hands_from_dedicated(frame_rgb):
    """
    Run the dedicated hands detector and return (left_lm, right_lm, score_left, score_right).
    Also returns confidence score so we can prefer the higher-confidence result.
    """
    result   = hands_detector.process(frame_rgb)
    left_lm  = None
    right_lm = None
    left_score  = 0.0
    right_score = 0.0

    if result.multi_hand_landmarks and result.multi_handedness:
        for hand_lm, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = handedness.classification[0].label       # "Left" or "Right"
            score = handedness.classification[0].score
            if label == "Left":
                if score > left_score:
                    left_lm    = hand_lm
                    left_score = score
            else:
                if score > right_score:
                    right_lm    = hand_lm
                    right_score = score

    return left_lm, right_lm, left_score, right_score


def merge_hand_results(holistic_lm, dedicated_lm):
    """
    Prefer holistic result if available; fill in with dedicated detector otherwise.
    Returns (landmark, source_string).
    """
    if holistic_lm is not None:
        return holistic_lm, "LIVE"
    if dedicated_lm is not None:
        return dedicated_lm, "DEDCTD"
    return None, None


def draw_all_landmarks(frame, results, left_lm, right_lm):
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=POSE_LM, connection_drawing_spec=POSE_CONN
        )
    if results.face_landmarks:
        mp_drawing.draw_landmarks(
            frame, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS,
            landmark_drawing_spec=FACE_LM, connection_drawing_spec=FACE_CONN
        )
    if left_lm:
        mp_drawing.draw_landmarks(
            frame, left_lm, mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=HAND_LM, connection_drawing_spec=HAND_CONN
        )
    if right_lm:
        mp_drawing.draw_landmarks(
            frame, right_lm, mp_holistic.HAND_CONNECTIONS,
            landmark_drawing_spec=HAND_LM, connection_drawing_spec=HAND_CONN
        )


def create_holistic_video(video_path, output_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  [ERROR] Could not open: {video_path}")
        return

    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Cache for when BOTH detectors miss a hand
    cached_left        = None
    cached_right       = None
    frames_since_left  = HAND_HOLD_FRAMES + 1   # start expired
    frames_since_right = HAND_HOLD_FRAMES + 1

    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ---- Run BOTH detectors on every frame ----
        holistic_results                    = holistic.process(frame_rgb)
        ded_left, ded_right, _, _           = get_hands_from_dedicated(frame_rgb)

        # ---- Merge: holistic wins, dedicated fills gaps ----
        left_lm,  src_l = merge_hand_results(holistic_results.left_hand_landmarks,  ded_left)
        right_lm, src_r = merge_hand_results(holistic_results.right_hand_landmarks, ded_right)

        # ---- Cache management ----
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

        # Use cache when both detectors fail within the hold window
        if left_lm is None and frames_since_left <= HAND_HOLD_FRAMES:
            left_lm = cached_left
            src_l   = f"CACHE({frames_since_left}f)"

        if right_lm is None and frames_since_right <= HAND_HOLD_FRAMES:
            right_lm = cached_right
            src_r    = f"CACHE({frames_since_right}f)"

        if src_l is None: src_l = "LOST"
        if src_r is None: src_r = "LOST"

        # ---- Draw everything ----
        draw_all_landmarks(frame, holistic_results, left_lm, right_lm)

        # ---- Labels ----
        def label_color(src):
            if "LIVE"   in src: return (0, 255, 0)
            if "DEDCTD" in src: return (255, 180, 0)
            if "CACHE"  in src: return (100, 180, 255)
            return (0, 0, 255)  # LOST

        cv2.putText(frame, f"L: {src_l}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_color(src_l), 2)
        cv2.putText(frame, f"R: {src_r}", (10, 56),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, label_color(src_r), 2)

        # Legend
        cv2.putText(frame, "Pose",   (10, height - 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),   1)
        cv2.putText(frame, "Hands",  (10, height - 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 80, 0),  1)
        cv2.putText(frame, "Face",   (10, height - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 0, 255), 1)
        cv2.putText(frame, f"Frame {frame_idx}/{total}", (10, height - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        out.write(frame)

    cap.release()
    out.release()
    print(f"  [DONE] {frame_idx} frames -> {output_path}")


# ====== WALK THROUGH ALL SUBFOLDERS ======
processed = 0
skipped   = 0

for root, dirs, files in os.walk(INPUT_ROOT):
    for file in files:
        if not file.endswith(".mp4"):
            continue

        video_path      = os.path.join(root, file)
        relative_path   = os.path.relpath(root, INPUT_ROOT)
        output_dir      = os.path.join(OUTPUT_ROOT, relative_path)
        os.makedirs(output_dir, exist_ok=True)

        filename_no_ext = os.path.splitext(file)[0]
        output_path     = os.path.join(output_dir, f"{filename_no_ext}_holistic.mp4")

        if os.path.exists(output_path):
            print(f"  [SKIP] Already exists: {output_path}")
            skipped += 1
            continue

        print(f"Processing: {video_path}")
        create_holistic_video(video_path, output_path)
        processed += 1

holistic.close()
hands_detector.close()
print(f"\nDone. {processed} video(s) processed, {skipped} skipped.")