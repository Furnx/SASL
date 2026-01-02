"""
Sign Language Recognition - Transformer Architecture Training
==============================================================
This script trains a Transformer-based model for sign language recognition.

Transformers are better than LSTMs because:
1. Parallel processing (faster training)
2. Better at capturing long-range dependencies
3. Attention mechanism focuses on important frames
4. State-of-the-art for sequence modeling

Author: WeThinkCode_Cohort_2025_SASL team
Date: 2026-01-02
"""

import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input, Dense, Dropout, LayerNormalization, 
    MultiHeadAttention, GlobalAveragePooling1D, Add
)
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
# TRANSFORMER CONFIGURATION
# =============================================================================
# Transformer-specific hyperparameters
TRANSFORMER_CONFIG = {
    'num_transformer_blocks': 3,      # Number of transformer encoder blocks
    'num_heads': 8,                    # Number of attention heads
    'ff_dim': 256,                     # Feed-forward network dimension
    'embed_dim': 128,                  # Embedding dimension
    'dropout_rate': DROPOUT_RATE,      # Dropout rate
}

# =============================================================================
# 1. DATA LOADING (Same as train.py)
# =============================================================================
def load_data():
    """
    Load sequences and labels from DATA_PATH.
    Handles distributed data collection (multiple users per action).
    """
    sequences, labels = [], []
    label_map = {label: num for num, label in enumerate(ACTIONS)}
    
    print(f"\n{'='*60}")
    print(f"LOADING DATA FOR {len(ACTIONS)} ACTIONS")
    print(f"{'='*60}")
    
    for action in ACTIONS:
        action_path = os.path.join(DATA_PATH, action)
        
        if not os.path.exists(action_path):
            print(f"⚠️  WARNING: No data folder for '{action}' - skipping")
            continue
        
        # Get all sequence directories (e.g., "Thabo_0", "Sarah_1", etc.)
        sequences_dirs = [d for d in os.listdir(action_path) 
                         if os.path.isdir(os.path.join(action_path, d))]
        
        loaded_count = 0
        
        for sequence_dir in sequences_dirs:
            sequence_path = os.path.join(action_path, sequence_dir)
            window = []
            
            # Load all frames in this sequence
            for frame_num in range(SEQUENCE_LENGTH):
                npy_path = os.path.join(sequence_path, f"{frame_num}.npy")
                
                if not os.path.exists(npy_path):
                    print(f"⚠️  Missing frame {frame_num} in {action}/{sequence_dir}")
                    break
                
                try:
                    res = np.load(npy_path)
                    window.append(res)
                except Exception as e:
                    print(f"❌ Error loading {npy_path}: {e}")
                    break
            
            # Only add complete sequences
            if len(window) == SEQUENCE_LENGTH:
                sequences.append(window)
                labels.append(label_map[action])
                loaded_count += 1
        
        print(f"✓ {action:20s} → {loaded_count:3d} sequences")
    
    print(f"{'='*60}")
    print(f"TOTAL SEQUENCES LOADED: {len(sequences)}")
    print(f"{'='*60}\n")
    
    return np.array(sequences), to_categorical(labels).astype(int)

# =============================================================================
# 2. TRANSFORMER MODEL DEFINITION
# =============================================================================
def transformer_encoder_block(inputs, num_heads, ff_dim, dropout_rate):
    """
    Single Transformer Encoder Block
    
    Architecture:
    1. Multi-Head Self-Attention
    2. Add & Normalize (Residual connection)
    3. Feed-Forward Network
    4. Add & Normalize (Residual connection)
    
    Args:
        inputs: Input tensor (batch, sequence_length, embed_dim)
        num_heads: Number of attention heads
        ff_dim: Feed-forward network dimension
        dropout_rate: Dropout rate
    
    Returns:
        Output tensor (same shape as input)
    """
    # Multi-Head Self-Attention
    attention_output = MultiHeadAttention(
        num_heads=num_heads,
        key_dim=inputs.shape[-1] // num_heads,
        dropout=dropout_rate
    )(inputs, inputs)
    
    # Add & Normalize (Residual connection)
    attention_output = Dropout(dropout_rate)(attention_output)
    x1 = Add()([inputs, attention_output])
    x1 = LayerNormalization(epsilon=1e-6)(x1)
    
    # Feed-Forward Network
    ffn_output = Dense(ff_dim, activation='relu')(x1)
    ffn_output = Dropout(dropout_rate)(ffn_output)
    ffn_output = Dense(inputs.shape[-1])(ffn_output)
    
    # Add & Normalize (Residual connection)
    ffn_output = Dropout(dropout_rate)(ffn_output)
    x2 = Add()([x1, ffn_output])
    x2 = LayerNormalization(epsilon=1e-6)(x2)
    
    return x2

def build_transformer_model(num_classes):
    """
    Build Transformer-based model for sign language recognition

    Architecture:
    Input (30, 1662) → Embedding → Transformer Blocks → Pooling → Dense → Output

    Why Transformer > LSTM:
    1. Attention mechanism: Focuses on important frames (e.g., peak of hand movement)
    2. Parallel processing: Faster training (LSTM is sequential)
    3. Long-range dependencies: Better at connecting start and end of sign
    4. No vanishing gradients: Better gradient flow

    Args:
        num_classes: Number of sign classes to predict

    Returns:
        Compiled Keras model
    """
    # Input layer
    inputs = Input(shape=(SEQUENCE_LENGTH, TOTAL_FEATURES))

    # Embedding layer (project 1662 features to smaller dimension)
    x = Dense(TRANSFORMER_CONFIG['embed_dim'], activation='relu')(inputs)
    x = LayerNormalization(epsilon=1e-6)(x)

    # Stack multiple Transformer encoder blocks
    for _ in range(TRANSFORMER_CONFIG['num_transformer_blocks']):
        x = transformer_encoder_block(
            x,
            num_heads=TRANSFORMER_CONFIG['num_heads'],
            ff_dim=TRANSFORMER_CONFIG['ff_dim'],
            dropout_rate=TRANSFORMER_CONFIG['dropout_rate']
        )

    # Global pooling (aggregate information from all frames)
    x = GlobalAveragePooling1D()(x)

    # Dense layers for classification
    x = Dense(128, activation='relu')(x)
    x = Dropout(TRANSFORMER_CONFIG['dropout_rate'])(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(TRANSFORMER_CONFIG['dropout_rate'])(x)

    # Output layer
    outputs = Dense(num_classes, activation='softmax')(x)

    # Create model
    model = Model(inputs=inputs, outputs=outputs)

    # Compile model
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['categorical_accuracy']
    )

    return model

# =============================================================================
# 3. TRAINING PIPELINE
# =============================================================================
def train_model():
    """Main training function"""

    # Create necessary directories
    create_directories()

    # Load data
    print("Loading data...")
    X, y = load_data()

    if len(X) == 0:
        print("❌ ERROR: No data loaded! Please run data_collection.py first.")
        return

    print(f"Data shape: X={X.shape}, y={y.shape}")

    # Data Augmentation (if enabled)
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

    # Split data (80% train, 20% validation)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y.argmax(axis=1)
    )

    print(f"Training set: {X_train.shape[0]} samples")
    print(f"Validation set: {X_val.shape[0]} samples")

    # Build model
    print("\nBuilding Transformer model...")
    model = build_transformer_model(num_classes=len(ACTIONS))

    # Print model summary
    print("\n" + "="*60)
    print("MODEL ARCHITECTURE")
    print("="*60)
    model.summary()
    print("="*60 + "\n")

    # Calculate total parameters
    total_params = model.count_params()
    print(f"Total parameters: {total_params:,}")

    # Callbacks
    log_dir = os.path.join(LOGS_PATH, 'transformer')
    os.makedirs(log_dir, exist_ok=True)

    tensorboard_callback = TensorBoard(log_dir=log_dir)

    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=20,
        restore_best_weights=True,
        verbose=1
    )

    model_path = get_model_path().replace('.h5', '_transformer.h5')
    checkpoint = ModelCheckpoint(
        model_path,
        monitor='val_categorical_accuracy',
        save_best_only=True,
        mode='max',
        verbose=1
    )

    # Train model
    print(f"\nTraining for up to {EPOCHS} epochs...")
    print(f"Model will be saved to: {model_path}")
    print("="*60 + "\n")

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[tensorboard_callback, early_stopping, checkpoint],
        verbose=1
    )

    # Final evaluation
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)

    train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)

    print(f"Training Accuracy:   {train_acc*100:.2f}%")
    print(f"Validation Accuracy: {val_acc*100:.2f}%")
    print(f"Model saved to: {model_path}")
    print("="*60 + "\n")

    return model, history

# =============================================================================
# 4. MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("SIGN LANGUAGE RECOGNITION - TRANSFORMER TRAINING")
    print("="*60 + "\n")

    # Train model
    model, history = train_model()

    print("\n✓ Training complete!")
    print("To view training progress, run:")
    print(f"  tensorboard --logdir={LOGS_PATH}")


