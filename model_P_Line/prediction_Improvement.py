"""
Improved Prediction Script with Movement Detection and Detailed Logging
Features:
  - Imports core prediction logic from predict.py
  - Collects 30 frames when movement is detected
  - Makes predictions continuously during movement
  - Comprehensive logging for debugging
"""

import cv2
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras.models import load_model
from datetime import datetime
import logging
import json
from pathlib import Path

# Import configuration
from config import (
    ACTIONS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    get_model_path
)

# Override sequence length for faster predictions
SEQUENCE_LENGTH = 20  # Reduced from 30 for faster predictions

# Import core functions from predict.py
from predict import (
    mediapipe_detection,
    draw_styled_landmarks,
    extract_keypoints,
    draw_probability_bars,
    mp_holistic
)

# =============================================================================
# LOGGING SETUP
# =============================================================================
def setup_logging():
    """Setup detailed logging to both file and console."""
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"prediction_improvement_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*80)
    logger.info("PREDICTION IMPROVEMENT SESSION STARTED")
    logger.info("="*80)
    
    return logger

# =============================================================================
# MOVEMENT DETECTION FUNCTIONS
# =============================================================================
def calculate_hand_movement(current_keypoints, previous_keypoints):
    """
    Calculate the amount of hand movement between two frames.
    Returns the average Euclidean distance of hand landmarks.
    """
    if previous_keypoints is None:
        return float('inf')  # First frame, assume movement
    
    # Extract hand keypoints (last 126 values: 63 for left hand, 63 for right hand)
    # Keypoint structure: [pose(132), face(1404), left_hand(63), right_hand(63)]
    current_hands = current_keypoints[-126:]
    previous_hands = previous_keypoints[-126:]
    
    # Reshape to get x, y, z coordinates
    current_hands_reshaped = current_hands.reshape(-1, 3)
    previous_hands_reshaped = previous_hands.reshape(-1, 3)
    
    # Calculate Euclidean distance for each landmark
    distances = np.linalg.norm(current_hands_reshaped - previous_hands_reshaped, axis=1)
    
    # Return average movement
    return np.mean(distances)

def is_significant_movement(movement, threshold=0.05):
    """
    Check if the movement is significant enough to warrant a prediction.
    """
    return movement > threshold

# =============================================================================
# LLM INTEGRATION FUNCTIONS
# =============================================================================
def share_prediction_with_llm(predicted_sign):
    """
    Share the predicted sign with the LLM integration script.
    """
    try:
        shared_file = Path("shared_predictions_regular.json")
        
        # Read existing data or create new
        if shared_file.exists():
            with open(shared_file, 'r') as f:
                data = json.load(f)
        else:
            data = {'predictions': []}
        
        # Add new prediction
        data['predictions'].append(predicted_sign)
        
        # Write back to file
        with open(shared_file, 'w') as f:
            json.dump(data, f)
            
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error sharing prediction with LLM: {e}")

# =============================================================================
# IMPROVED PREDICTION LOOP
# =============================================================================
def predict_improved():
    """
    Enhanced prediction with movement detection and comprehensive logging.
    """
    # Setup logging
    logger = setup_logging()
    
    # 1. Validation
    model_path = get_model_path()
    logger.info(f"Model path: {model_path}")
    
    if not os.path.exists(model_path):
        logger.error(f"Model not found at {model_path}")
        print(f"❌ Error: Model not found at {model_path}")
        print("   Please run 'train.py' first.")
        return

    # 2. Load Model
    logger.info("Loading model...")
    print("⏳ Loading model...")
    model = load_model(model_path)
    
    # Safety Check
    model_output_shape = model.output_shape[1]
    config_actions_len = len(ACTIONS)
    
    logger.info(f"Model output shape: {model_output_shape}")
    logger.info(f"Config actions count: {config_actions_len}")
    logger.info(f"Actions: {ACTIONS}")
    
    if model_output_shape != config_actions_len:
        logger.error("Configuration mismatch detected!")
        print("\n⚠️  CONFIGURATION MISMATCH DETECTED ⚠️")
        print(f"   - The loaded model knows {model_output_shape} signs.")
        print(f"   - Your config.py has {config_actions_len} signs uncommented.")
        print("   -> Please update config.py to uncomment the signs this model was trained on.")
        return

    logger.info(f"✅ Model loaded successfully! Knows {len(ACTIONS)} signs.")
    print(f"✅ Model loaded! It knows {len(ACTIONS)} signs.")
    print("📷 Starting Camera...")
    print("\n🎯 Hybrid Prediction Features:")
    print("   ✓ Maintains rolling 20-frame buffer continuously")
    print("   ✓ Only predicts during sustained movement (3+ frames)")
    print("   ✓ Handles fast sign language movements")
    print("   ✓ Prediction cooldown prevents spam")
    print("   ✓ Comprehensive logging enabled\n")

    # 3. Initialize tracking variables for hybrid approach
    rolling_buffer = []  # Always maintains 20 frames
    sentence = []
    previous_keypoints = None
    movement_history = []  # Track movement values for the rolling buffer
    
    movement_threshold = 0.02  # Threshold for detecting movement
    prediction_cooldown = 4  # Frames to wait between predictions during movement (adjusted for 20 frames)
    frames_since_prediction = 0  # Counter for prediction cooldown
    
    # Movement detection variables
    movement_detected = False
    consecutive_movement_frames = 0
    min_movement_frames = 3  # Minimum frames of movement before predicting
    
    logger.info(f"Movement threshold set to: {movement_threshold}")
    logger.info(f"Prediction cooldown set to: {prediction_cooldown} frames")
    logger.info(f"Minimum movement frames required: {min_movement_frames}")
    
    # Statistics tracking
    total_frames = 0
    frames_with_movement = 0
    total_predictions = 0
    movement_sessions = 0
    predictions_this_session = 0
    
    cap = cv2.VideoCapture(0)
    logger.info("Camera initialized")
    
    with mp_holistic.Holistic(
        min_detection_confidence=MIN_DETECTION_CONFIDENCE, 
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    ) as holistic:
        logger.info("MediaPipe Holistic initialized")
        
        while cap.isOpened():
            # Read feed
            ret, frame = cap.read()
            if not ret: 
                logger.warning("Failed to read frame from camera")
                break

            total_frames += 1
            
            # Make detections
            image, results = mediapipe_detection(frame, holistic)
            draw_styled_landmarks(image, results)
            
            # Extract keypoints
            keypoints = extract_keypoints(results)
            
            # Calculate hand movement
            movement = calculate_hand_movement(keypoints, previous_keypoints)
            previous_keypoints = keypoints.copy()
            
            # HYBRID APPROACH: Always maintain rolling buffer + movement-gated predictions
            
            # Always add frame to rolling buffer
            rolling_buffer.append(keypoints)
            rolling_buffer = rolling_buffer[-SEQUENCE_LENGTH:]  # Keep last 20 frames
            
            # Calculate hand movement
            movement = calculate_hand_movement(keypoints, previous_keypoints)
            previous_keypoints = keypoints.copy()
            
            # Track movement history for rolling buffer
            movement_history.append(movement)
            movement_history = movement_history[-SEQUENCE_LENGTH:]
            
            # Check if there's significant movement
            has_movement = is_significant_movement(movement, movement_threshold)
            frames_since_prediction += 1
            
            if has_movement:
                frames_with_movement += 1
                consecutive_movement_frames += 1
                
                # Start new movement session if needed
                if not movement_detected:
                    movement_sessions += 1
                    predictions_this_session = 0
                    movement_detected = True
                    logger.info(f"--- MOVEMENT SESSION #{movement_sessions} STARTED (Movement: {movement:.4f}) ---")
                
            else:
                # Reset movement tracking if no movement
                if consecutive_movement_frames > 0:
                    logger.info(f"--- MOVEMENT SESSION #{movement_sessions} ENDED (lasted {consecutive_movement_frames} frames) ---")
                consecutive_movement_frames = 0
                movement_detected = False
            
            # PREDICTION LOGIC: Only predict during movement with sufficient buffer and cooldown
            should_predict = (
                len(rolling_buffer) == SEQUENCE_LENGTH and  # Buffer is full
                movement_detected and  # Currently detecting movement
                consecutive_movement_frames >= min_movement_frames and  # Sustained movement
                frames_since_prediction >= prediction_cooldown  # Cooldown period passed
            )
            
            if should_predict:
                # Calculate average movement for current buffer
                avg_movement = np.mean(movement_history)
                
                # Make prediction using rolling buffer
                total_predictions += 1
                predictions_this_session += 1
                frames_since_prediction = 0  # Reset cooldown
                
                logger.info(f"Making prediction #{total_predictions} for session #{movement_sessions} ")
                logger.info(f"  Buffer movement avg: {avg_movement:.4f}, Current: {movement:.4f}")
                
                res = model.predict(np.expand_dims(rolling_buffer, axis=0), verbose=0)[0]
                
                # Get top 5 predictions
                top_5_indices = np.argsort(res)[-5:][::-1]
                
                logger.info(f"  Top 5 predictions:")
                for i, idx in enumerate(top_5_indices, 1):
                    logger.info(f"    {i}. {ACTIONS[idx]}: {res[idx]*100:.2f}%")
                
                # Get the best prediction
                best_class_index = np.argmax(res)
                confidence = res[best_class_index]
                predicted_sign = ACTIONS[best_class_index]
                
                logger.info(f"  BEST: {predicted_sign} (confidence: {confidence*100:.2f}%)")

                # Visualization (Top 5 Probabilities)
                image = draw_probability_bars(image, res, ACTIONS, len(rolling_buffer))

                # Lowered confidence threshold to 50%
                if confidence > 0.5:
                    if len(sentence) > 0:
                        if predicted_sign != sentence[-1]:
                            sentence.append(predicted_sign)
                            logger.info(f"  ✅ Added '{predicted_sign}' to sentence")
                            # Share with LLM integration
                            share_prediction_with_llm(predicted_sign)
                    else:
                        sentence.append(predicted_sign)
                        logger.info(f"  ✅ Added '{predicted_sign}' to sentence (first word)")
                        # Share with LLM integration
                        share_prediction_with_llm(predicted_sign)
                    
                    # Display confidence
                    cv2.putText(image, f'CONF: {confidence:.2f}', (450, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                else:
                    logger.info(f"  ⚠️ Confidence too low ({confidence*100:.2f}%), not adding to sentence")
                
                if len(sentence) > 5: 
                    sentence = sentence[-5:]
                    
            # Display rolling buffer info and movement status
            if len(movement_history) > 0:
                avg_mov = np.mean(movement_history)
                
                # Buffer status - always shows 20/20 when ready
                buffer_text = f'Buffer: {len(rolling_buffer)}/{SEQUENCE_LENGTH} frames'
                cv2.putText(image, buffer_text, (10, 430), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
                
                # Draw buffer status bar (always full when ready)
                bar_width = 200
                bar_height = 20
                bar_x = 10
                bar_y = 440
                progress = len(rolling_buffer) / SEQUENCE_LENGTH
                
                # Background
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
                # Progress (green when full, yellow when filling)
                color = (0, 255, 0) if len(rolling_buffer) == SEQUENCE_LENGTH else (0, 255, 255)
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), color, -1)
                # Border
                cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
                
                # Movement status and stats
                status_text = f'Session: {movement_sessions} | Movement: {"YES" if movement_detected else "NO"} | Avg: {avg_mov:.3f}'
                cv2.putText(image, status_text, (10, 475), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Movement status indicator
            if movement_detected:
                # Show movement detected with consecutive frame count
                cv2.putText(image, f'MOVEMENT DETECTED ({consecutive_movement_frames}f)', (450, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            else:
                # Show no movement
                cv2.putText(image, 'NO MOVEMENT', (450, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)
            
            # Prediction cooldown indicator
            if frames_since_prediction < prediction_cooldown:
                cooldown_left = prediction_cooldown - frames_since_prediction
                cv2.putText(image, f'Cooldown: {cooldown_left}', (450, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2, cv2.LINE_AA)

            # Draw Sentence Box
            cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
            cv2.putText(image, ' '.join(sentence), (3, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Show to screen
            cv2.imshow('WeThinkCode_ SASL Decoder - HYBRID APPROACH', image)

            # Break gracefully
            if cv2.waitKey(10) & 0xFF == ord('q'):
                logger.info("User pressed 'q' to quit")
                break

    # Final statistics
    logger.info("="*80)
    logger.info("SESSION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total frames processed: {total_frames}")
    logger.info(f"Frames with movement: {frames_with_movement} ({frames_with_movement/total_frames*100:.2f}%)")
    logger.info(f"Total movement sessions: {movement_sessions}")
    logger.info(f"Total predictions made: {total_predictions}")
    logger.info(f"Final sentence: {' '.join(sentence)}")
    logger.info("="*80)
    
    print("\n" + "="*80)
    print("SESSION SUMMARY - HYBRID APPROACH")
    print("="*80)
    print(f"Total frames processed: {total_frames}")
    print(f"Frames with movement: {frames_with_movement} ({frames_with_movement/total_frames*100:.2f}%)")
    print(f"Total movement sessions: {movement_sessions}")
    print(f"Total predictions made: {total_predictions}")
    print(f"Final sentence: {' '.join(sentence)}")
    print("="*80)
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    predict_improved()
