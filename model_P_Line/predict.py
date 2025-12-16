"""
Real-time Prediction Script for WeThinkCode_ SASL Project
Updates:
  - Shows only TOP 5 probabilities (cleaner UI)
  - Self-contained MediaPipe logic (no external utils needed)
  - Checks for Model/Config mismatches
"""

import cv2
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras.models import load_model

# Import configuration
from config import (
    ACTIONS,
    SEQUENCE_LENGTH,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    get_model_path
)

import mediapipe as mp

# =============================================================================
# 1. MEDIAPIPE SETUP (Same as Data Collection)
# =============================================================================
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

# =============================================================================
# 2. VISUALIZATION FUNCTIONS
# =============================================================================
def draw_probability_bars(image, res, actions, input_frame_len, threshold=0.3):
    """
    Draws the Top 5 most likely signs to avoid cluttering the screen.
    """
    # Get top 5 indices
    top_5_indices = np.argsort(res)[-5:][::-1]
    
    y_offset = 0
    for i in top_5_indices:
        prob = res[i]
        
        # Only show if probability is somewhat significant
        if prob > 0.05:
            action_name = actions[i]
            
            # Dynamic Color (Green for high confidence, Red for low)
            if prob > threshold:
                color = (0, 255, 0) # Green
            else:
                color = (0, 0, 255) # Red

            # Draw Bar
            cv2.rectangle(image, (0, 60 + y_offset), (int(prob * 100), 90 + y_offset), color, -1)
            # Draw Text
            cv2.putText(image, f'{action_name}: {int(prob*100)}%', (5, 85 + y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
            
            y_offset += 40
            
    return image

# =============================================================================
# 3. MAIN PREDICTION LOOP
# =============================================================================
def predict():
    # 1. Validation
    model_path = get_model_path()
    if not os.path.exists(model_path):
        print(f"❌ Error: Model not found at {model_path}")
        print("   Please run 'train.py' first.")
        return

    # 2. Load Model
    print("⏳ Loading model...")
    model = load_model(model_path)
    
    # Safety Check: Does config.py match the model?
    # model.layers[-1].output_shape[1] is the number of neurons in the last layer
    model_output_shape = model.layers[-1].output_shape[1]
    config_actions_len = len(ACTIONS)
    
    if model_output_shape != config_actions_len:
        print("\n⚠️  CONFIGURATION MISMATCH DETECTED ⚠️")
        print(f"   - The loaded model knows {model_output_shape} signs.")
        print(f"   - Your config.py has {config_actions_len} signs uncommented.")
        print("   -> Please update config.py to uncomment the signs this model was trained on.")
        return

    print(f"✅ Model loaded! It knows {len(ACTIONS)} signs.")
    print("📷 Starting Camera...")

    # 3. Start Stream
    sequence = []
    sentence = []
    threshold = 0.8

    cap = cv2.VideoCapture(0)
    
    with mp_holistic.Holistic(min_detection_confidence=MIN_DETECTION_CONFIDENCE, min_tracking_confidence=MIN_TRACKING_CONFIDENCE) as holistic:
        while cap.isOpened():
            # Read feed
            ret, frame = cap.read()
            if not ret: break

            # Make detections
            image, results = mediapipe_detection(frame, holistic)
            draw_styled_landmarks(image, results)
            
            # Prediction logic
            keypoints = extract_keypoints(results)
            sequence.append(keypoints)
            sequence = sequence[-SEQUENCE_LENGTH:] # Keep last 30 frames

            if len(sequence) == SEQUENCE_LENGTH:
                # Predict
                res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
                
                # Get the best prediction
                best_class_index = np.argmax(res)
                confidence = res[best_class_index]
                predicted_sign = ACTIONS[best_class_index]

                # Visualization (Top 5 Probabilities)
                image = draw_probability_bars(image, res, ACTIONS, len(sequence))

                # Sentence Construction Logic
                if confidence > threshold:
                    if len(sentence) > 0:
                        if predicted_sign != sentence[-1]:
                            sentence.append(predicted_sign)
                    else:
                        sentence.append(predicted_sign)

                if len(sentence) > 5: 
                    sentence = sentence[-5:]

            # Draw Sentence Box
            cv2.rectangle(image, (0,0), (640, 40), (245, 117, 16), -1)
            cv2.putText(image, ' '.join(sentence), (3,30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Show to screen
            cv2.imshow('WeThinkCode_ SASL Decoder', image)

            # Break gracefully
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    predict()