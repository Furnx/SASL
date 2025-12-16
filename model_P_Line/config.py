"""
Configuration file for WeThinkCode_ SASL Sign Language Project
Based on 'Einstein Hands' Vocabulary (300+ signs).
Structured for the 'No-Burnout' Weekly Plan (5 signs/week).
"""

import os
import numpy as np

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'MP_Data') 
MODEL_PATH = os.path.join(BASE_DIR, 'model')
LOGS_PATH = os.path.join(BASE_DIR, 'logs')

# =============================================================================
# ACTIONS / CLASSES (WEEKLY SCHEDULE)
# =============================================================================
# INSTRUCTIONS: 
# Uncomment the 5 signs for the CURRENT WEEK only. 
# Keep all other weeks commented out to prevent burnout.

ACTIONS = np.array([
    # -------------------------------------------------------------------------
    # PHASE 1: THE BASICS & MANNERS
    # -------------------------------------------------------------------------
    
    # --- WEEK 1: Golden Rules ---
    #'hello', 
    #'goodbye', 
    #'yes', 
    #'no', 
    #'please',

    # --- WEEK 2: Manners ---
    'thank_you', 
    'sorry', 
    'welcome', 
    'help', 
    'excuse_me',

    # --- WEEK 3: Questions 1 ---
    # 'who', 
    # 'what', 
    # 'where', 
    # 'when', 
    # 'why',

    # --- WEEK 4: Questions 2 ---
    # 'how', 
    # 'which', 
    # 'how_many', 
    # 'how_much', 
    # 'how_old',

    # --- WEEK 5: Pronouns ---
    # 'i', 
    # 'you', 
    # 'he', 
    # 'she', 
    # 'we',

    # -------------------------------------------------------------------------
    # PHASE 2: PEOPLE & FEELINGS
    # -------------------------------------------------------------------------

    # --- WEEK 6: Family 1 ---
    # 'mother', 
    # 'father', 
    # 'brother', 
    # 'sister', 
    # 'family',

    # --- WEEK 7: Family 2 ---
    # 'grandmother', 
    # 'grandfather', 
    # 'aunt', 
    # 'uncle', 
    # 'cousin',

    # --- WEEK 8: Emotions 1 ---
    # 'happy', 
    # 'sad', 
    # 'angry', 
    # 'scared', 
    # 'excited',

    # --- WEEK 9: Emotions 2 ---
    # 'tired', 
    # 'sick', 
    # 'hungry', 
    # 'thirsty', 
    # 'bored',

    # --- WEEK 10: Love & Likes ---
    # 'love', 
    # 'hate', 
    # 'like', 
    # 'dislike', 
    # 'enjoy',

    # -------------------------------------------------------------------------
    # PHASE 3: DAILY LIFE
    # -------------------------------------------------------------------------

    # --- WEEK 11: Routine ---
    # 'wake_up', 
    # 'sleep', 
    # 'eat', 
    # 'drink', 
    # 'wash',

    # --- WEEK 12: Home 1 ---
    # 'home', 
    # 'house', 
    # 'kitchen', 
    # 'bedroom', 
    # 'bathroom',

    # --- WEEK 13: Home 2 ---
    # 'door', 
    # 'window', 
    # 'table', 
    # 'chair', 
    # 'bed',

    # --- WEEK 14: Technology ---
    # 'computer', 
    # 'phone', 
    # 'tv', 
    # 'radio', 
    # 'light',

    # --- WEEK 15: Clothing 1 ---
    # 'shirt', 
    # 'pants', 
    # 'dress', 
    # 'shoes', 
    # 'socks',

    # --- WEEK 16: Clothing 2 ---
    # 'jacket', 
    # 'hat', 
    # 'coat', 
    # 'pyjamas', 
    # 'glasses',

    # -------------------------------------------------------------------------
    # PHASE 4: FOOD & NATURE
    # -------------------------------------------------------------------------

    # --- WEEK 17: Fruit 1 ---
    # 'apple', 
    # 'banana', 
    # 'orange', 
    # 'grape', 
    # 'pear',

    # --- WEEK 18: Vegetables ---
    # 'carrot', 
    # 'potato', 
    # 'tomato', 
    # 'onion', 
    # 'pumpkin',

    # --- WEEK 19: Meals ---
    # 'bread', 
    # 'meat', 
    # 'chicken', 
    # 'fish', 
    # 'egg',

    # --- WEEK 20: Drinks ---
    # 'water', 
    # 'milk', 
    # 'juice', 
    # 'tea', 
    # 'coffee',

    # --- WEEK 21: Nature 1 ---
    # 'sun', 
    # 'moon', 
    # 'rain', 
    # 'wind', 
    # 'cloud',

    # --- WEEK 22: Nature 2 ---
    # 'tree', 
    # 'flower', 
    # 'grass', 
    # 'fire', 
    # 'water',

    # -------------------------------------------------------------------------
    # PHASE 5: TIME, SCHOOL & PLACES
    # -------------------------------------------------------------------------

    # --- WEEK 23: Time 1 ---
    # 'today', 
    # 'tomorrow', 
    # 'yesterday', 
    # 'now', 
    # 'later',

    # --- WEEK 24: Time 2 ---
    # 'morning', 
    # 'afternoon', 
    # 'evening', 
    # 'day', 
    # 'night',

    # --- WEEK 25: Calendar ---
    # 'week', 
    # 'month', 
    # 'year', 
    # 'birthday', 
    # 'holiday',

    # --- WEEK 26: School ---
    # 'teacher', 
    # 'student', 
    # 'class', 
    # 'book', 
    # 'pen',

    # --- WEEK 27: Actions (Cognitive) ---
    # 'learn', 
    # 'write', 
    # 'read', 
    # 'think', 
    # 'know',

    # --- WEEK 28: Places ---
    # 'school', 
    # 'shop', 
    # 'hospital', 
    # 'police_station', 
    # 'church',

    # --- WEEK 29: Transport ---
    # 'car', 
    # 'bus', 
    # 'taxi', 
    # 'train', 
    # 'aeroplane',

    # --- WEEK 30: Colours ---
    # 'red', 
    # 'blue', 
    # 'green', 
    # 'yellow', 
    # 'black',

    # -------------------------------------------------------------------------
    # PHASE 6: ANIMALS (THE FUN PART)
    # -------------------------------------------------------------------------

    # --- WEEK 31: Pets ---
    # 'cat', 
    # 'dog', 
    # 'bird', 
    # 'fish', 
    # 'rabbit',

    # --- WEEK 32: Farm ---
    # 'cow', 
    # 'pig', 
    # 'sheep', 
    # 'goat', 
    # 'chicken',

    # --- WEEK 33: Wild 1 ---
    # 'lion', 
    # 'elephant', 
    # 'monkey', 
    # 'giraffe', 
    # 'zebra',

    # --- WEEK 34: Wild 2 ---
    # 'hippo', 
    # 'rhino', 
    # 'snake', 
    # 'crocodile', 
    # 'frog',

    # -------------------------------------------------------------------------
    # PHASE 7: ADVANCED DESCRIPTIONS & HEALTH
    # -------------------------------------------------------------------------

    # --- WEEK 35: Descriptions 1 ---
    # 'big', 
    # 'small', 
    # 'good', 
    # 'bad', 
    # 'hot',

    # --- WEEK 36: Descriptions 2 ---
    # 'cold', 
    # 'clean', 
    # 'dirty', 
    # 'fast', 
    # 'slow',

    # --- WEEK 37: Descriptions 3 ---
    # 'same', 
    # 'different', 
    # 'open', 
    # 'closed', 
    # 'full',

    # --- WEEK 38: Health ---
    # 'doctor', 
    # 'nurse', 
    # 'medicine', 
    # 'pain', 
    # 'hospital',

    # --- WEEK 39: Action Verbs 1 ---
    # 'go', 
    # 'come', 
    # 'stop', 
    # 'start', 
    # 'wait',

    # --- WEEK 40: Action Verbs 2 ---
    # 'give', 
    # 'take', 
    # 'make', 
    # 'buy', 
    # 'sell',
])

# =============================================================================
# DATA COLLECTION PARAMETERS
# =============================================================================
# 30 videos per person per sign
# If 30 people participate: 30 * 30 = 900 samples per sign (Excellent depth)
NO_SEQUENCES = 30        
SEQUENCE_LENGTH = 30     # Frames (approx 1 sec)
COLLECTION_PAUSE = 2     # Seconds break

# =============================================================================
# MEDIAPIPE PARAMETERS
# =============================================================================
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# =============================================================================
# MODEL ARCHITECTURE
# =============================================================================
# Heavy architecture for 200+ classes
LSTM_UNITS = [128, 256, 128]  
DENSE_UNITS = [256, 128]      
DROPOUT_RATE = 0.2            

# =============================================================================
# TRAINING HYPERPARAMETERS
# =============================================================================
EPOCHS = 2000                 
BATCH_SIZE = 64               
LEARNING_RATE = 1e-4          
EARLY_STOPPING_PATIENCE = 100

# =============================================================================
# FEATURE DIMENSIONS
# =============================================================================
POSE_LANDMARKS = 33
FACE_LANDMARKS = 468
HAND_LANDMARKS = 21
TOTAL_FEATURES = 1662 

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def create_directories():
    for path in [DATA_PATH, MODEL_PATH, LOGS_PATH]:
        if not os.path.exists(path):
            os.makedirs(path)
    
    # Create action subdirectories for UNCOMMENTED actions only
    for action in ACTIONS:
        action_path = os.path.join(DATA_PATH, action)
        if not os.path.exists(action_path):
            os.makedirs(action_path)

def get_model_path(filename='sasl_model_v1.h5'):
    return os.path.join(MODEL_PATH, filename)