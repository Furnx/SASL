"""
Distributed Data Collection Script for WeThinkCode_ Sign Language Project
Updates:
  - Adds User ID to prevent cloud storage overwrites
  - Full screen video display
  - Space key to start/continue recording
  - Review and retake option after each sign
  - Backspace to retake, any other key to continue
"""
import cv2
import numpy as np
import os
import sys
import time
import shutil

# --------------------------------------------------------------------------
# IMPORT CONFIGURATION (Connects to config.py)
# --------------------------------------------------------------------------
# We import variables directly so you don't have to edit this file ever again.
from config import ACTIONS, DATA_PATH, no_sequences, sequence_length

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
# MAIN LOGIC
# --------------------------------------------------------------------------
def main():
    # 1. GET USER ID (CRITICAL FOR TEAMWORK)
    print("="*50)
    print("WETHINKCODE_ SIGN LANGUAGE COLLECTOR")
    print(f"TARGET WORDS: {ACTIONS}") # Show user what they are recording
    print("="*50)
    
    user_name = input("Enter your First Name (e.g., Thabo): ").strip().replace(" ", "_")
    if not user_name:
        print("Error: Name is required to prevent data overwrites!")
        return

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
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:

        # Loop through actions (Pulled from config.py)
        for action in ACTIONS:
            print(f"\n--- PREPARING FOR ACTION: {action} ---")

            # Flag to control retake
            retake_sign = True

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

                    # Get screen dimensions for centering text
                    h, w = image.shape[:2]

                    # Show instruction screen
                    cv2.putText(image, f'SIGN: {action.upper()}', (w//2 - 200, h//2 - 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4, cv2.LINE_AA)
                    cv2.putText(image, f'You will record {no_sequences} videos', (w//2 - 250, h//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Press SPACE to start recording', (w//2 - 280, h//2 + 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Press Q to quit', (w//2 - 150, h//2 + 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2, cv2.LINE_AA)

                    cv2.imshow('SASL Data Collection', image)

                    key = cv2.waitKey(10)
                    if key == 32:  # SPACE bar
                        break
                    if key == ord('q'):
                        cap.release()
                        cv2.destroyAllWindows()
                        sys.exit()

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
                            ret, frame = cap.read()
                            if not ret:
                                break

                            image, results = mediapipe_detection(frame, holistic)
                            draw_styled_landmarks(image, results)

                            h, w = image.shape[:2]

                            # Show countdown
                            cv2.putText(image, f'SIGN: {action.upper()}', (w//2 - 200, h//2 - 150),
                                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4, cv2.LINE_AA)
                            cv2.putText(image, f'Video {sequence + 1} of {no_sequences}', (w//2 - 200, h//2 - 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                            cv2.putText(image, f'Starting in {countdown}...', (w//2 - 180, h//2 + 50),
                                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4, cv2.LINE_AA)
                            cv2.putText(image, 'Get ready!', (w//2 - 120, h//2 + 130),
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3, cv2.LINE_AA)

                            cv2.imshow('SASL Data Collection', image)

                            # Check for quit during countdown
                            if cv2.waitKey(1000) & 0xFF == ord('q'):
                                cap.release()
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

                        h, w = image.shape[:2]

                        # RECORDING FEEDBACK
                        cv2.putText(image, f'RECORDING: {action.upper()}', (50, 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                        cv2.putText(image, f'Video {sequence + 1}/{no_sequences} | Frame {frame_num + 1}/{sequence_length}', (50, 100),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                        # Show to screen
                        cv2.imshow('SASL Data Collection', image)

                        # Export keypoints
                        keypoints = extract_keypoints(results)
                        npy_path = os.path.join(sequence_path, str(frame_num))
                        np.save(npy_path, keypoints)

                        # Break gracefully
                        if cv2.waitKey(10) & 0xFF == ord('q'):
                            cap.release()
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

                    h, w = image.shape[:2]

                    # Review screen
                    cv2.putText(image, f'COMPLETED: {action.upper()}', (w//2 - 250, h//2 - 120),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4, cv2.LINE_AA)
                    cv2.putText(image, f'Recorded {no_sequences} videos', (w//2 - 200, h//2 - 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Are you happy with these videos?', (w//2 - 280, h//2 + 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Press BACKSPACE to retake', (w//2 - 250, h//2 + 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.putText(image, 'Press any other key to continue', (w//2 - 280, h//2 + 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                    cv2.imshow('SASL Data Collection', image)

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

    cap.release()
    cv2.destroyAllWindows()
    print("\nSUCCESS! All data collected.")
    print(f"Please upload the folder '{DATA_PATH}' to Google Drive.")

if __name__ == '__main__':
    main()