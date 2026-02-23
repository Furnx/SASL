# 🧠 model_P_Line — SASL Sign Language ML Pipeline

> The complete machine learning pipeline for collecting, training, and predicting South African Sign Language (SASL) gestures using MediaPipe Holistic and deep learning.

---

## 📋 Table of Contents

- [Pipeline Overview](#pipeline-overview)
- [File Reference](#file-reference)
- [Data Flow](#data-flow)
- [How to Use](#how-to-use)
- [Model Architectures](#model-architectures)
- [Configuration System](#configuration-system)
- [LLM Integration](#llm-integration)

---

## Pipeline Overview

```
┌─────────────────────┐
│   config.py         │ ← Central config: vocabulary, hyperparameters, paths
└──────────┬──────────┘
           │
    ┌──────▼──────┐     ┌──────────────────┐
    │  data_      │     │  Demonstration   │
    │  collection │◄────│  _videos/        │ (reference videos shown during recording)
    │  .py        │     └──────────────────┘
    └──────┬──────┘
           │ Saves .npy keypoints to MP_Data/
           │
    ┌──────▼──────┐
    │ upload_     │ → Google Drive (team collaboration)
    │ data.py     │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ pre-        │ ← Downloads & normalises team data
    │ process.py  │
    └──────┬──────┘
           │
    ┌──────▼──────┐     ┌──────────────────┐
    │ train.py    │     │ augmentation.py  │ ← Data augmentation (time warp, noise, etc.)
    │ (LSTM)      │◄────│                  │
    └──────┬──────┘     └──────────────────┘
           │
    ┌──────▼──────┐     ┌──────────────────┐
    │ train_      │     │ augmentation.py  │
    │ transformer │◄────│                  │
    │ .py         │     └──────────────────┘
    └──────┬──────┘
           │ Saves .h5 models to model/
           │
    ┌──────▼──────┐
    │ predict.py  │ → Real-time webcam prediction
    └──────┬──────┘
           │
    ┌──────▼──────────────────┐     ┌──────────────────────────┐
    │ prediction_             │     │ LLM_prediction_          │
    │ Improvement.py          │────►│ improvement.py           │
    │ (movement detection,    │     │ (OpenAI GPT refinement,  │
    │  detailed logging)      │JSON │  LangChain memory,       │
    └─────────────────────────┘     │  popup display, TTS)     │
                                    └──────────────────────────┘
```

---

## File Reference

### 🔧 Configuration & Setup

| File | Purpose |
|------|---------|
| **`config.py`** | Central configuration hub. Defines the 40-week SASL vocabulary schedule (300+ signs), model hyperparameters (LSTM layers, epochs, batch size, dropout), MediaPipe detection confidence, data paths, augmentation settings, and feature dimensions (1662 per frame). All other scripts import from here. |
| **`project_setup.py`** | Automated environment setup script. Detects OS (Windows/Mac/Linux), checks Python version, creates a virtual environment, installs all dependencies from `requirements.txt`, verifies installation, checks camera access, and tests config alignment. Run this first on a new machine. |
| **`requirements.txt`** | Python dependencies: OpenCV, NumPy, MediaPipe, TensorFlow, scikit-learn, Google API client, LangChain, OpenAI, and more. |

### 📸 Data Collection & Upload

| File | Purpose |
|------|---------|
| **`data_collection.py`** | Webcam-based data recording tool. Uses MediaPipe Holistic to extract 1662-dim keypoint vectors (pose: 132, face: 1404, left hand: 63, right hand: 63) per frame. Records 30 videos × 30 frames per sign. Features: unique user IDs for distributed team collection, demonstration video alongside camera feed, skip/retake individual signs, auto-zip and upload to Google Drive when a week is complete. |
| **`upload_data.py`** | Google Drive upload module. Handles OAuth authentication, creates contributor folders, uploads zip files with resumable chunking and progress tracking, and verifies uploads by comparing file sizes. Includes retry logic with exponential backoff. |
| **`pre-process.py`** | Pre-training data normalisation. Downloads team-contributed zip files from Google Drive, extracts them, and flattens the folder structure into the standard `MP_Data/sign_name/user_sequence/frame.npy` format that the training scripts expect. |

### 🎓 Training

| File | Purpose |
|------|---------|
| **`train.py`** | LSTM model training script. Loads data from `MP_Data/`, applies augmentation (if enabled), splits data (95/5 train/test), builds a 3-layer LSTM model (64→128→64 units) with Dense layers (64→32) and dropout, trains with EarlyStopping and ModelCheckpoint callbacks. Saves the best model as `.h5` file. |
| **`train_transformer.py`** | Transformer model training. Same data loading pipeline but builds a Transformer encoder model with multi-head self-attention (8 heads, 3 blocks), positional embedding, and global average pooling. Benefits over LSTM: parallel processing, better long-range dependencies, no vanishing gradients. |
| **`augmentation.py`** | Data augmentation module used during training. Techniques include: **temporal** (time warping — speed up/slow down), **spatial** (translate, scale, rotate keypoints), and **noise** (Gaussian noise, keypoint dropout). Configurable probabilities and ranges in `config.py`. Default augmentation factor: 4× (each sequence produces 4 augmented copies). |
| **`compare_models.py`** | Head-to-head LSTM vs Transformer comparison. Evaluates both models on accuracy, inference speed, model size, and parameter count. Generates confusion matrices and per-class classification reports. |

### 🔮 Prediction

| File | Purpose |
|------|---------|
| **`predict.py`** | Basic real-time prediction. Opens webcam, runs MediaPipe Holistic, feeds 30-frame sliding window into the trained model, displays top-5 probability bars, and constructs sentences from high-confidence predictions (≥80% threshold). Includes model/config mismatch detection. |
| **`predict_transformer.py`** | Same as `predict.py` but loads the Transformer model variant. |
| **`prediction_Improvement.py`** | Enhanced prediction with **hand movement detection** — only triggers inference when significant hand movement is detected (Euclidean distance threshold). Includes comprehensive logging, frame-by-frame statistics, and writes predictions to a shared JSON file for LLM consumption. |
| **`prediction_improvement_TRANSFORMERS.py`** | Same improved prediction logic but for the Transformer model. |

### 🤖 LLM Integration

| File | Purpose |
|------|---------|
| **`LLM_prediction_improvement.py`** | Monitors the shared JSON file written by the prediction script. Accumulates predicted words, waits for a natural pause (5s timeout), then sends the collected words to **OpenAI GPT-3.5/4** via **LangChain** with conversation memory. Displays original vs. refined text in a Tkinter popup window. Optional TTS via pyttsx3. |
| **`LLM_prediction_improvement_transformers.py`** | Same LLM integration but paired with the Transformer prediction script. |
| **`LLM_Setup_Guide.md`** | Step-by-step setup guide for the LLM integration: API key configuration, dependency installation, usage instructions, and troubleshooting. |

### 📊 Supporting Files

| File / Folder | Purpose |
|---------------|---------|
| `MP_Data/` | Collected keypoint data organised as `sign_name/user_sequence/frame.npy` |
| `model/` | Saved trained models (`.h5` files) |
| `logs/` | TensorBoard training logs and LLM conversation logs |
| `Demonstration_videos/` | Reference sign language videos organised by week, shown during data collection |
| `analyze_drive_zip.py` | Utility to inspect the contents of uploaded zip files on Google Drive |
| `credentials.json` | Google Cloud OAuth client secret for Drive API access |
| `token.json` | Cached Google OAuth token |
| `shared_predictions_*.json` | Inter-process communication files between prediction and LLM scripts |

---

## Data Flow

### Feature Vector (per frame): 1662 dimensions

| Body Part | Landmarks | Values per Landmark | Total |
|-----------|-----------|-------------------|-------|
| **Pose** | 33 | 4 (x, y, z, visibility) | 132 |
| **Face** | 468 | 3 (x, y, z) | 1404 |
| **Left Hand** | 21 | 3 (x, y, z) | 63 |
| **Right Hand** | 21 | 3 (x, y, z) | 63 |
| | | **Total** | **1662** |

Each sign is represented as a sequence of **30 frames × 1662 features**, giving an input shape of `(30, 1662)` to the neural network.

---

## How to Use

### 1. First-Time Setup
```bash
cd model_P_Line
python project_setup.py
```

### 2. Collect Training Data
Edit `config.py` to set `ACTIVE_WEEK` to your target week, then:
```bash
python data_collection.py
```

### 3. Pre-Process Team Data (if applicable)
```bash
python pre-process.py
```

### 4. Train a Model
```bash
# LSTM
python train.py

# Transformer
python train_transformer.py
```

### 5. Run Predictions
```bash
# Basic
python predict.py

# With movement detection + LLM (run in two terminals)
python prediction_Improvement.py          # Terminal 1
python LLM_prediction_improvement.py      # Terminal 2
```

### 6. Compare Models
```bash
python compare_models.py
```

---

## Model Architectures

### LSTM Model
```
Input (30, 1662) → LSTM(64) → LSTM(128) → LSTM(64) → Dense(64) → Dropout(0.2) → Dense(32) → Softmax(N)
```

### Transformer Model
```
Input (30, 1662) → Linear Embedding → 3× Transformer Encoder Blocks → Global Avg Pool → Dense → Softmax(N)

Each Transformer Block:
  Multi-Head Attention (8 heads) → Add & Norm → Feed-Forward → Add & Norm
```

---

## Configuration System

All configurable values live in `config.py`:

- **`ACTIVE_WEEK`** — Controls which signs to collect/train/predict (e.g., `'Week_5_Pronouns'` or `'All'`)
- **`VOCAB_SCHEDULE`** — Dictionary mapping 40 weeks to their sign lists
- **`EPOCHS`, `BATCH_SIZE`, `DROPOUT_RATE`** — Training hyperparameters
- **`no_sequences`, `sequence_length`** — Data collection settings (30 videos × 30 frames)
- **`AUGMENTATION_CONFIG`** — Per-technique enable/disable, probability, and range settings

---

## LLM Integration

The LLM system works as a **two-process architecture**:

1. **Process 1** (`prediction_Improvement.py`): Detects signs via webcam and writes each predicted word to `shared_predictions_regular.json`
2. **Process 2** (`LLM_prediction_improvement.py`): Monitors the JSON file, accumulates words, sends them to OpenAI GPT after a 5-second pause, and displays the refined sentence

This architecture allows the compute-heavy webcam prediction to run independently of the network-dependent LLM calls.

📖 **See:** [`LLM_Setup_Guide.md`](LLM_Setup_Guide.md) for detailed setup instructions.
