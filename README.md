# 🤟 SignBridge SA — South African Sign Language (SASL) Recognition System

> A full-stack AI system that recognises South African Sign Language (SASL) gestures via webcam and translates them into natural English sentences in real time.

---

## 🎯 Project Overview

This project aims to bridge the communication gap between the Deaf community and hearing individuals in South Africa. It combines **computer vision**, **deep learning**, and **natural language processing** to:

1. **Capture** hand/body/face movements through a webcam using **MediaPipe Holistic**
2. **Recognise** sign language gestures using **LSTM** and **Transformer** neural networks
3. **Refine** raw predicted words into natural sentences using **OpenAI GPT** via LangChain
4. **Speak** the result aloud using **ElevenLabs TTS** or browser SpeechSynthesis
5. **Deliver** the experience through a polished **React** web interface and a **React Native** mobile app

---

## 📂 Project Structure

```
365_days/
│
├── model_P_Line/                  # 🧠 ML Pipeline — data collection, training, prediction, LLM integration
├── converting_videos_with_OPENCV_AND_MEDIAPIPE/  # 🎥 Video processing — downloading, pose extraction, normalisation
│
├── Kimi_Agent_.../                 # 🌐 Full-Stack Web Translator (FastAPI backend + React/TypeScript frontend)
│   ├── backend/                   #     FastAPI server — WebSocket predictions, LLM refinement, ElevenLabs TTS
│   └── app/                       #     React + Vite + TypeScript frontend with conversation interface
│
├── src/                           # 🖥️ Root-Level React Frontend (Vite + TailwindCSS — placeholder landing page)
├── api/                           # 🔌 Flask API Server (basic health-check endpoint, middleware logging)
├── mobile/                        # 📱 React Native (Expo) Mobile App
│
├── Dockerfile                     # Docker build for the root frontend
├── docker-compose.yaml            # Multi-service deployment (frontend + API)
├── package.json                   # Root Node.js config (sasl-chatbot)
├── index.html                     # Vite entry point for root frontend
└── README.md                      # ← You are here
```

---

## 🧠 Core: `model_P_Line/`

The heart of the project — a complete ML pipeline for sign language recognition.

| Stage | Script(s) | Description |
|-------|-----------|-------------|
| **Configuration** | `config.py` | Central config: 40-week vocabulary of 300+ SASL signs, model hyperparameters, MediaPipe settings, folder paths |
| **Data Collection** | `data_collection.py` | Webcam-based recording with MediaPipe Holistic landmark extraction. Supports distributed collection (unique user IDs), demonstration video side-by-side, skip/retake, auto-upload |
| **Data Upload** | `upload_data.py` | Google Drive integration: zips collected data, uploads with resumable chunking, verifies upload integrity |
| **Pre-Processing** | `pre-process.py` | Downloads team data from Google Drive, unzips, normalises folder structure into `MP_Data/sign/video_folder/` format |
| **Data Augmentation** | `augmentation.py` | Time warping, spatial transforms (translate, scale, rotate), Gaussian noise, keypoint dropout — applied during training |
| **Training (LSTM)** | `train.py` | 3-layer LSTM (64→128→64) with Dense layers, dropout, EarlyStopping, ModelCheckpoint |
| **Training (Transformer)** | `train_transformer.py` | Multi-head self-attention Transformer encoder with positional embedding |
| **Prediction (Basic)** | `predict.py` | Real-time webcam inference with top-5 probability bars and sentence construction |
| **Prediction (Improved)** | `prediction_Improvement.py` | Enhanced prediction with hand movement detection, detailed logging, LLM integration via shared JSON |
| **LLM Integration** | `LLM_prediction_improvement.py` | Monitors predictions, sends accumulated words to OpenAI GPT via LangChain, displays refined text in popup window |
| **Model Comparison** | `compare_models.py` | Side-by-side LSTM vs Transformer evaluation: accuracy, inference speed, confusion matrices |
| **Project Setup** | `project_setup.py` | Automated environment setup: OS detection, venv creation, dependency installation, camera check |

📖 **See:** [`model_P_Line/README.md`](model_P_Line/README.md) for full details.

---

## 🎥 Video Processing: `converting_videos_with_OPENCV_AND_MEDIAPIPE/`

A standalone pipeline for sourcing, processing, and normalising SASL demonstration videos.

| Step | Script | Description |
|------|--------|-------------|
| **1. Download** | `LearnSASL_VIDEOS.py`, `realsasl_videos.py` | Scrape SASL videos from LearnSASL (Vimeo) and RealSASL using Selenium + yt-dlp |
| **2. Pose Extraction** | `pose_extraction_videos.py` | Overlay MediaPipe Holistic + Hands landmarks on videos (dual-detector strategy) |
| **3. NumPy Extraction** | `extract_numpy_results.py` | Extract 1662-dim keypoint vectors per frame from videos with hand caching fallback |
| **4. Normalisation** | `normalise_numpy_data.py` | Resample all sequences to exactly 30 frames via linear interpolation |

📖 **See:** [`converting_videos_with_OPENCV_AND_MEDIAPIPE/README.md`](converting_videos_with_OPENCV_AND_MEDIAPIPE/README.md) for full details.

---

## 🌐 Full-Stack Translator: `Kimi_Agent_Sign Language Voice Translator__better website/`

A production-ready web application that connects the ML pipeline to a user-friendly interface.

- **Backend** (`backend/server.py`): FastAPI server with:
  - WebSocket endpoint (`/ws/predict`) for real-time sign prediction from webcam frames
  - REST endpoints for LLM text refinement (`/api/refine`) and ElevenLabs TTS (`/api/tts`)
  - Full MediaPipe + Transformer model integration
- **Frontend** (`app/`): React + TypeScript + Vite application with a conversation interface for two-way communication (sign → text → speech)

---

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Computer Vision** | OpenCV, MediaPipe Holistic, MediaPipe Hands |
| **Deep Learning** | TensorFlow/Keras (LSTM, Transformer), NumPy, scikit-learn |
| **NLP / LLM** | OpenAI GPT-3.5/4, LangChain, conversation memory |
| **Text-to-Speech** | ElevenLabs API (`eleven_flash_v2_5`), browser SpeechSynthesis |
| **Web Frontend** | React, TypeScript, Vite, TailwindCSS |
| **Web Backend** | FastAPI (Python), Flask |
| **Mobile** | React Native (Expo) |
| **Data Pipeline** | Google Drive API, Selenium, yt-dlp |
| **DevOps** | Docker, Docker Compose |
| **Visualisation** | Matplotlib, Seaborn, TensorBoard |

---

## 🚀 Quick Start

### ML Pipeline (`model_P_Line/`)
```bash
cd model_P_Line
python project_setup.py          # Auto-setup environment
python data_collection.py        # Collect sign data via webcam
python train.py                  # Train LSTM model
python predict.py                # Run real-time prediction
```

### Full-Stack App (`Kimi_Agent_.../`)
```bash
# Backend
cd "Kimi_Agent_Sign Language Voice Translator__better website/backend"
pip install -r requirements.txt
python server.py

# Frontend
cd ../app
npm install
npm run dev
```

### Docker Deployment
```bash
docker-compose up --build        # Builds frontend + API containers
```

---

## 📊 Vocabulary Coverage

The system targets **300+ SASL signs** organised into a **40-week learning schedule** across 8 phases:

| Phase | Weeks | Topics |
|-------|-------|--------|
| 1 — Foundation | 1–5 | Greetings, Manners, Questions, Grammar, Pronouns |
| 2 — People & Feelings | 6–10 | Family, Emotions, Opinions |
| 3 — Daily Routine | 11–16 | Actions, Home, Tech, Clothing |
| 4 — Food & Nature | 17–22 | Fruit, Vegetables, Meals, Drinks, Weather |
| 5 — Time & Places | 23–28 | Time, Calendar, School, Work, Places |
| 6 — Transport | 29–32 | Vehicles, Directions, Travel, Movement |
| 7 — Animals & Descriptions | 33–37 | Pets, Farm, Wild, Adjectives |
| 8 — Advanced | 38–40 | Health, Verbs, Mixed Review |

---
