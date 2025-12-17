"""
Configuration file for WeThinkCode_ SASL Sign Language Project
Based on 'Einstein Hands' Vocabulary (300+ signs).
Structured for the 'No-Burnout' Weekly Plan (5 signs/week).
"""
import os
import numpy as np

# ---------------------------------------------------
# 1. PROJECT SETUP
# ---------------------------------------------------
DATA_PATH = os.path.join('MP_Data')  # Folder for collected data
MODEL_PATH = os.path.join('model')   # Folder for saved models (aligned with train.py)
LOGS_PATH = os.path.join('logs')     # Folder for logs (aligned with train.py)

# ---------------------------------------------------
# 2. DATA COLLECTION CONFIG
# ---------------------------------------------------
no_sequences = 30       # Videos per word
sequence_length = 30    # Frames per video
start_folder = 0        # Start count

# Uppercase aliases for train.py and predict.py compatibility
SEQUENCE_LENGTH = sequence_length
NO_SEQUENCES = no_sequences

# ---------------------------------------------------
# 3. MODEL TRAINING CONFIG
# ---------------------------------------------------
# Training hyperparameters
EPOCHS = 200                    # Maximum training epochs
BATCH_SIZE = 32                 # Batch size for training
LSTM_UNITS = [64, 128, 64]      # LSTM layer units (3 layers)
DENSE_UNITS = [64, 32]          # Dense layer units (2 layers)
DROPOUT_RATE = 0.2              # Dropout rate to prevent overfitting

# MediaPipe detection confidence
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Total features from MediaPipe Holistic
# Pose: 33 landmarks × 4 (x, y, z, visibility) = 132
# Face: 468 landmarks × 3 (x, y, z) = 1404
# Left Hand: 21 landmarks × 3 (x, y, z) = 63
# Right Hand: 21 landmarks × 3 (x, y, z) = 63
# Total: 132 + 1404 + 63 + 63 = 1662
TOTAL_FEATURES = 1662

# ---------------------------------------------------
# 3. WEEKLY VOCABULARY SCHEDULE (The Master Plan)
# ---------------------------------------------------
# Words are grouped by your 40-Week Goals.
# We have distributed the A-Z list into these topics.

VOCAB_SCHEDULE = {
    # =========================================
    # PHASE 1: THE FOUNDATION (Weeks 1-5)
    # =========================================
    "Week_1_Greetings":  ['hello', 'goodbye', 'yes', 'no', 'welcome', 'awake', 'alive', 'start'],
    "Week_2_Manners":    ['please', 'thank_you', 'sorry', 'excuse', 'respect', 'join', 'help', 'accept'],
    "Week_3_Questions":  ['who', 'what', 'where', 'when', 'why', 'how', 'ask', 'question', 'answer'],
    "Week_4_Grammar":    ['because', 'but', 'and', 'if', 'or', 'about', 'maybe', 'idea', 'example'],
    "Week_5_Pronouns":   ['i', 'you', 'me', 'mine', 'we', 'us', 'they', 'your', 'my', 'him', 'her'],

    # =========================================
    # PHASE 2: PEOPLE & FEELINGS (Weeks 6-10)
    # =========================================
    "Week_6_Family_A":   ['mother', 'father', 'brother', 'sister', 'family', 'parents', 'husband', 'wife'],
    "Week_7_Family_B":   ['grandmother', 'grandfather', 'aunt', 'uncle', 'cousin', 'child', 'baby', 'friend', 'neighbor'],
    "Week_8_Feelings_A": ['happy', 'sad', 'angry', 'afraid', 'scared', 'cry', 'laugh', 'smile'],
    "Week_9_Feelings_B": ['tired', 'sick', 'hungry', 'thirsty', 'bored', 'busy', 'pain', 'hurt', 'feel'],
    "Week_10_Opinions":  ['love', 'like', 'hate', 'enjoy', 'want', 'need', 'prefer', 'hope', 'wish'],

    # =========================================
    # PHASE 3: DAILY ROUTINE (Weeks 11-16)
    # =========================================
    "Week_11_Actions":   ['sleep', 'wake_up', 'eat', 'drink', 'bath', 'wash', 'clean', 'brush', 'rest'],
    "Week_12_Home_A":    ['home', 'house', 'kitchen', 'bedroom', 'bathroom', 'toilet', 'room', 'door'],
    "Week_13_Home_B":    ['window', 'table', 'chair', 'bed', 'light', 'lamp', 'key', 'lock', 'floor'],
    "Week_14_Tech":      ['computer', 'phone', 'tv', 'radio', 'internet', 'video', 'email', 'message', 'call'],
    "Week_15_Clothing_A":['shirt', 'pants', 'dress', 'shoes', 'socks', 'clothes', 'wear', 'change'],
    "Week_16_Clothing_B":['jacket', 'hat', 'coat', 'glasses', 'bag', 'purse', 'watch', 'umbrella'],

    # =========================================
    # PHASE 4: FOOD & NATURE (Weeks 17-22)
    # =========================================
    "Week_17_Fruit":     ['apple', 'banana', 'orange', 'grape', 'fruit', 'lemon', 'peach', 'strawberry'],
    "Week_18_Veg":       ['carrot', 'potato', 'tomato', 'onion', 'pumpkin', 'vegetable', 'cabbage', 'corn'],
    "Week_19_Meals":     ['bread', 'meat', 'chicken', 'fish', 'egg', 'cheese', 'sandwich', 'soup', 'salad'],
    "Week_20_Drinks":    ['water', 'milk', 'juice', 'tea', 'coffee', 'sugar', 'soda', 'wine', 'beer'],
    "Week_21_Nature_A":  ['sun', 'moon', 'rain', 'wind', 'cloud', 'sky', 'star', 'weather', 'hot', 'cold'],
    "Week_22_Nature_B":  ['tree', 'flower', 'grass', 'fire', 'river', 'sea', 'beach', 'mountain', 'ground'],

    # =========================================
    # PHASE 5: TIME & PLACES (Weeks 23-28)
    # =========================================
    "Week_23_Time_A":    ['today', 'tomorrow', 'yesterday', 'now', 'later', 'soon', 'before', 'after'],
    "Week_24_Time_B":    ['morning', 'afternoon', 'evening', 'night', 'day', 'noon', 'midnight', 'time'],
    "Week_25_Calendar":  ['week', 'month', 'year', 'birthday', 'holiday', 'monday', 'friday', 'weekend'],
    "Week_26_School":    ['teacher', 'student', 'class', 'book', 'pen', 'paper', 'learn', 'write', 'read', 'study'],
    "Week_27_Work":      ['work', 'job', 'boss', 'office', 'meeting', 'computer', 'email', 'salary'],
    "Week_28_Places":    ['school', 'shop', 'hospital', 'police', 'church', 'bank', 'restaurant', 'city', 'town'],

    # =========================================
    # PHASE 6: TRANSPORT & MOVEMENT (Weeks 29-32)
    # =========================================
    "Week_29_Vehicles":  ['car', 'bus', 'taxi', 'train', 'plane', 'bike', 'truck', 'drive', 'ride'],
    "Week_30_Directions":['left', 'right', 'up', 'down', 'straight', 'stop', 'go', 'come', 'stay'],
    "Week_31_Travel":    ['visit', 'travel', 'holiday', 'trip', 'ticket', 'passport', 'arrive', 'leave'],
    "Week_32_Movement":  ['walk', 'run', 'jump', 'sit', 'stand', 'dance', 'play', 'fall', 'climb'],

    # =========================================
    # PHASE 7: ANIMALS & DESCRIPTIONS (Weeks 33-37)
    # =========================================
    "Week_33_Pets":      ['cat', 'dog', 'bird', 'fish', 'rabbit', 'mouse', 'pet', 'feed'],
    "Week_34_Farm":      ['cow', 'pig', 'sheep', 'goat', 'chicken', 'horse', 'duck', 'farm'],
    "Week_35_Wild":      ['lion', 'elephant', 'monkey', 'giraffe', 'zebra', 'snake', 'crocodile', 'hippo'],
    "Week_36_Desc_A":    ['big', 'small', 'good', 'bad', 'fast', 'slow', 'loud', 'quiet'],
    "Week_37_Desc_B":    ['same', 'different', 'open', 'closed', 'full', 'empty', 'new', 'old', 'beautiful'],

    # =========================================
    # PHASE 8: ADVANCED & HEALTH (Weeks 38-40)
    # =========================================
    "Week_38_Health":    ['doctor', 'nurse', 'medicine', 'hospital', 'clinic', 'body', 'head', 'stomach', 'blood'],
    "Week_39_Verbs_Mix": ['give', 'take', 'make', 'do', 'try', 'know', 'think', 'remember', 'forget'],
    "Week_40_Final_Mix": ['funny', 'cool', 'luck', 'congratulations', 'finish', 'end', 'problem', 'solve']
}

# ---------------------------------------------------
# 4. ACTIVE CONFIGURATION (CONTROL PANEL)
# ---------------------------------------------------

# !!! CHANGE THIS VARIABLE TO WORK ON A SPECIFIC WEEK !!!
# Options: 'Week_1_Greetings', 'Week_2_Manners', 'All', etc.
ACTIVE_WEEK = 'Week_1_Greetings'

def get_actions():
    """
    Returns the list of words based on the ACTIVE_WEEK setting.
    This is what the Model will look at.
    """
    if ACTIVE_WEEK == 'All':
        # Flatten all lists into one big array
        all_words = []
        for week in VOCAB_SCHEDULE.values():
            all_words.extend(week)
        return np.array(all_words)
    
    elif ACTIVE_WEEK in VOCAB_SCHEDULE:
        # Return only the specific week's words
        return np.array(VOCAB_SCHEDULE[ACTIVE_WEEK])
    
    else:
        raise ValueError(f"Week '{ACTIVE_WEEK}' not found in schedule.")

# The final list used by main.py
ACTIONS = get_actions()

# Create a map for the AI to understand labels
label_map = {label:num for num, label in enumerate(ACTIONS)}

# ---------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------
def create_directories():
    """
    Creates necessary directories for the project if they don't exist.
    Used by train.py to ensure model and log directories exist.
    """
    os.makedirs(DATA_PATH, exist_ok=True)
    os.makedirs(MODEL_PATH, exist_ok=True)
    os.makedirs(LOGS_PATH, exist_ok=True)
    print(f"✅ Directories verified: {DATA_PATH}, {MODEL_PATH}, {LOGS_PATH}")

def get_model_path():
    """
    Returns the path to the model file based on the active week.
    This ensures train.py and predict.py use the same model file.
    """
    model_filename = f"sasl_model_{ACTIVE_WEEK}.h5"
    return os.path.join(MODEL_PATH, model_filename)

print(f"--- CONFIGURATION LOADED ---")
print(f"Active Schedule: {ACTIVE_WEEK}")
print(f"Target Words ({len(ACTIONS)}): {ACTIONS}")
print(f"Model will be saved to: {get_model_path()}")