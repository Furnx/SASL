"""
Model Comparison: LSTM vs Transformer
======================================
This script compares the performance of LSTM and Transformer models.

Metrics compared:
- Accuracy (training and validation)
- Inference speed
- Model size
- Parameter count

Author: WeThinkCode_Cohort_2025_SASL
Date: 2026-01-02
"""

import os
import time
import numpy as np
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split

from config import ACTIONS, get_model_path
from train import load_data

# =============================================================================
# COMPARISON FUNCTIONS
# =============================================================================
def get_model_info(model_path):
    """Get model information (size, parameters)"""
    if not os.path.exists(model_path):
        return None
    
    model = load_model(model_path)
    
    # Model size in MB
    size_mb = os.path.getsize(model_path) / (1024 * 1024)
    
    # Parameter count
    total_params = model.count_params()
    trainable_params = sum([np.prod(v.shape) for v in model.trainable_weights])
    
    return {
        'model': model,
        'size_mb': size_mb,
        'total_params': total_params,
        'trainable_params': trainable_params
    }

def measure_inference_speed(model, X_test, num_runs=100):
    """Measure average inference time"""
    times = []
    
    for _ in range(num_runs):
        # Random sample
        idx = np.random.randint(0, len(X_test))
        sample = np.expand_dims(X_test[idx], axis=0)
        
        # Time prediction
        start = time.time()
        _ = model.predict(sample, verbose=0)
        end = time.time()
        
        times.append(end - start)
    
    return {
        'mean_ms': np.mean(times) * 1000,
        'std_ms': np.std(times) * 1000,
        'min_ms': np.min(times) * 1000,
        'max_ms': np.max(times) * 1000
    }

def evaluate_model(model, X_train, y_train, X_val, y_val):
    """Evaluate model on train and validation sets"""
    train_loss, train_acc = model.evaluate(X_train, y_train, verbose=0)
    val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
    
    return {
        'train_loss': train_loss,
        'train_acc': train_acc,
        'val_loss': val_loss,
        'val_acc': val_acc
    }

# =============================================================================
# MAIN COMPARISON
# =============================================================================
def compare_models():
    """Compare LSTM and Transformer models"""
    
    print("\n" + "="*80)
    print("MODEL COMPARISON: LSTM vs TRANSFORMER")
    print("="*80 + "\n")
    
    # Load data
    print("Loading data...")
    X, y = load_data()
    
    if len(X) == 0:
        print("❌ ERROR: No data loaded!")
        return
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y.argmax(axis=1)
    )
    
    print(f"Dataset: {len(X)} samples ({len(X_train)} train, {len(X_val)} val)\n")
    
    # Model paths
    lstm_path = get_model_path()
    transformer_path = get_model_path().replace('.h5', '_transformer.h5')
    
    # Load models
    print("Loading models...")
    lstm_info = get_model_info(lstm_path)
    transformer_info = get_model_info(transformer_path)
    
    if lstm_info is None:
        print(f"⚠️  LSTM model not found at {lstm_path}")
    if transformer_info is None:
        print(f"⚠️  Transformer model not found at {transformer_path}")
    
    if lstm_info is None and transformer_info is None:
        print("\n❌ No models found! Please train models first.")
        return
    
    print("\n" + "="*80)
    print("1. MODEL SIZE & COMPLEXITY")
    print("="*80)
    
    # Print comparison table
    print(f"\n{'Metric':<30} {'LSTM':<25} {'Transformer':<25}")
    print("-" * 80)
    
    if lstm_info:
        lstm_size = f"{lstm_info['size_mb']:.2f} MB"
        lstm_params = f"{lstm_info['total_params']:,}"
    else:
        lstm_size = "N/A"
        lstm_params = "N/A"
    
    if transformer_info:
        trans_size = f"{transformer_info['size_mb']:.2f} MB"
        trans_params = f"{transformer_info['total_params']:,}"
    else:
        trans_size = "N/A"
        trans_params = "N/A"
    
    print(f"{'Model Size':<30} {lstm_size:<25} {trans_size:<25}")
    print(f"{'Total Parameters':<30} {lstm_params:<25} {trans_params:<25}")
    
    # Accuracy comparison
    print("\n" + "="*80)
    print("2. ACCURACY")
    print("="*80 + "\n")
    
    if lstm_info:
        print("Evaluating LSTM model...")
        lstm_metrics = evaluate_model(
            lstm_info['model'], X_train, y_train, X_val, y_val
        )
    
    if transformer_info:
        print("Evaluating Transformer model...")
        transformer_metrics = evaluate_model(
            transformer_info['model'], X_train, y_train, X_val, y_val
        )
    
    print(f"\n{'Metric':<30} {'LSTM':<25} {'Transformer':<25}")
    print("-" * 80)
    
    if lstm_info:
        lstm_train = f"{lstm_metrics['train_acc']*100:.2f}%"
        lstm_val = f"{lstm_metrics['val_acc']*100:.2f}%"
    else:
        lstm_train = "N/A"
        lstm_val = "N/A"
    
    if transformer_info:
        trans_train = f"{transformer_metrics['train_acc']*100:.2f}%"
        trans_val = f"{transformer_metrics['val_acc']*100:.2f}%"
    else:
        trans_train = "N/A"
        trans_val = "N/A"
    
    print(f"{'Training Accuracy':<30} {lstm_train:<25} {trans_train:<25}")
    print(f"{'Validation Accuracy':<30} {lstm_val:<25} {trans_val:<25}")

    # Inference speed comparison
    print("\n" + "="*80)
    print("3. INFERENCE SPEED")
    print("="*80 + "\n")

    if lstm_info:
        print("Measuring LSTM inference speed (100 runs)...")
        lstm_speed = measure_inference_speed(lstm_info['model'], X_val, num_runs=100)

    if transformer_info:
        print("Measuring Transformer inference speed (100 runs)...")
        transformer_speed = measure_inference_speed(transformer_info['model'], X_val, num_runs=100)

    print(f"\n{'Metric':<30} {'LSTM':<25} {'Transformer':<25}")
    print("-" * 80)

    if lstm_info:
        lstm_mean = f"{lstm_speed['mean_ms']:.2f} ms"
        lstm_std = f"±{lstm_speed['std_ms']:.2f} ms"
    else:
        lstm_mean = "N/A"
        lstm_std = "N/A"

    if transformer_info:
        trans_mean = f"{transformer_speed['mean_ms']:.2f} ms"
        trans_std = f"±{transformer_speed['std_ms']:.2f} ms"
    else:
        trans_mean = "N/A"
        trans_std = "N/A"

    print(f"{'Average Inference Time':<30} {lstm_mean:<25} {trans_mean:<25}")
    print(f"{'Standard Deviation':<30} {lstm_std:<25} {trans_std:<25}")

    # Summary
    print("\n" + "="*80)
    print("4. SUMMARY & RECOMMENDATIONS")
    print("="*80 + "\n")

    if lstm_info and transformer_info:
        # Determine winner for each category
        print("📊 COMPARISON RESULTS:\n")

        # Accuracy winner
        if transformer_metrics['val_acc'] > lstm_metrics['val_acc']:
            acc_diff = (transformer_metrics['val_acc'] - lstm_metrics['val_acc']) * 100
            print(f"✓ Accuracy: Transformer wins by {acc_diff:.2f}%")
        elif lstm_metrics['val_acc'] > transformer_metrics['val_acc']:
            acc_diff = (lstm_metrics['val_acc'] - transformer_metrics['val_acc']) * 100
            print(f"✓ Accuracy: LSTM wins by {acc_diff:.2f}%")
        else:
            print(f"✓ Accuracy: Tie")

        # Speed winner
        if transformer_speed['mean_ms'] < lstm_speed['mean_ms']:
            speed_diff = lstm_speed['mean_ms'] - transformer_speed['mean_ms']
            print(f"✓ Speed: Transformer wins by {speed_diff:.2f} ms")
        elif lstm_speed['mean_ms'] < transformer_speed['mean_ms']:
            speed_diff = transformer_speed['mean_ms'] - lstm_speed['mean_ms']
            print(f"✓ Speed: LSTM wins by {speed_diff:.2f} ms")
        else:
            print(f"✓ Speed: Tie")

        # Size winner
        if transformer_info['size_mb'] < lstm_info['size_mb']:
            size_diff = lstm_info['size_mb'] - transformer_info['size_mb']
            print(f"✓ Model Size: Transformer wins by {size_diff:.2f} MB")
        elif lstm_info['size_mb'] < transformer_info['size_mb']:
            size_diff = transformer_info['size_mb'] - lstm_info['size_mb']
            print(f"✓ Model Size: LSTM wins by {size_diff:.2f} MB")
        else:
            print(f"✓ Model Size: Tie")

        print("\n💡 RECOMMENDATIONS:\n")

        # Overall recommendation
        if transformer_metrics['val_acc'] > lstm_metrics['val_acc']:
            print("→ Use TRANSFORMER for:")
            print("  • Better accuracy and generalization")
            print("  • Attention mechanism shows which frames are important")
            print("  • State-of-the-art architecture")
            print("\n→ Use LSTM for:")
            print("  • Simpler architecture, easier to understand")
            print("  • Potentially faster inference (if speed is critical)")
        else:
            print("→ Both models perform similarly!")
            print("  • Try collecting more data")
            print("  • Try data augmentation")
            print("  • Experiment with hyperparameters")

    print("\n" + "="*80 + "\n")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    compare_models()

