"""
Distributed Data Collection Script for WeThinkCode_ Sign Language Project
Updates:
  - Adds User ID to prevent cloud storage overwrites
  - Full screen video display
  - Space key to start/continue recording
  - Review and retake option after each sign
  - Backspace to retake, any other key to continue
  - Demonstration video shown alongside camera feed
  - Skip functionality: Start from any sign number or skip individual signs
  - Press 'S' during instruction screen to skip current sign
  - Zipping of collected data for easier upload when all signs for the week are complete
"""
import cv2
import numpy as np
import os
import sys
import time
import shutil
import zipfile
from googleapiclient.errors import HttpError

# --------------------------------------------------------------------------
# IMPORT CONFIGURATION (Connects to config.py)
# --------------------------------------------------------------------------
# We import variables directly so you don't have to edit this file ever again.
from config import ACTIONS, DATA_PATH, no_sequences, sequence_length, VOCAB_SCHEDULE, ACTIVE_WEEK, get_demo_video_path
from upload_data import get_drive_service, create_or_get_contributor_folder, upload_zip_folder, zip_mp_data

# --------------------------------------------------------------------------
# MEDIAPIPE SETUP
# --------------------------------------------------------------------------
import mediapipe as mp
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils

def mediapipe_detection(image, model):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = model.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return image, results

def draw_styled_landmarks(image, results):
    # Draw face connections
    mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS, 
                             mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1), 
                             mp_drawing.DrawingSpec(color=(80,256,121), thickness=1, circle_radius=1)) 
    # Draw pose connections
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                             mp_drawing.DrawingSpec(color=(80,22,10), thickness=2, circle_radius=4), 
                             mp_drawing.DrawingSpec(color=(80,44,121), thickness=2, circle_radius=2)) 
    # Draw left hand connections
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                             mp_drawing.DrawingSpec(color=(121,22,76), thickness=2, circle_radius=4), 
                             mp_drawing.DrawingSpec(color=(121,44,250), thickness=2, circle_radius=2)) 
    # Draw right hand connections  
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                             mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4), 
                             mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)) 

def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
    face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468*3)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*3)
    return np.concatenate([pose, face, lh, rh])

# --------------------------------------------------------------------------
# DEMONSTRATION VIDEO HELPER
# --------------------------------------------------------------------------
def get_demo_frame(demo_cap, target_height):
    """
    Get the next frame from the demonstration video.
    Loops the video when it reaches the end.
    Resizes to be smaller (40% of target height) while maintaining aspect ratio.

    Args:
        demo_cap: cv2.VideoCapture object for the demo video
        target_height: Height of the camera frame (demo will be 40% of this)

    Returns:
        Resized demo frame, or None if video can't be read
    """
    if demo_cap is None or not demo_cap.isOpened():
        return None

    ret, demo_frame = demo_cap.read()

    # If video ended, loop back to start
    if not ret:
        demo_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, demo_frame = demo_cap.read()
        if not ret:
            return None

    # Resize demo frame to be smaller (40% of camera height) while maintaining aspect ratio
    demo_h, demo_w = demo_frame.shape[:2]
    aspect_ratio = demo_w / demo_h

    # Make demo video 40% of the camera height
    demo_target_height = int(target_height * 0.4)
    new_width = int(demo_target_height * aspect_ratio)
    demo_frame_resized = cv2.resize(demo_frame, (new_width, demo_target_height))

    return demo_frame_resized

def combine_frames(camera_frame, demo_frame):
    """
    Combine camera frame and demo frame side by side.
    Camera frame is large (main focus), demo frame is smaller (reference).

    Args:
        camera_frame: The webcam frame with MediaPipe landmarks (LARGE)
        demo_frame: The demonstration video frame (SMALL - 40% height)

    Returns:
        Combined frame with camera on left (large), demo on right (small)
    """
    if demo_frame is None:
        # If no demo video, just return camera frame
        return camera_frame

    cam_h, cam_w = camera_frame.shape[:2]
    demo_h, demo_w = demo_frame.shape[:2]

    # Create a blank space on the right side of the camera frame
    # The demo video will be placed in the top-right corner

    # Calculate total width (camera + demo)
    total_width = cam_w + demo_w

    # Create a black canvas with the total width and camera height
    combined = np.zeros((cam_h, total_width, 3), dtype=np.uint8)

    # Place camera frame on the left (full height)
    combined[0:cam_h, 0:cam_w] = camera_frame

    # Place demo frame on the right (top-aligned, smaller)
    combined[0:demo_h, cam_w:cam_w+demo_w] = demo_frame

    # Add a border around the demo video to make it stand out
    cv2.rectangle(combined, (cam_w, 0), (cam_w + demo_w, demo_h), (0, 255, 0), 2)

    # Add label above demo video
    cv2.putText(combined, 'DEMO', (cam_w + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

    return combined

def is_week_complete(mp_data_path, vocab, active_week):
    """
    Check if all signs for the active week have been collected.

    Args:
        mp_data_path: Path to the MP_Data directory
        vocab: List of signs for the active week"""
    if not os.path.exists(mp_data_path):
        return False
    recorded = [d for d in os.listdir(mp_data_path) if os.path.isdir(os.path.join(mp_data_path, d))]

    return True if len(recorded) >= len(vocab[active_week]) else False
    
    

# --------------------------------------------------------------------------
# MAIN LOGIC
# --------------------------------------------------------------------------
def main():
    # 1. GET USER ID (CRITICAL FOR TEAMWORK)
    print("="*50)
    print("WETHINKCODE_ SIGN LANGUAGE COLLECTOR")
    print(f"TARGET WORDS: {ACTIONS}") # Show user what they are recording
    print("="*50)

    user_name = input("Enter your Email (e.g., tumomogame9@gmail.com): ").strip().replace(" ", "_")
    if not user_name:
        print("Error: Name is required to prevent data overwrites!")
        return

    # 2. ASK USER WHICH SIGN TO START FROM
    print("\n" + "="*50)
    print("SIGN LIST:")
    for idx, action in enumerate(ACTIONS):
        print(f"  {idx + 1}. {action}")
    print("="*50)

    start_from = input("\nEnter the sign number to start from (press Enter to start from 1): ").strip()

    if start_from == "":
        start_index = 0
    else:
        try:
            start_index = int(start_from) - 1  # Convert to 0-based index
            if start_index < 0 or start_index >= len(ACTIONS):
                print(f"Error: Please enter a number between 1 and {len(ACTIONS)}")
                return
        except ValueError:
            print("Error: Please enter a valid number")
            return

    print(f"\n✅ Starting from sign #{start_index + 1}: {ACTIONS[start_index]}")
    if start_index > 0:
        print(f"   (Skipping {start_index} sign(s))")

    # Create base directory
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot access webcam.")
        return

    # Set full screen window
    cv2.namedWindow('SASL Data Collection', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('SASL Data Collection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Set mediapipe model
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=2) as holistic:

        # Loop through actions (Pulled from config.py) - starting from user's choice
        for action_index, action in enumerate(ACTIONS[start_index:], start=start_index):
            print(f"\n--- PREPARING FOR ACTION #{action_index + 1}: {action} ---")

            # Load demonstration video for this action
            demo_video_path = get_demo_video_path(action)
            demo_cap = None

            if demo_video_path:
                demo_cap = cv2.VideoCapture(demo_video_path)
                if demo_cap.isOpened():
                    print(f"✅ Loaded demonstration video: {demo_video_path}")
                else:
                    print(f"⚠️  Could not open demonstration video: {demo_video_path}")
                    demo_cap = None
            else:
                print(f"⚠️  No demonstration video found for '{action}'")

            # Flag to control retake and skip
            retake_sign = True
            skip_sign = False

            while retake_sign:
                # Create action folder (MP_Data/hello)
                action_path = os.path.join(DATA_PATH, action)
                if not os.path.exists(action_path):
                    os.makedirs(action_path)

                # Show initial instruction screen for this sign
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Make detections for live preview
                    image, results = mediapipe_detection(frame, holistic)
                    draw_styled_landmarks(image, results)

                    # Get demo frame if available
                    demo_frame = get_demo_frame(demo_cap, image.shape[0])

                    # Combine camera and demo frames
                    combined_frame = combine_frames(image, demo_frame)

                    # Get screen dimensions for centering text
                    h, w = combined_frame.shape[:2]

                    # Show instruction screen with sign number
                    cv2.putText(combined_frame, f'SIGN #{action_index + 1}/{len(ACTIONS)}: {action.upper()}', (w//2 - 300, h//2 - 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3, cv2.LINE_AA)
                    cv2.putText(combined_frame, f'You will record {no_sequences} videos', (w//2 - 250, h//2 - 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press SPACE to start recording', (w//2 - 280, h//2 + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press S to skip this sign', (w//2 - 230, h//2 + 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press Q to quit', (w//2 - 150, h//2 + 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2, cv2.LINE_AA)

                    # Add labels for demo and camera sections
                    if demo_frame is not None:
                        cv2.putText(combined_frame, 'DEMONSTRATION', (50, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
                        demo_w = demo_frame.shape[1]
                        cv2.putText(combined_frame, 'YOUR CAMERA', (demo_w + 50, 50),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)

                    cv2.imshow('SASL Data Collection', combined_frame)

                    key = cv2.waitKey(10)
                    if key == 32:  # SPACE bar
                        break
                    if key == ord('s') or key == ord('S'):  # S key to skip
                        print(f"⏭️  Skipping sign '{action}'...")
                        skip_sign = True
                        retake_sign = False
                        break
                    if key == ord('q'):
                        cap.release()
                        if demo_cap:
                            demo_cap.release()
                        cv2.destroyAllWindows()
                        sys.exit()

                # If user chose to skip, break out of retake loop
                if skip_sign:
                    break

                # Only record if not skipping
                # Loop through sequences (videos)
                for sequence in range(no_sequences):

                    # 2. CREATE UNIQUE FOLDER NAME: User_Sequence (e.g., Thabo_0)
                    folder_name = f"{user_name}_{sequence}"
                    sequence_path = os.path.join(action_path, folder_name)

                    # Create the specific folder for this video
                    if not os.path.exists(sequence_path):
                        os.makedirs(sequence_path)

                    # Countdown between videos (3 seconds)
                    if sequence > 0:  # Don't countdown before first sequence (already waited above)
                        for countdown in range(3, 0, -1):
                            # Record start time for this countdown second
                            start_time = time.time()

                            # Keep updating the display for 1 second to keep demo video smooth
                            while time.time() - start_time < 1.0:
                                ret, frame = cap.read()
                                if not ret:
                                    break

                                image, results = mediapipe_detection(frame, holistic)
                                draw_styled_landmarks(image, results)

                                # Get demo frame and combine
                                demo_frame = get_demo_frame(demo_cap, image.shape[0])
                                combined_frame = combine_frames(image, demo_frame)

                                h, w = combined_frame.shape[:2]

                                # Show countdown
                                cv2.putText(combined_frame, f'SIGN: {action.upper()}', (w//2 - 200, h//2 - 150),
                                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4, cv2.LINE_AA)
                                cv2.putText(combined_frame, f'Video {sequence + 1} of {no_sequences}', (w//2 - 200, h//2 - 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                                cv2.putText(combined_frame, f'Starting in {countdown}...', (w//2 - 180, h//2 + 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4, cv2.LINE_AA)
                                cv2.putText(combined_frame, 'Get ready!', (w//2 - 120, h//2 + 130),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3, cv2.LINE_AA)

                                cv2.imshow('SASL Data Collection', combined_frame)

                                # Check for quit during countdown (short wait to keep video smooth)
                                if cv2.waitKey(10) & 0xFF == ord('q'):
                                    cap.release()
                                    if demo_cap:
                                        demo_cap.release()
                                    cv2.destroyAllWindows()
                                    sys.exit()

                    # Loop through video length (sequence_length)
                    for frame_num in range(sequence_length):

                        # Read feed
                        ret, frame = cap.read()
                        if not ret:
                            break

                        # Make detections
                        image, results = mediapipe_detection(frame, holistic)
                        draw_styled_landmarks(image, results)

                        # Get demo frame and combine
                        demo_frame = get_demo_frame(demo_cap, image.shape[0])
                        combined_frame = combine_frames(image, demo_frame)

                        h, w = combined_frame.shape[:2]

                        # RECORDING FEEDBACK
                        cv2.putText(combined_frame, f'RECORDING: {action.upper()}', (50, 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                        cv2.putText(combined_frame, f'Video {sequence + 1}/{no_sequences} | Frame {frame_num + 1}/{sequence_length}', (50, 100),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                        # Show to screen
                        cv2.imshow('SASL Data Collection', combined_frame)

                        # Export keypoints
                        keypoints = extract_keypoints(results)
                        npy_path = os.path.join(sequence_path, str(frame_num))
                        np.save(npy_path, keypoints)

                        # Add a small delay to slow down recording (100ms = 10 fps)
                        # This gives users more time to perform the sign properly
                        time.sleep(0.1)  # 100 milliseconds delay

                        # Break gracefully
                        if cv2.waitKey(10) & 0xFF == ord('q'):
                            cap.release()
                            if demo_cap:
                                demo_cap.release()
                            cv2.destroyAllWindows()
                            sys.exit()

                # After all sequences for this sign, ask if happy
                print(f"\n✅ Completed all {no_sequences} videos for '{action}'")

                happy_with_videos = False
                while not happy_with_videos:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    image, results = mediapipe_detection(frame, holistic)
                    draw_styled_landmarks(image, results)

                    # Get demo frame and combine
                    demo_frame = get_demo_frame(demo_cap, image.shape[0])
                    combined_frame = combine_frames(image, demo_frame)

                    h, w = combined_frame.shape[:2]

                    # Review screen
                    cv2.putText(combined_frame, f'COMPLETED: {action.upper()}', (w//2 - 250, h//2 - 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4, cv2.LINE_AA)
                    cv2.putText(combined_frame, f'Recorded {no_sequences} videos', (w//2 - 200, h//2 - 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Are you happy with these videos?', (w//2 - 280, h//2 + 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press BACKSPACE to retake', (w//2 - 250, h//2 + 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press any other key to continue', (w//2 - 280, h//2 + 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    cv2.imshow('SASL Data Collection', combined_frame)

                    key = cv2.waitKey(10)
                    if key == 8:  # BACKSPACE
                        print(f"🔄 Retaking videos for '{action}'...")
                        # Delete all videos for this sign
                        if os.path.exists(action_path):
                            shutil.rmtree(action_path)
                            print(f"   Deleted previous recordings for '{action}'")
                        retake_sign = True
                        happy_with_videos = True  # Exit this loop to restart sign
                        break
                    elif key != -1:  # Any other key pressed
                        print(f"✅ Keeping videos for '{action}'. Moving to next sign...")
                        retake_sign = False
                        happy_with_videos = True
                        break

            # Release demo video capture for this action
            if demo_cap:
                demo_cap.release()
                print(f"✅ Released demonstration video for '{action}'")

    cap.release()
    cv2.destroyAllWindows()
    print("\nSUCCESS! All data collected.")

    # Check if all signs for the active week are collected
    mp_data_path = DATA_PATH

    # If complete, zip the folder for easier upload
    if is_week_complete(DATA_PATH, VOCAB_SCHEDULE, ACTIVE_WEEK):
        try:
            print("Authenticating with Google Drive...")
            service = get_drive_service()  
            
            # The ID of the main folder where everyone's work goes
            parent_folder_id = '1xOUyOz1fiRocPXLqkjHCBaXtEreVTGt3' 

            # logic change: We use 'user_name' from the top of THIS script
            print(f"Creating/getting folder for {user_name}...")
            contributor_folder_id = create_or_get_contributor_folder(service, parent_folder_id, user_name)

            # Zip the data (DATA_PATH is defined in config.py)
            zip_output = f"{ACTIVE_WEEK}_{user_name}.zip"
            print(f"Zipping data to {zip_output}...")
            zip_file_path = zip_mp_data(DATA_PATH, zip_output) 
            
            # Upload (using the IDs we just generated)
            print(f"Uploading to Google Drive...")
            file_id = upload_zip_folder(service, zip_file_path, contributor_folder_id) 
            
            if file_id:
                print(f"\n✅ Success! Uploaded with ID: {file_id}")
            
        except Exception as e:
            print(f"❌ Automation Error: {e}")
    else:
        print(f"\n⚠️ Week {ACTIVE_WEEK} incomplete. Finish all signs to trigger upload.")

if __name__ == '__main__':
    main()