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
from sklearn.metrics import confusion_matrix, classification_report
import matplotlib.pyplot as plt
import seaborn as sns

from config import ACTIONS, get_model_path, SEQUENCE_LENGTH, TOTAL_FEATURES
from train import load_and_process_data

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

def measure_inference_speed(model, input_shape, num_runs=100):
    """Measure average inference time using synthetic data"""
    times = []
    
    # Create synthetic test samples (random data with correct shape)
    # This avoids loading the entire dataset
    for _ in range(num_runs):
        # Generate random sample matching the model input shape
        sample = np.random.randn(1, *input_shape)
        
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

def evaluate_model_performance(model, X_test, y_test, model_name):
    """Evaluate model and return metrics"""
    print(f"  Evaluating {model_name}...")
    
    # Get predictions
    y_pred_probs = model.predict(X_test, verbose=0)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = np.argmax(y_test, axis=1)
    
    # Calculate metrics
    loss, accuracy = model.evaluate(X_test, y_test, verbose=0)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    
    # Per-class accuracy
    class_accuracy = cm.diagonal() / cm.sum(axis=1)
    
    return {
        'loss': loss,
        'accuracy': accuracy,
        'predictions': y_pred,
        'true_labels': y_true,
        'confusion_matrix': cm,
        'class_accuracy': class_accuracy,
        'pred_probs': y_pred_probs
    }

def plot_confusion_matrix(cm, model_name, save_path=None):
    """Plot confusion matrix"""
    plt.figure(figsize=(12, 10))
    
    # Use action names if length matches
    labels = ACTIONS if len(ACTIONS) == len(cm) else [f"Class {i}" for i in range(len(cm))]
    
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels, yticklabels=labels,
                cbar_kws={'label': 'Count'})
    
    plt.title(f'Confusion Matrix - {model_name}', fontsize=16, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"  Saved to {save_path}")
    
    plt.close()

def print_classification_report(y_true, y_pred, model_name):
    """Print detailed classification report"""
    labels = ACTIONS if len(ACTIONS) == np.max(y_true) + 1 else [f"Class {i}" for i in range(np.max(y_true) + 1)]
    
    print(f"\n{model_name} - Detailed Classification Report:")
    print("-" * 80)
    report = classification_report(y_true, y_pred, target_names=labels, digits=4)
    print(report)

# =============================================================================
# MAIN COMPARISON
# =============================================================================
def compare_models():
    """Compare LSTM and Transformer models"""
    
    print("\n" + "="*80)
    print("MODEL COMPARISON: LSTM vs TRANSFORMER")
    print("="*80 + "\n")
    
    # Load test data for performance evaluation
    print("Loading test data for performance evaluation...")
    X, y = load_and_process_data()
    
    if len(X) == 0:
        print("❌ ERROR: No data loaded! Cannot compare model performance.")
        return
    
    # Split data - use 20% for testing
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y.argmax(axis=1)
    )
    
    print(f"Test dataset: {len(X_test)} samples\n")
    
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
    
    # Performance evaluation
    print("\n" + "="*80)
    print("2. PERFORMANCE METRICS (Accuracy, Loss, Error)")
    print("="*80 + "\n")
    
    lstm_perf = None
    transformer_perf = None
    
    if lstm_info:
        lstm_perf = evaluate_model_performance(
            lstm_info['model'], X_test, y_test, "LSTM"
        )
    
    if transformer_info:
        transformer_perf = evaluate_model_performance(
            transformer_info['model'], X_test, y_test, "Transformer"
        )
    
    print(f"\n{'Metric':<30} {'LSTM':<25} {'Transformer':<25}")
    print("-" * 80)
    
    if lstm_perf:
        lstm_acc = f"{lstm_perf['accuracy']*100:.2f}%"
        lstm_loss = f"{lstm_perf['loss']:.4f}"
        lstm_err = f"{(1-lstm_perf['accuracy'])*100:.2f}%"
    else:
        lstm_acc = "N/A"
        lstm_loss = "N/A"
        lstm_err = "N/A"
    
    if transformer_perf:
        trans_acc = f"{transformer_perf['accuracy']*100:.2f}%"
        trans_loss = f"{transformer_perf['loss']:.4f}"
        trans_err = f"{(1-transformer_perf['accuracy'])*100:.2f}%"
    else:
        trans_acc = "N/A"
        trans_loss = "N/A"
        trans_err = "N/A"
    
    print(f"{'Test Accuracy':<30} {lstm_acc:<25} {trans_acc:<25}")
    print(f"{'Test Loss':<30} {lstm_loss:<25} {trans_loss:<25}")
    print(f"{'Error Rate':<30} {lstm_err:<25} {trans_err:<25}")
    
    # Per-class accuracy
    if lstm_perf:
        print(f"\nLSTM - Per-Class Accuracy:")
        for i, acc in enumerate(lstm_perf['class_accuracy']):
            action_name = ACTIONS[i] if i < len(ACTIONS) else f"Class {i}"
            print(f"  {action_name:<20}: {acc*100:>6.2f}%")
    
    if transformer_perf:
        print(f"\nTransformer - Per-Class Accuracy:")
        for i, acc in enumerate(transformer_perf['class_accuracy']):
            action_name = ACTIONS[i] if i < len(ACTIONS) else f"Class {i}"
            print(f"  {action_name:<20}: {acc*100:>6.2f}%")
    
    # Input shape for testing
    input_shape = (SEQUENCE_LENGTH, TOTAL_FEATURES)
    
    # Inference speed comparison
    print("\n" + "="*80)
    print("3. INFERENCE SPEED")
    print("="*80 + "\n")

    if lstm_info:
        print("Measuring LSTM inference speed (100 runs with synthetic data)...")
        lstm_speed = measure_inference_speed(lstm_info['model'], input_shape, num_runs=100)

    if transformer_info:
        print("Measuring Transformer inference speed (100 runs with synthetic data)...")
        transformer_speed = measure_inference_speed(transformer_info['model'], input_shape, num_runs=100)

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
    
    # Confusion Matrix
    print("\n" + "="*80)
    print("4. CONFUSION MATRICES")
    print("="*80 + "\n")
    
    if lstm_perf:
        print("Generating LSTM confusion matrix...")
        plot_confusion_matrix(
            lstm_perf['confusion_matrix'], 
            "LSTM",
            "model/lstm_confusion_matrix.png"
        )
        print("\nLSTM Confusion Matrix:")
        print(lstm_perf['confusion_matrix'])
        print_classification_report(
            lstm_perf['true_labels'], 
            lstm_perf['predictions'], 
            "LSTM"
        )
    
    if transformer_perf:
        print("\nGenerating Transformer confusion matrix...")
        plot_confusion_matrix(
            transformer_perf['confusion_matrix'], 
            "Transformer",
            "model/transformer_confusion_matrix.png"
        )
        print("\nTransformer Confusion Matrix:")
        print(transformer_perf['confusion_matrix'])
        print_classification_report(
            transformer_perf['true_labels'], 
            transformer_perf['predictions'], 
            "Transformer"
        )

    # Summary
    print("\n" + "="*80)
    print("5. SUMMARY & RECOMMENDATIONS")
    print("="*80 + "\n")

    if lstm_info and transformer_info and lstm_perf and transformer_perf:
        # Determine winner for each category
        print("📊 COMPARISON RESULTS:\n")
        
        # Accuracy winner
        if transformer_perf['accuracy'] > lstm_perf['accuracy']:
            acc_diff = (transformer_perf['accuracy'] - lstm_perf['accuracy']) * 100
            print(f"✓ Accuracy: Transformer wins by {acc_diff:.2f}%")
        elif lstm_perf['accuracy'] > transformer_perf['accuracy']:
            acc_diff = (lstm_perf['accuracy'] - transformer_perf['accuracy']) * 100
            print(f"✓ Accuracy: LSTM wins by {acc_diff:.2f}%")
        else:
            print(f"✓ Accuracy: Tie")
        
        # Loss winner (lower is better)
        if transformer_perf['loss'] < lstm_perf['loss']:
            loss_diff = lstm_perf['loss'] - transformer_perf['loss']
            print(f"✓ Loss: Transformer wins (lower by {loss_diff:.4f})")
        elif lstm_perf['loss'] < transformer_perf['loss']:
            loss_diff = transformer_perf['loss'] - lstm_perf['loss']
            print(f"✓ Loss: LSTM wins (lower by {loss_diff:.4f})")
        else:
            print(f"✓ Loss: Tie")

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

        # Overall recommendation based on accuracy
        if transformer_perf['accuracy'] > lstm_perf['accuracy']:
            print("→ 🏆 WINNER: Transformer")
            print(f"  • {transformer_perf['accuracy']*100:.2f}% accuracy vs {lstm_perf['accuracy']*100:.2f}%")
            print("  • Better at capturing complex patterns")
            print("  • Attention mechanism provides interpretability")
        elif lstm_perf['accuracy'] > transformer_perf['accuracy']:
            print("→ 🏆 WINNER: LSTM")
            print(f"  • {lstm_perf['accuracy']*100:.2f}% accuracy vs {transformer_perf['accuracy']*100:.2f}%")
            print("  • Simpler and more efficient")
            print("  • Better generalization for this dataset")
        else:
            print("→ 🤝 TIE: Both models perform similarly")
            print("  • Consider inference speed and model size for deployment")
        
        print("\n→ Check confusion matrices:")
        print("  • model/lstm_confusion_matrix.png")
        print("  • model/transformer_confusion_matrix.png")
        print("\n→ Review detailed metrics above for per-class performance")

    print("\n" + "="*80 + "\n")

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    compare_models()

