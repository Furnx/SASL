"""
Sign Language Recognition - Real-time Prediction with Transformer Model
========================================================================
This script performs real-time sign language recognition using the Transformer model.

Features:
- Frame skipping for better performance
- Top-5 predictions display
- Confidence visualization
- Smooth real-time inference

WeThinkCode_Cohort_2025_SASL
Date: 2026-01-02
"""

import cv2
import numpy as np
import os
from tensorflow.keras.models import load_model

# Import from your existing modules
from config import (
    ACTIONS,
    SEQUENCE_LENGTH,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    get_model_path
)

# Import helper functions from data_collection
from data_collection import (
    mediapipe_detection,
    draw_styled_landmarks,
    extract_keypoints,
    mp_holistic
)

# =============================================================================
# CONFIGURATION
# =============================================================================
CONFIDENCE_THRESHOLD = 0.05  # Only show predictions above 5%
TOP_K = 5  # Show top 5 predictions

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================
def draw_prediction_bar(image, text, probability, y_position, color):
    """
    Draw a horizontal bar showing prediction confidence
    
    Args:
        image: Frame to draw on
        text: Prediction text
        probability: Confidence (0-1)
        y_position: Y coordinate
        color: BGR color tuple
    """
    # Bar dimensions
    bar_width = 300
    bar_height = 25
    x_start = 10
    
    # Background bar (gray)
    cv2.rectangle(
        image,
        (x_start, y_position),
        (x_start + bar_width, y_position + bar_height),
        (50, 50, 50),
        -1
    )
    
    # Confidence bar (colored)
    filled_width = int(bar_width * probability)
    cv2.rectangle(
        image,
        (x_start, y_position),
        (x_start + filled_width, y_position + bar_height),
        color,
        -1
    )
    
    # Text
    label = f"{text}: {probability*100:.1f}%"
    cv2.putText(
        image,
        label,
        (x_start + 5, y_position + 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

def visualize_predictions(image, predictions, actions):
    """
    Visualize top-K predictions on the frame
    
    Args:
        image: Frame to draw on
        predictions: Prediction probabilities array
        actions: List of action names
    """
    # Get top K predictions
    top_k_indices = np.argsort(predictions)[-TOP_K:][::-1]
    
    # Filter by confidence threshold
    significant_predictions = [
        (idx, predictions[idx]) 
        for idx in top_k_indices 
        if predictions[idx] > CONFIDENCE_THRESHOLD
    ]
    
    # Draw each prediction
    y_offset = 50
    for i, (idx, prob) in enumerate(significant_predictions):
        # Color gradient: green (high confidence) to yellow (low confidence)
        if prob > 0.7:
            color = (0, 255, 0)  # Green
        elif prob > 0.4:
            color = (0, 255, 255)  # Yellow
        else:
            color = (0, 165, 255)  # Orange
        
        draw_prediction_bar(
            image,
            actions[idx],
            prob,
            y_offset + i * 35,
            color
        )
    
    # Draw model indicator
    cv2.putText(
        image,
        "Transformer Model",
        (10, image.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1,
        cv2.LINE_AA
    )

# =============================================================================
# MAIN PREDICTION LOOP
# =============================================================================
def run_prediction():
    """Main real-time prediction function"""
    
    # Load model
    model_path = get_model_path().replace('.h5', '_transformer.h5')
    
    if not os.path.exists(model_path):
        print(f"❌ ERROR: Model not found at {model_path}")
        print("Please train the model first using train_transformer.py")
        return
    
    print(f"Loading Transformer model from: {model_path}")
    model = load_model(model_path)
    print("✓ Model loaded successfully!\n")
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    
    # Set camera properties for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Initialize MediaPipe
    with mp_holistic.Holistic(
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE
    ) as holistic:
        
        sequence = []
        predictions = np.zeros(len(ACTIONS))
        
        print("="*60)
        print("REAL-TIME SIGN LANGUAGE RECOGNITION")
        print("="*60)
        print(f"Model: Transformer Architecture")
        print(f"Sequence Length: {SEQUENCE_LENGTH} frames")
        print(f"Actions: {len(ACTIONS)}")
        print("="*60)
        print("\nPress 'q' to quit\n")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # MediaPipe detection
            image, results = mediapipe_detection(frame, holistic)

            # Draw landmarks
            draw_styled_landmarks(image, results)

            # Extract keypoints
            keypoints = extract_keypoints(results)
            sequence.append(keypoints)
            sequence = sequence[-SEQUENCE_LENGTH:]  # Keep only last N frames

            # Make prediction when we have enough frames
            if len(sequence) == SEQUENCE_LENGTH:
                res = model.predict(np.expand_dims(sequence, axis=0), verbose=0)[0]
                predictions = res
            
            # Visualize predictions
            visualize_predictions(image, predictions, ACTIONS)
            
            # Display
            cv2.imshow('Transformer Sign Language Recognition', image)
            
            # Quit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Prediction session ended")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    run_prediction()

