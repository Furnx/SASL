"""
Robust Training Script for WeThinkCode_ SASL Project
Updates:
  - Handles 'Distributed' folder names (e.g., 'Thabo_0' instead of just '0')
  - Skips corrupt/empty sequences automatically
  - Visualizes training progress
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import TensorBoard, EarlyStopping, ModelCheckpoint
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

# Import your config
from config import (
    ACTIONS,
    DATA_PATH,
    MODEL_PATH,
    LOGS_PATH,
    EPOCHS,
    BATCH_SIZE,
    LSTM_UNITS,
    DENSE_UNITS,
    DROPOUT_RATE,
    SEQUENCE_LENGTH,
    TOTAL_FEATURES,
    USE_AUGMENTATION,
    AUGMENTATION_FACTOR,
    create_directories,
    get_model_path
)

# Import augmentation
from augmentation import create_augmented_dataset

# =============================================================================
# 1. DATA LOADING FUNCTION (The "Smart" Part)
# =============================================================================
def load_and_process_data():
    """
    Iterates through MP_Data/Action/User_Sequence folders.
    Does NOT rely on fixed numbers (0,1,2). It reads whatever strings are there.
    """
    sequences, labels = [], []
    
    # Create a map: "hello" -> 0, "yes" -> 1
    label_map = {label: num for num, label in enumerate(ACTIONS)}
    
    print(f"🔍 Scanning data for {len(ACTIONS)} active classes...")

    for action in ACTIONS:
        action_path = os.path.join(DATA_PATH, action)
        
        # Skip if action folder doesn't exist (e.g. if you haven't recorded it yet)
        if not os.path.exists(action_path):
            print(f"⚠️ Warning: Folder for '{action}' not found. Skipping.")
            continue

        # Get all subfolders (e.g., Thabo_0, Sarah_1)
        # We ignore .DS_Store or other system files
        sequences_dirs = [d for d in os.listdir(action_path) if os.path.isdir(os.path.join(action_path, d))]
        
        print(f"   - {action}: Found {len(sequences_dirs)} sequences.")

        for seq_name in sequences_dirs:
            window = []
            valid_sequence = True
            
            # Loop through frames 0 to 29
            for frame_num in range(SEQUENCE_LENGTH):
                # We assume frames are saved as 0.npy, 1.npy inside the user's folder
                res_path = os.path.join(action_path, seq_name, "{}.npy".format(frame_num))
                
                if os.path.exists(res_path):
                    res = np.load(res_path)
                    window.append(res)
                else:
                    # If a frame is missing, this sequence is garbage. Skip it.
                    valid_sequence = False
                    break
            
            if valid_sequence and len(window) == SEQUENCE_LENGTH:
                sequences.append(window)
                labels.append(label_map[action])

    print(f"✅ Data Loaded. Total Sequences: {len(sequences)}")
    return np.array(sequences), to_categorical(labels).astype(int)

# =============================================================================
# 2. MODEL DEFINITION
# =============================================================================
def build_model(num_classes):
    model = Sequential()
    
    # LSTM Layers
    # Layer 1
    model.add(LSTM(LSTM_UNITS[0], return_sequences=True, activation='relu', input_shape=(SEQUENCE_LENGTH, TOTAL_FEATURES)))
    
    # Layer 2
    model.add(LSTM(LSTM_UNITS[1], return_sequences=True, activation='relu'))
    
    # Layer 3
    model.add(LSTM(LSTM_UNITS[2], return_sequences=False, activation='relu'))
    
    # Dense Layers (Interpretation)
    model.add(Dense(DENSE_UNITS[0], activation='relu'))
    model.add(Dropout(DROPOUT_RATE)) # Prevents overfitting on backgrounds
    
    model.add(Dense(DENSE_UNITS[1], activation='relu'))
    
    # Output Layer
    model.add(Dense(num_classes, activation='softmax')) # Softmax for probability (0-1)

    model.compile(optimizer='Adam', loss='categorical_crossentropy', metrics=['categorical_accuracy'])
    return model

# =============================================================================
# 3. MAIN TRAINING LOOP
# =============================================================================
def train():
    # 1. Setup
    create_directories()

    # 2. Load Data
    X, y = load_and_process_data()

    if len(X) == 0:
        print("❌ CRITICAL ERROR: No data found. Run data_collection.py first.")
        return

    # 3. Data Augmentation (if enabled)
    if USE_AUGMENTATION:
        print(f"\n{'='*60}")
        print(f"DATA AUGMENTATION ENABLED")
        print(f"{'='*60}")
        print(f"Augmentation factor: {AUGMENTATION_FACTOR}")
        print(f"This will create {AUGMENTATION_FACTOR} augmented versions of each sequence")
        print(f"{'='*60}\n")

        X, y = create_augmented_dataset(X, y, AUGMENTATION_FACTOR)
    else:
        print(f"\n⚠️  Data augmentation is DISABLED")
        print(f"   To enable, set USE_AUGMENTATION = True in config.py\n")

    # 4. Split Data (Train vs Test)
    # We hold back 5% of data to test if the model actually generalizes
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05)

    # 5. Build Model
    # Note: len(ACTIONS) must match the current config.py active list
    print(f"\n{'='*60}")
    print(f"BUILDING LSTM MODEL")
    print(f"{'='*60}")
    model = build_model(len(ACTIONS))
    model.summary()
    print(f"{'='*60}\n")

    # 6. Callbacks (The "Auto-Save" features)
    callbacks = [
        # Stop training if it stops getting better (saves time)
        EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True, verbose=1),
        # Save the best version of the model automatically
        ModelCheckpoint(get_model_path(), monitor='val_loss', save_best_only=True, verbose=1)
    ]

    # 7. Train
    print(f"\n{'='*60}")
    print(f"STARTING TRAINING")
    print(f"{'='*60}")
    print(f"Training samples: {len(X_train)}")
    print(f"Validation samples: {len(X_test)}")
    print(f"Epochs: {EPOCHS}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Model will be saved to: {get_model_path()}")
    print(f"{'='*60}\n")

    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_test, y_test),
        callbacks=callbacks,
        verbose=1
    )

    # 8. Final Evaluation
    print(f"\n{'='*60}")
    print(f"TRAINING COMPLETE!")
    print(f"{'='*60}")

    train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)

    print(f"Training Accuracy:   {train_acc*100:.2f}%")
    print(f"Validation Accuracy: {test_acc*100:.2f}%")
    print(f"Model saved to: {get_model_path()}")
    print(f"{'='*60}\n")

    return model, history

    print(f"\n🎉 Success! Model saved to: {get_model_path()}")

if __name__ == "__main__":
    train()