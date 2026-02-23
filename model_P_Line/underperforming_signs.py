# Code is almost ready!!! I think....

"""
Targeted Data Collection Script for Underperforming Signs
Includes completeness validation to ensure 30x30 frames are captured before uploading.
"""
import cv2
import numpy as np
import os
import time
import shutil
import mediapipe as mp

# Import configuration
from config import no_sequences, sequence_length, get_demo_video_path, ACTIVE_WEEK, PROJECT_ROOT_ID, ACTIONS

# Import Google Drive upload helpers
from upload_data import get_drive_service, create_or_get_contributor_folder, upload_zip_folder, zip_mp_data, verify_upload


# ISOLATED RETAKE CONFIGURATION

RETAKE_DATA_PATH = os.path.join('MP_Data_Retakes')


# Mediapipe setup

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
    mp_drawing.draw_landmarks(image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS, 
                            mp_drawing.DrawingSpec(color=(80,110,10), thickness=1, circle_radius=1), 
                            mp_drawing.DrawingSpec(color=(80,256,121), thickness=1, circle_radius=1)) 
    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
                            mp_drawing.DrawingSpec(color=(80,22,10), thickness=2, circle_radius=4), 
                            mp_drawing.DrawingSpec(color=(80,44,121), thickness=2, circle_radius=2)) 
    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                            mp_drawing.DrawingSpec(color=(121,22,76), thickness=2, circle_radius=4), 
                            mp_drawing.DrawingSpec(color=(121,44,250), thickness=2, circle_radius=2)) 
    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS, 
                            mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=4), 
                            mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)) 

def extract_keypoints(results):
    pose = np.array([[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]).flatten() if results.pose_landmarks else np.zeros(33*4)
    face = np.array([[res.x, res.y, res.z] for res in results.face_landmarks.landmark]).flatten() if results.face_landmarks else np.zeros(468*3)
    lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten() if results.left_hand_landmarks else np.zeros(21*3)
    rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten() if results.right_hand_landmarks else np.zeros(21*3)
    return np.concatenate([pose, face, lh, rh])

def get_demo_frame(demo_cap, target_height):
    if demo_cap is None or not demo_cap.isOpened(): return None
    ret, demo_frame = demo_cap.read()
    if not ret:
        demo_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, demo_frame = demo_cap.read()
        if not ret: return None

    demo_h, demo_w = demo_frame.shape[:2]
    aspect_ratio = demo_w / demo_h
    demo_target_height = int(target_height * 0.4)
    new_width = int(demo_target_height * aspect_ratio)
    return cv2.resize(demo_frame, (new_width, demo_target_height))

def combine_frames(camera_frame, demo_frame):
    if demo_frame is None: return camera_frame
    cam_h, cam_w = camera_frame.shape[:2]
    demo_h, demo_w = demo_frame.shape[:2]
    total_width = cam_w + demo_w
    combined = np.zeros((cam_h, total_width, 3), dtype=np.uint8)
    combined[0:cam_h, 0:cam_w] = camera_frame
    combined[0:demo_h, cam_w:cam_w+demo_w] = demo_frame
    cv2.rectangle(combined, (cam_w, 0), (cam_w + demo_w, demo_h), (0, 255, 0), 2)
    cv2.putText(combined, 'DEMO', (cam_w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
    return combined


# VALIDATION LOGIC - Only upload complete signs

def are_retakes_complete(data_path, target_signs):
    """
    Check if all targeted retake signs have been completely collected.
    Validates exactly 30 sequence folders containing 30 frames each.
    """
    if not os.path.exists(data_path):
        print(f"Data path does not exist: {data_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"VALIDATING RETAKE DATA COMPLETENESS")
    print(f"Expected: {len(target_signs)} signs × {no_sequences} videos × {sequence_length} frames")
    print(f"{'='*60}")
    
    incomplete_signs = []
    
    for sign in target_signs:
        sign_path = os.path.join(data_path, sign)
        
        if not os.path.exists(sign_path):
            print(f"'{sign}': Folder missing")
            incomplete_signs.append(sign)
            continue
            
        all_folders = [f for f in os.listdir(sign_path) if os.path.isdir(os.path.join(sign_path, f))]
        
        sequence_folders = {}
        for folder in all_folders:
            if '_' in folder:
                try:
                    seq_num = int(folder.split('_')[-1])
                    sequence_folders[seq_num] = folder
                except ValueError:
                    continue
                    
        if len(sequence_folders) != no_sequences:
            print(f"'{sign}': Expected {no_sequences} videos, found {len(sequence_folders)}")
            incomplete_signs.append(sign)
            continue
            
        missing_sequences = []
        incomplete_sequences = []
        
        for seq_num in range(no_sequences):
            if seq_num not in sequence_folders:
                missing_sequences.append(seq_num)
                continue
                
            folder_name = sequence_folders[seq_num]
            seq_path = os.path.join(sign_path, folder_name)
            npy_files = [f for f in os.listdir(seq_path) if f.endswith('.npy')]
            
            if len(npy_files) != sequence_length:
                incomplete_sequences.append(f"seq_{seq_num} ({len(npy_files)}/{sequence_length} frames)")
                
        if missing_sequences or incomplete_sequences:
            status = f"'{sign}': "
            if missing_sequences:
                status += f"{len(missing_sequences)} missing videos, "
            if incomplete_sequences:
                status += f"{len(incomplete_sequences)} incomplete videos"
            print(status)
            incomplete_signs.append(sign)
        else:
            print(f"'{sign}': Complete ({no_sequences} videos × {sequence_length} frames)")
            
    print(f"{'='*60}")
    
    if incomplete_signs:
        print(f"INCOMPLETE: {len(incomplete_signs)}/{len(target_signs)} signs need work")
        print(f"Incomplete signs: {', '.join(incomplete_signs)}")
        print(f"{'='*60}")
        return False
    else:
        print(f"COMPLETE: All {len(target_signs)} targeted signs ready for upload!")
        print(f"{'='*60}")
        return True


def main():
    print("="*50)
    print("TARGETED SIGN RETAKE SCRIPT (CLOUD SYNCED)")
    print("="*50)

    user_name = input("Enter your Email/ID: ").strip().replace(" ", "_")
    if not user_name:
        print("Error: Name/Email is required.")
        return

    tagged_user_name = f"{user_name}_RETAKES"

    # Create a list of valid lowercased signs for comparison
    valid_signs = [action.lower() for action in ACTIONS]

    while True:
        print("\nEnter the signs you want to retake, separated by commas.")
        print(f"Available signs for {ACTIVE_WEEK}: {valid_signs}")
        raw_input = input("Target Signs: ").strip()
        
        if not raw_input:
            print("No signs entered. Exiting.")
            return

        # Parse and clean the input list
        target_actions = [sign.strip().lower() for sign in raw_input.split(',')]
        
        # Check for any typos or signs not in the active week
        invalid_signs = [sign for sign in target_actions if sign not in valid_signs]
        
        if invalid_signs:
            print(f"\n ERROR: The following signs are NOT in your active week: {invalid_signs}")
            print("Please check your spelling and try again.")
        else:
            print(f"\n Queued {len(target_actions)} valid signs for retake: {target_actions}")
            break

    if not os.path.exists(RETAKE_DATA_PATH):
        os.makedirs(RETAKE_DATA_PATH)

    cap = cv2.VideoCapture(0)
    cv2.namedWindow('SASL Targeted Retake', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('SASL Targeted Retake', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    should_quit = False

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=2) as holistic:
        for action_index, action in enumerate(target_actions):
            if should_quit: break
            
            action_path = os.path.join(RETAKE_DATA_PATH, action)
            if os.path.exists(action_path):
                print(f"\nWARNING: Previous local retake data found for '{action}'.")
                choice = input(f"Delete old retake data for '{action}' before starting? (y/n): ").strip().lower()
                if choice == 'y':
                    shutil.rmtree(action_path)
                    print(f"Deleted old retake data for '{action}'.")

            if not os.path.exists(action_path):
                os.makedirs(action_path)

            demo_video_path = get_demo_video_path(action)
            demo_cap = cv2.VideoCapture(demo_video_path) if demo_video_path else None

            retake_sign = True
            skip_sign = False

            while retake_sign:
                if should_quit: break

                while True:
                    ret, frame = cap.read()
                    if not ret: break

                    image, results = mediapipe_detection(frame, holistic)
                    draw_styled_landmarks(image, results)
                    demo_frame = get_demo_frame(demo_cap, image.shape[0])
                    combined_frame = combine_frames(image, demo_frame)

                    h, w = combined_frame.shape[:2]
                    cv2.putText(combined_frame, f'RETAKING: {action.upper()}', (w//2 - 200, h//2 - 150),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press SPACE to start recording', (w//2 - 280, h//2 + 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.putText(combined_frame, 'Press S to skip this sign', (w//2 - 230, h//2 + 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 2, cv2.LINE_AA)

                    cv2.imshow('SASL Targeted Retake', combined_frame)

                    key = cv2.waitKey(10)
                    if key == 32: break
                    if key in [ord('s'), ord('S')]: 
                        skip_sign = True
                        retake_sign = False
                        break
                    if key == ord('q'): 
                        should_quit = True
                        break

                if skip_sign or should_quit: break

                for sequence in range(no_sequences):
                    if should_quit: break

                    folder_name = f"{tagged_user_name}_{sequence}"
                    sequence_path = os.path.join(action_path, folder_name)
                    if not os.path.exists(sequence_path): os.makedirs(sequence_path)

                    if sequence > 0:
                        for countdown in range(3, 0, -1):
                            start_time = time.time()
                            while time.time() - start_time < 1.0:
                                ret, frame = cap.read()
                                image, results = mediapipe_detection(frame, holistic)
                                draw_styled_landmarks(image, results)
                                demo_frame = get_demo_frame(demo_cap, image.shape[0])
                                combined_frame = combine_frames(image, demo_frame)
                                h, w = combined_frame.shape[:2]
                                
                                cv2.putText(combined_frame, f'Starting in {countdown}...', (w//2 - 180, h//2 + 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4, cv2.LINE_AA)
                                cv2.imshow('SASL Targeted Retake', combined_frame)
                                if cv2.waitKey(10) & 0xFF == ord('q'):
                                    should_quit = True
                                    break

                    for frame_num in range(sequence_length):
                        ret, frame = cap.read()
                        if not ret: break

                        image, results = mediapipe_detection(frame, holistic)
                        draw_styled_landmarks(image, results)
                        demo_frame = get_demo_frame(demo_cap, image.shape[0])
                        combined_frame = combine_frames(image, demo_frame)

                        cv2.putText(combined_frame, f'RECORDING: {action.upper()}', (50, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                        cv2.imshow('SASL Targeted Retake', combined_frame)

                        keypoints = extract_keypoints(results)
                        np.save(os.path.join(sequence_path, str(frame_num)), keypoints)
                        time.sleep(0.067)

                        if cv2.waitKey(10) & 0xFF == ord('q'):
                            should_quit = True
                            break

                if not should_quit:
                    while True:
                        ret, frame = cap.read()
                        image, results = mediapipe_detection(frame, holistic)
                        draw_styled_landmarks(image, results)
                        combined_frame = combine_frames(image, get_demo_frame(demo_cap, image.shape[0]))
                        h, w = combined_frame.shape[:2]
                        
                        cv2.putText(combined_frame, 'Happy with this retake?', (w//2 - 280, h//2 + 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 0), 2, cv2.LINE_AA)
                        cv2.putText(combined_frame, 'Press BACKSPACE to retake', (w//2 - 250, h//2 + 100),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                        cv2.putText(combined_frame, 'Press any other key to continue', (w//2 - 280, h//2 + 150),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                        cv2.imshow('SASL Targeted Retake', combined_frame)
                        
                        key = cv2.waitKey(10)
                        if key == 8: 
                            shutil.rmtree(action_path)
                            retake_sign = True
                            break
                        elif key != -1:
                            retake_sign = False
                            break

            if demo_cap: demo_cap.release()

    cap.release()
    cv2.destroyAllWindows()


    # Google drive upload

    if are_retakes_complete(RETAKE_DATA_PATH, target_actions):
        print("\n" + "="*50)
        print("INITIATING CLOUD UPLOAD FOR RETAKES")
        print("="*50)

        try:
            print("Authenticating with Google Drive...")
            service = get_drive_service()   
            
            print(f"Routing to folder for {ACTIVE_WEEK}...")
            weekly_folder_id = create_or_get_contributor_folder(service, PROJECT_ROOT_ID, ACTIVE_WEEK)

            zip_output = f"{tagged_user_name}.zip"
            print(f"Zipping targeted data to {zip_output}...")
            
            zip_file_path = zip_mp_data(RETAKE_DATA_PATH, zip_output, target_actions, folder_name=tagged_user_name) 
            
            print(f"Uploading to Google Drive...")
            file_id = upload_zip_folder(service, zip_file_path, weekly_folder_id) 
            
            if file_id:
                print(f"\n Success! Uploaded with ID: {file_id}")
                
                if verify_upload(service, file_id, zip_file_path):
                    print(" Upload verified successfully!")
                    
                    try:
                        os.remove(zip_file_path)
                    except Exception as e:
                        print(f" Could not delete zip: {e}")

                    print("\nYour targeted data is safe in the cloud and still available locally in 'MP_Data_Retakes' for immediate model training.")
                else:
                    print(f" Upload verification failed. The zip file '{zip_file_path}' has been kept safe locally.")
            else:
                print(f" Upload failed. Files kept safe locally.")
            
        except Exception as e:
            print(f" Automation Error: {e}")
            print("Data was saved locally in 'MP_Data_Retakes' but failed to upload.")
    else:
        print("\n Upload aborted. Please complete all requested retakes to ensure data integrity.")

if __name__ == '__main__':
    main()