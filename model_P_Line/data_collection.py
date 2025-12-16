"""
Distributed Data Collection Script for WeThinkCode_ Sign Language Project
Updates:
  - Adds User ID to prevent cloud storage overwrites
  - improved UX (Wait for Spacebar)
  - Auto-creates config if missing
"""

import cv2
import numpy as np
import os
import time
import sys

# --------------------------------------------------------------------------
# CONFIGURATION BLOCK (Self-Contained for easier sharing)
# --------------------------------------------------------------------------
# Path for exported data, numpy arrays
DATA_PATH = os.path.join('MP_Data') 

# Actions that we try to detect (Edit these for your weekly batch)
ACTIONS = np.array(['thank_you', 'thank_you', 'iloveyou'])

# Thirty videos worth of data
no_sequences = 30

# Videos are going to be 30 frames in length
sequence_length = 30

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

    # Set mediapipe model 
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        
        # Loop through actions
        for action in ACTIONS:
            print(f"\n--- PREPARING FOR ACTION: {action} ---")
            
            # Create action folder (MP_Data/hello)
            action_path = os.path.join(DATA_PATH, action)
            if not os.path.exists(action_path):
                os.makedirs(action_path)
            
            # Loop through sequences (videos)
            for sequence in range(no_sequences):
                
                # 2. CREATE UNIQUE FOLDER NAME: User_Sequence (e.g., Thabo_0)
                # This ensures Thabo_0 doesn't overwrite Sarah_0 in the cloud
                folder_name = f"{user_name}_{sequence}"
                sequence_path = os.path.join(action_path, folder_name)
                
                # Create the specific folder for this video
                if not os.path.exists(sequence_path):
                    os.makedirs(sequence_path)

                # Loop through video length (sequence_length)
                for frame_num in range(sequence_length):

                    # Read feed
                    ret, frame = cap.read()
                    if not ret: break

                    # Make detections
                    image, results = mediapipe_detection(frame, holistic)
                    draw_styled_landmarks(image, results)
                    
                    # 3. BETTER UX: WAIT LOGIC
                    if frame_num == 0:
                        while True:
                            # Show "Waiting" Screen
                            display_image = image.copy()
                            cv2.putText(display_image, f'COLLECTING: {action}', (120,200), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255, 0), 4, cv2.LINE_AA)
                            cv2.putText(display_image, f'Video {sequence+1} of {no_sequences}', (120,250), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
                            cv2.putText(display_image, 'Press "SPACE" to Record', (120,300), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)
                            
                            cv2.imshow('OpenCV Feed', display_image)
                            
                            key = cv2.waitKey(10)
                            if key == 32: # SPACE bar
                                break
                            if key == ord('q'):
                                cap.release()
                                cv2.destroyAllWindows()
                                sys.exit()

                        # Quick 1s Countdown after space press
                        cv2.putText(image, '3...', (120,200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255, 0), 4, cv2.LINE_AA)
                        cv2.imshow('OpenCV Feed', image)
                        cv2.waitKey(500)
                    
                    # RECORDING FEEDBACK
                    cv2.putText(image, f'Recording {action}: {sequence+1}/{no_sequences}', (15,12), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                    
                    # Show to screen
                    cv2.imshow('OpenCV Feed', image)

                    # Export keypoints
                    keypoints = extract_keypoints(results)
                    npy_path = os.path.join(sequence_path, str(frame_num))
                    np.save(npy_path, keypoints)

                    # Break gracefully
                    if cv2.waitKey(10) & 0xFF == ord('q'):
                        cap.release()
                        cv2.destroyAllWindows()
                        sys.exit()

    cap.release()
    cv2.destroyAllWindows()
    print("\nSUCCESS! All data collected.")
    print(f"Please upload the folder '{DATA_PATH}' to Google Drive.")

if __name__ == '__main__':
    main()