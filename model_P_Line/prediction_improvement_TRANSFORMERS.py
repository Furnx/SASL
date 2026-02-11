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

# Import configuration
from config import (
    ACTIONS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    get_model_path
)

# Override sequence length for transformer model
SEQUENCE_LENGTH = 30  # Transformer model was trained with 30 frames

# Import core functions from data_collection.py (for transformer compatibility)
from data_collection import (
    mediapipe_detection,
    draw_styled_landmarks,
    extract_keypoints,
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
# VISUALIZATION FUNCTION
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
# IMPROVED PREDICTION LOOP
# =============================================================================
def predict_improved():
    """
    Enhanced prediction with movement detection and comprehensive logging.
    """
    # Setup logging
    logger = setup_logging()
    
    # 1. Validation - Load Transformer Model
    model_path = get_model_path().replace('.h5', '_transformer.h5')
    logger.info(f"Transformer model path: {model_path}")
    
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

    logger.info(f"[OK] Transformer model loaded successfully! Knows {len(ACTIONS)} signs.")
    print(f"✅ Transformer Model loaded! It knows {len(ACTIONS)} signs.")
    print("📷 Starting Camera...")
    print("\n🎯 Improved Prediction Features (Transformer):")
    print("   ✓ Collects 30 frames when movement detected")
    print("   ✓ Makes predictions continuously during movement")
    print("   ✓ Comprehensive logging enabled")
    print("   ✓ Using Transformer architecture\n")

    # 3. Initialize tracking variables
    sequence = []
    sentence = []
    previous_keypoints = None
    movement_history = []  # Track movement values
    
    movement_threshold = 0.02  # Lowered from 0.05 to capture slower movements
    grace_period = 15  # Increased from 10 to allow longer pauses
    frames_below_threshold = 0  # Counter for frames with low movement
    
    logger.info(f"Movement threshold set to: {movement_threshold}")
    logger.info(f"Grace period set to: {grace_period} frames")
    
    # Statistics tracking
    total_frames = 0
    frames_with_movement = 0
    total_predictions = 0
    sequence_count = 0
    predictions_this_sequence = 0
    
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
            
            # Track movement in sequence
            if len(sequence) > 0:
                movement_history.append(movement)
            
            # Check if there's significant movement
            has_movement = is_significant_movement(movement, movement_threshold)
            
            if has_movement:
                frames_with_movement += 1
                frames_below_threshold = 0  # Reset grace period counter
                
                # Start new sequence if needed
                if len(sequence) == 0:
                    sequence_count += 1
                    predictions_this_sequence = 0
                    movement_history = [movement]
                    logger.info(f"--- SEQUENCE #{sequence_count} STARTED (Initial Movement: {movement:.4f}) ---")
                
                # Add to sequence
                sequence.append(keypoints)
                current_seq_len = len(sequence)
                
                # Keep last 30 frames
                sequence = sequence[-SEQUENCE_LENGTH:]
                movement_history = movement_history[-SEQUENCE_LENGTH:]

                if len(sequence) == SEQUENCE_LENGTH:
                    # Calculate average movement for this sequence
                    avg_movement = np.mean(movement_history)
                    
                    # Make prediction
                    total_predictions += 1
                    predictions_this_sequence += 1
                    logger.info(f"Making prediction #{total_predictions} for sequence #{sequence_count} (Avg movement: {avg_movement:.4f})")
                    
                    res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
                    
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
                    image = draw_probability_bars(image, res, ACTIONS, len(sequence))

                    # Lowered confidence threshold to 50%
                    if confidence > 0.5:
                        if len(sentence) > 0:
                            if predicted_sign != sentence[-1]:
                                sentence.append(predicted_sign)
                                logger.info(f"  [+] Added '{predicted_sign}' to sentence")
                        else:
                            sentence.append(predicted_sign)
                            logger.info(f"  [+] Added '{predicted_sign}' to sentence (first word)")
                        
                        # Display confidence
                        cv2.putText(image, f'CONF: {confidence:.2f}', (450, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                    else:
                        logger.info(f"  [!] Confidence too low ({confidence*100:.2f}%), not adding to sentence")
                    
                    if len(sentence) > 5: 
                        sentence = sentence[-5:]
                    
                # Display sequence info with average movement
                if len(movement_history) > 0:
                    avg_mov = np.mean(movement_history)
                    
                    # Progress bar for frame collection
                    progress_text = f'Collecting: {len(sequence)}/{SEQUENCE_LENGTH} frames'
                    cv2.putText(image, progress_text, (10, 430), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)
                    
                    # Draw progress bar
                    bar_width = 200
                    bar_height = 20
                    bar_x = 10
                    bar_y = 440
                    progress = len(sequence) / SEQUENCE_LENGTH
                    
                    # Background
                    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
                    # Progress
                    cv2.rectangle(image, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), (0, 255, 255), -1)
                    # Border
                    cv2.rectangle(image, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 255, 255), 2)
                    
                    # Stats below
                    cv2.putText(image, f'Seq: {sequence_count} | Avg Mov: {avg_mov:.3f}', 
                               (10, 475), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                # No significant movement - use grace period
                if len(sequence) > 0:
                    frames_below_threshold += 1
                    
                    # Still add frame to sequence during grace period
                    if frames_below_threshold <= grace_period:
                        sequence.append(keypoints)
                        movement_history.append(movement)
                        sequence = sequence[-SEQUENCE_LENGTH:]
                        movement_history = movement_history[-SEQUENCE_LENGTH:]
                        
                        # Display grace period indicator
                        cv2.putText(image, f'Grace: {frames_below_threshold}/{grace_period}', (450, 60), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2, cv2.LINE_AA)
                    else:
                        # Grace period expired - end sequence
                        avg_movement = np.mean(movement_history) if len(movement_history) > 0 else 0
                        logger.info(f"--- SEQUENCE #{sequence_count} ENDED (collected {len(sequence)} frames, made {predictions_this_sequence} predictions, avg movement: {avg_movement:.4f}) ---")
                        sequence = []
                        movement_history = []
                        frames_below_threshold = 0
                else:
                    # Display "No Movement" indicator
                    cv2.putText(image, 'No Movement', (450, 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)

            # Draw Sentence Box
            cv2.rectangle(image, (0, 0), (640, 40), (245, 117, 16), -1)
            cv2.putText(image, ' '.join(sentence), (3, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            
            # Show to screen
            cv2.imshow('WeThinkCode_ SASL Decoder - IMPROVED', image)

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
    logger.info(f"Total sequences collected: {sequence_count}")
    logger.info(f"Total predictions made: {total_predictions}")
    logger.info(f"Final sentence: {' '.join(sentence)}")
    logger.info("="*80)
    
    print("\n" + "="*80)
    print("SESSION SUMMARY")
    print("="*80)
    print(f"Total frames processed: {total_frames}")
    print(f"Frames with movement: {frames_with_movement} ({frames_with_movement/total_frames*100:.2f}%)")
    print(f"Total sequences collected: {sequence_count}")
    print(f"Total predictions made: {total_predictions}")
    print(f"Final sentence: {' '.join(sentence)}")
    print("="*80)
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    predict_improved()
