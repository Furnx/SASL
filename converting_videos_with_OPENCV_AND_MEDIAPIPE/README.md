# 🎥 converting_videos_with_OPENCV_AND_MEDIAPIPE

> A standalone pipeline for sourcing SASL (South African Sign Language) demonstration videos from the web, extracting body/hand/face pose data using MediaPipe, and normalising the output into training-ready NumPy arrays.

---

## 📋 Table of Contents

- [Pipeline Overview](#pipeline-overview)
- [File Reference](#file-reference)
- [Step-by-Step Workflow](#step-by-step-workflow)
- [Folder Structure](#folder-structure)
- [Technical Details](#technical-details)

---

## Pipeline Overview

```
  ┌─────────────────────┐     ┌─────────────────────┐
  │  LearnSASL_VIDEOS   │     │  realsasl_videos    │
  │  .py                │     │  .py                │
  │  (Vimeo downloads)  │     │  (RealSASL scraper) │
  └──────────┬──────────┘     └──────────┬──────────┘
             │                           │
             ▼                           ▼
       ┌─────────────────────────────────────┐
       │       Demonstration_videos/         │
       │   (raw .mp4 files organised by      │
       │    week and sign name)              │
       └──────────┬──────────────────────────┘
                  │
         ┌────────┴────────┐
         ▼                 ▼
  ┌──────────────┐  ┌──────────────────┐
  │ pose_        │  │ extract_numpy    │
  │ extraction_  │  │ _results.py      │
  │ videos.py    │  │                  │
  │ (visual      │  │ (1662-dim        │
  │  overlays)   │  │  keypoint        │
  └──────┬───────┘  │  vectors)        │
         │          └──────┬───────────┘
         ▼                 │
  ┌──────────────┐         ▼
  │ pose_        │  ┌──────────────────┐
  │ visualized_  │  │ numpy_results/   │
  │ videos/      │  │ (variable-length │
  │ (.mp4s with  │  │  .npy files)     │
  │  landmarks)  │  └──────┬───────────┘
  └──────────────┘         │
                           ▼
                    ┌──────────────────┐
                    │ normalise_numpy  │
                    │ _data.py         │
                    │ (resample to     │
                    │  30 frames)      │
                    └──────┬───────────┘
                           │
                           ▼
                    ┌──────────────────┐
                    │ numpy_normalised/│
                    │ (30, 1662) .npy  │
                    │ files — ready    │
                    │ for training     │
                    └──────────────────┘
```

---

## File Reference

### 📥 Video Downloading

| File | Purpose |
|------|---------|
| **`LearnSASL_VIDEOS.py`** | Downloads sign language videos from **LearnSASL** (learnsasl.com). Handles Vimeo-hosted videos using **yt-dlp**, direct `.mp4` URLs via HTTP requests, and RealSASL player pages via **Selenium** (undetected ChromeDriver with Brave browser). Reads URLs from `urls.txt`. |
| **`realsasl_videos.py`** | Scrapes videos from **RealSASL** (realsasl.com). Requires manual login (session-based authentication). Extracts video titles and source URLs from player pages. Bypasses 403 errors by downloading via the browser's fetch API (`execute_async_script` with base64 encoding). |
| **`somethingelse.py`** | Experimental script for reverse-engineering the LearnSASL Flutter web app. Uses Chrome DevTools Protocol (CDP) to intercept network traffic, scan for Vimeo IDs, and probe Firebase/Flutter internal state for video data. |
| **`urls.txt`** | List of video URLs to download — Vimeo player links and RealSASL player page URLs. |
| **`weeks.md`** | Reference document mapping weekly vocabulary to their video source URLs (LearnSASL Vimeo links and RealSASL player pages). |

### 🔬 Pose Extraction & Visualisation

| File | Purpose |
|------|---------|
| **`pose_extraction_videos.py`** | Processes all `.mp4` files in `Demonstration_videos/` and creates new videos with **MediaPipe landmark overlays** drawn on every frame. Uses a **dual-detector strategy**: MediaPipe Holistic as the primary detector, with a standalone MediaPipe Hands detector as fallback for frames where Holistic misses hand landmarks. Outputs to `pose_visualized_videos/`. |

### 📊 Feature Extraction

| File | Purpose |
|------|---------|
| **`extract_numpy_results.py`** | The core data extraction script. Processes each video frame-by-frame through MediaPipe Holistic and extracts a **1662-dimensional feature vector** per frame (pose: 132, face: 1404, left hand: 63, right hand: 63). Uses the same dual-detector + caching strategy: if both detectors lose a hand, the last known position is held for up to 25 frames. Saves output as `.npy` files in `numpy_results/`. |

### 📏 Normalisation

| File | Purpose |
|------|---------|
| **`normalise_numpy_data.py`** | Resamples all extracted `.npy` sequences to exactly **30 frames** using linear interpolation (`scipy.interpolate.interp1d`). Handles both old-format (object arrays of dicts) and new-format (float arrays) `.npy` files. Collects from multiple input roots (`numpy_results/`, `numpy_results_2/`), skips sequences shorter than 2 frames, and verifies all outputs are the correct shape. Produces a per-sign sample count summary. |

---

## Step-by-Step Workflow

### Step 1: Download Videos

Add video URLs to `urls.txt`, then run one of the download scripts:

```bash
# For LearnSASL / Vimeo / RealSASL (without login)
python LearnSASL_VIDEOS.py

# For RealSASL (with login required)
python realsasl_videos.py
# → A browser window opens; log in manually, then press Enter in the terminal
```

Videos are saved to `Demonstration_videos/` with their sign name as the filename.

### Step 2: Extract Pose Keypoints

```bash
python extract_numpy_results.py
```

This processes every `.mp4` in `Demonstration_videos/` and saves a `.npy` file per video in `numpy_results/`. Each file has shape `(num_frames, 1662)`.

### Step 3: (Optional) Visualise Pose Overlays

```bash
python pose_extraction_videos.py
```

Creates landmark-annotated videos in `pose_visualized_videos/` for visual verification.

### Step 4: Normalise to 30 Frames

```bash
python normalise_numpy_data.py
```

Resamples all `.npy` files to exactly 30 frames and saves them to `numpy_normalised/`. After this step, every file has shape `(30, 1662)` — the same format as the data collected via the `model_P_Line/data_collection.py` webcam tool.

---

## Folder Structure

```
converting_videos_with_OPENCV_AND_MEDIAPIPE/
│
├── Demonstration_videos/          # Raw downloaded .mp4 sign videos (organised by week)
│   ├── Week_1_Greetings/
│   │   ├── hello.mp4
│   │   ├── goodbye.mp4
│   │   └── ...
│   └── ...
│
├── numpy_results/                 # Extracted keypoints (variable frame count)
│   ├── Week_1_Greetings/
│   │   ├── hello.npy              # shape: (N, 1662) where N varies
│   │   └── ...
│   └── ...
│
├── numpy_normalised/              # Normalised keypoints (fixed 30 frames)
│   ├── numpy_results/
│   │   ├── Week_1_Greetings/
│   │   │   ├── hello.npy          # shape: (30, 1662) ✓
│   │   │   └── ...
│   │   └── ...
│   └── ...
│
├── pose_visualized_videos/        # Videos with MediaPipe landmark overlays
│
├── LearnSASL_VIDEOS.py            # Download from LearnSASL / Vimeo
├── realsasl_videos.py             # Download from RealSASL (with login)
├── somethingelse.py               # Experimental Flutter/Firebase probing
├── extract_numpy_results.py       # Video → NumPy feature extraction
├── normalise_numpy_data.py        # Variable frames → fixed 30 frames
├── pose_extraction_videos.py      # Video → landmark-annotated video
├── urls.txt                       # Video URLs to download
├── weeks.md                       # URL reference by week
└── requirements.txt               # Python dependencies
```

---

## Technical Details

### Feature Vector (1662 dimensions per frame)

| Component | Landmarks | Values per Landmark | Dimension |
|-----------|-----------|-------------------|-----------|
| **Pose** | 33 | x, y, z, visibility | 132 |
| **Face** | 468 | x, y, z | 1404 |
| **Left Hand** | 21 | x, y, z | 63 |
| **Right Hand** | 21 | x, y, z | 63 |
| **Total** | | | **1662** |

### Dual-Detector Strategy

The scripts use two MediaPipe models simultaneously to maximise hand detection:

1. **MediaPipe Holistic** (`model_complexity=2`) — Primary detector for pose, face, and hands
2. **MediaPipe Hands** (`model_complexity=1`, `min_detection_confidence=0.3`) — Fallback when Holistic misses a hand

If both detectors fail for a hand, the **last known position is cached** and reused for up to 25 frames (`HAND_HOLD_FRAMES`), preventing gaps in the data.

### Normalisation

Videos vary in length (different frame rates, recording durations). The normalisation step ensures every sign has exactly **30 frames** by applying **linear interpolation** along the time axis. This matches the `sequence_length = 30` expected by the training scripts in `model_P_Line/`.

### Dependencies

```
opencv-python
numpy
mediapipe
scipy
selenium
undetected-chromedriver
yt-dlp
requests
```

Install with:
```bash
pip install -r requirements.txt
```
