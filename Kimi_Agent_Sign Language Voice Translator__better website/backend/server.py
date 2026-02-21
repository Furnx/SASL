"""
SignBridge SA — FastAPI Backend Server
======================================
Bridges the React frontend with the Python transformer model pipeline.

Endpoints:
    - ws://localhost:8000/ws/predict   — WebSocket for real-time sign prediction
    - GET  /api/health                 — Health check
    - GET  /api/actions                — Available sign actions
    - POST /api/refine                 — LLM sentence refinement
"""

import os
import sys
import json
import time
import base64
import logging
import asyncio
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import mediapipe as mp
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import httpx

# ---------------------------------------------------------------------------
# ENVIRONMENT & PATHS
# ---------------------------------------------------------------------------
load_dotenv()

MODEL_P_LINE_PATH = os.getenv("MODEL_P_LINE_PATH", "c:/365_days/model_P_Line")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Add model_P_Line to Python path so we can import config
sys.path.insert(0, MODEL_P_LINE_PATH)

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("signbridge-backend")

# ---------------------------------------------------------------------------
# IMPORT FROM model_P_Line
# ---------------------------------------------------------------------------
try:
    from config import ACTIONS, ACTIVE_WEEK, get_model_path, SEQUENCE_LENGTH, VOCAB_SCHEDULE
    logger.info(f"Config loaded — Active week: {ACTIVE_WEEK}, Actions: {list(ACTIONS)}")
except ImportError as exc:
    logger.error(f"Could not import from config.py in {MODEL_P_LINE_PATH}: {exc}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# MEDIAPIPE SETUP (same logic as data_collection.py)
# ---------------------------------------------------------------------------
mp_holistic = mp.solutions.holistic


def mediapipe_detection(image: np.ndarray, model):
    """Run MediaPipe detection on a BGR image."""
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = model.process(image_rgb)
    image_rgb.flags.writeable = True
    return results


def extract_keypoints(results) -> np.ndarray:
    """Extract the 1662-dim keypoint vector from MediaPipe results."""
    pose = (
        np.array(
            [[res.x, res.y, res.z, res.visibility] for res in results.pose_landmarks.landmark]
        ).flatten()
        if results.pose_landmarks
        else np.zeros(33 * 4)
    )
    face = (
        np.array(
            [[res.x, res.y, res.z] for res in results.face_landmarks.landmark]
        ).flatten()
        if results.face_landmarks
        else np.zeros(468 * 3)
    )
    lh = (
        np.array(
            [[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]
        ).flatten()
        if results.left_hand_landmarks
        else np.zeros(21 * 3)
    )
    rh = (
        np.array(
            [[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]
        ).flatten()
        if results.right_hand_landmarks
        else np.zeros(21 * 3)
    )
    return np.concatenate([pose, face, lh, rh])


# ---------------------------------------------------------------------------
# MOVEMENT DETECTION (same logic as prediction_improvement_TRANSFORMERS.py)
# ---------------------------------------------------------------------------
def calculate_hand_movement(
    current_keypoints: np.ndarray,
    previous_keypoints: Optional[np.ndarray],
) -> float:
    """Average Euclidean distance of hand landmarks between two frames."""
    if previous_keypoints is None:
        return float("inf")
    current_hands = current_keypoints[-126:]
    previous_hands = previous_keypoints[-126:]
    current_reshaped = current_hands.reshape(-1, 3)
    previous_reshaped = previous_hands.reshape(-1, 3)
    distances = np.linalg.norm(current_reshaped - previous_reshaped, axis=1)
    return float(np.mean(distances))


def is_significant_movement(movement: float, threshold: float = 0.05) -> bool:
    return movement > threshold


# ---------------------------------------------------------------------------
# LOAD TRANSFORMER MODEL
# ---------------------------------------------------------------------------
import tensorflow as tf  # noqa: E402 — imported after path setup

MODEL_FILE = get_model_path().replace(".h5", "_transformer.h5")
logger.info(f"Looking for transformer model: {MODEL_FILE}")

if not os.path.exists(MODEL_FILE):
    # Fallback: scan model directory for any transformer model
    model_dir = os.path.join(MODEL_P_LINE_PATH, "model")
    logger.warning(
        f"Model not found at {MODEL_FILE}. "
        f"Scanning {model_dir} for any transformer model..."
    )

    transformer_models = [
        f for f in os.listdir(model_dir)
        if f.endswith("_transformer.h5")
    ] if os.path.isdir(model_dir) else []

    if transformer_models:
        MODEL_FILE = os.path.join(model_dir, transformer_models[0])
        logger.info(f"Found fallback transformer model: {MODEL_FILE}")

        # Extract week name from model filename to load correct actions
        # e.g., "sasl_model_Week_1_Greetings_transformer.h5" → "Week_1_Greetings"
        fname = transformer_models[0]
        week_name = fname.replace("sasl_model_", "").replace("_transformer.h5", "")
        if week_name in VOCAB_SCHEDULE:
            ACTIONS = np.array(VOCAB_SCHEDULE[week_name])
            logger.info(f"Overriding ACTIONS to match model: {week_name} → {list(ACTIONS)}")
        else:
            logger.warning(f"Could not find '{week_name}' in VOCAB_SCHEDULE, using config ACTIONS")
    else:
        logger.error("No transformer model found in model directory!")
        logger.error("Please run train_transformer.py first.")
        sys.exit(1)

model = tf.keras.models.load_model(MODEL_FILE)
model_output_shape = model.output_shape[1]

if model_output_shape != len(ACTIONS):
    logger.error(
        f"Model output ({model_output_shape}) != ACTIONS count ({len(ACTIONS)}). "
        "Check config.py ACTIVE_WEEK."
    )
    sys.exit(1)

logger.info(f"✅ Transformer model loaded — knows {len(ACTIONS)} signs: {list(ACTIONS)}")

# ---------------------------------------------------------------------------
# LLM SERVICE (same logic as LLM_prediction_improvement_transformers.py)
# ---------------------------------------------------------------------------
llm_instance = None

SYSTEM_PROMPT = """
You are an AI assistant helping to interpret South African Sign Language (SASL) predictions from a Transformer model.

Your role is to TRANSFORM and EXPAND sign language word sequences into natural, conversational English sentences.

IMPORTANT: Don't just restate the words - INTERPRET and EXPAND them!

Key tasks:
1. ADD missing function words (you, are, can, will, let's, the, a, is, etc.)
2. EXPAND abbreviated concepts into full conversational sentences
3. INTERPRET the likely intended meaning, not just literal translation
4. Make sentences sound NATURAL and CONVERSATIONAL
5. Consider context from previous conversations

Examples of what you should do:
- "hello welcome start" → "Hello, you're welcome to start"
- "goodbye no start" → "No, I'm not ready to start yet, goodbye"
- "thank you help" → "Thank you for your help"
- "please sit down" → "Please, have a seat"

Remember: Sign language often omits function words and uses different word order.
Your job is to fill in the gaps and make it sound like natural spoken English.
Be creative but contextually appropriate. Focus on what the person likely MEANT to say.
"""


def get_llm():
    """Lazy-initialize the OpenAI LLM. Returns None if key not configured."""
    global llm_instance
    if llm_instance is not None:
        return llm_instance

    if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
        logger.warning("OpenAI API key not configured — LLM refinement disabled")
        return None

    try:
        from langchain_openai import ChatOpenAI

        llm_instance = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=150,
            openai_api_key=OPENAI_API_KEY,
        )
        logger.info("✅ OpenAI LLM initialized")
        return llm_instance
    except Exception as exc:
        logger.error(f"Failed to initialize OpenAI LLM: {exc}")
        return None


# Conversation history per-session (kept in memory for simplicity)
conversation_histories: dict[str, list] = {}


async def refine_with_llm(
    raw_words: list[str],
    context: str = "",
    session_id: str = "default",
) -> str:
    """Refine raw sign words into a natural sentence using OpenAI."""
    llm = get_llm()
    if llm is None:
        # Fallback: basic capitalisation + join
        return basic_refine(raw_words)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        # Build or retrieve conversation history
        if session_id not in conversation_histories:
            conversation_histories[session_id] = [SystemMessage(content=SYSTEM_PROMPT)]

        history = conversation_histories[session_id]

        sentence_text = " ".join(raw_words)
        prompt = (
            f"Transform these SASL words into natural English: '{sentence_text}'. "
            "Don't just repeat them - ADD missing words, fix grammar, and make it "
            "conversational. What would someone naturally SAY using these concepts?"
        )
        if context:
            prompt += f"\n\nConversation context:\n{context}"

        human_msg = HumanMessage(content=prompt)
        messages = history + [human_msg]

        # Run LLM (blocking call — run in thread to keep async)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, llm.invoke, messages)
        refined = response.content.strip()

        # Update history (keep last 20 messages max)
        history.append(human_msg)
        history.append(response)
        if len(history) > 21:  # system + 10 pairs
            history[1:3] = []  # remove oldest pair (keep system msg)

        logger.info(f"LLM refined '{sentence_text}' → '{refined}'")
        return refined

    except Exception as exc:
        logger.error(f"LLM refinement error: {exc}")
        return basic_refine(raw_words)


def basic_refine(words: list[str]) -> str:
    """Fallback refinement when LLM is unavailable."""
    if not words:
        return ""
    # Remove consecutive duplicates
    deduped = [words[0]]
    for w in words[1:]:
        if w.lower() != deduped[-1].lower():
            deduped.append(w)
    sentence = " ".join(deduped)
    # Capitalise first letter, add period
    sentence = sentence[0].upper() + sentence[1:].lower()
    if not sentence.endswith((".", "!", "?")):
        sentence += "."
    return sentence


# ---------------------------------------------------------------------------
# PER-CLIENT PREDICTION STATE
# ---------------------------------------------------------------------------
class ClientState:
    """Holds prediction state for each WebSocket client."""

    def __init__(self):
        self.rolling_buffer: list[np.ndarray] = []
        self.previous_keypoints: Optional[np.ndarray] = None
        self.movement_history: list[float] = []
        self.sentence: list[str] = []
        self.movement_detected: bool = False
        self.consecutive_movement_frames: int = 0
        self.min_movement_frames: int = 3
        self.movement_threshold: float = 0.02
        self.prediction_cooldown: int = 5
        self.frames_since_prediction: int = 0
        self.total_frames: int = 0
        self.total_predictions: int = 0

        # Accumulated predictions waiting for LLM processing
        self.pending_predictions: list[str] = []
        self.last_prediction_time: Optional[float] = None
        self.prediction_timeout: float = 6.0  # seconds before sending to LLM


# ---------------------------------------------------------------------------
# FASTAPI APP
# ---------------------------------------------------------------------------
app = FastAPI(title="SignBridge SA Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- REST ENDPOINTS --------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "model_loaded": True,
        "active_week": str(ACTIVE_WEEK),
        "actions_count": len(ACTIONS),
        "llm_available": get_llm() is not None,
    }


@app.get("/api/actions")
async def get_actions():
    return {
        "active_week": str(ACTIVE_WEEK),
        "actions": [str(a) for a in ACTIONS],
    }


class RefineRequest(BaseModel):
    words: list[str]
    context: str = ""
    session_id: str = "default"


@app.post("/api/refine")
async def refine_endpoint(req: RefineRequest):
    refined = await refine_with_llm(req.words, req.context, req.session_id)
    return {
        "original": " ".join(req.words),
        "refined": refined,
    }


# --- ELEVENLABS TTS ENDPOINT -----------------------------------------------

ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel — clear, natural voice
ELEVENLABS_MODEL = "eleven_flash_v2_5"          # Cheapest & fastest model


class TTSRequest(BaseModel):
    text: str


@app.post("/api/tts")
async def tts_endpoint(req: TTSRequest):
    """Convert text to speech using ElevenLabs API.
    Returns audio/mpeg stream.
    """
    if not ELEVENLABS_API_KEY:
        logger.warning("ElevenLabs API key not configured")
        return {"error": "ElevenLabs API key not configured"}

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": req.text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_detail = response.text[:200]
            logger.error(f"ElevenLabs TTS error ({response.status_code}): {error_detail}")
            return {"error": f"ElevenLabs error: {response.status_code}"}

        logger.info(f"\u2705 ElevenLabs TTS: '{req.text[:50]}...' -> {len(response.content)} bytes")

        return StreamingResponse(
            iter([response.content]),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "inline; filename=speech.mp3"},
        )

    except Exception as exc:
        logger.error(f"ElevenLabs TTS error: {exc}")
        return {"error": str(exc)}


# --- WEBSOCKET ENDPOINT ---------------------------------------------------

@app.websocket("/ws/predict")
async def websocket_predict(ws: WebSocket):
    await ws.accept()
    client = ClientState()
    session_id = f"ws_{id(ws)}_{int(time.time())}"
    logger.info(f"WebSocket client connected — session {session_id}")

    # Create a MediaPipe Holistic instance per connection
    holistic = mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    try:
        while True:
            # Receive a frame from the client
            data = await ws.receive()

            if "bytes" in data:
                raw_bytes = data["bytes"]
            elif "text" in data:
                # Expect base64-encoded JPEG in a JSON message
                try:
                    msg = json.loads(data["text"])
                    if msg.get("type") == "frame":
                        raw_bytes = base64.b64decode(msg["data"])
                    elif msg.get("type") == "flush":
                        # Client requested to flush buffer
                        if client.pending_predictions:
                            refined = await refine_with_llm(
                                client.pending_predictions,
                                session_id=session_id,
                            )
                            await ws.send_json({
                                "type": "refined",
                                "original": " ".join(client.pending_predictions),
                                "refined": refined,
                            })
                            client.pending_predictions = []
                            client.last_prediction_time = None
                        continue
                    elif msg.get("type") == "reset":
                        client = ClientState()
                        await ws.send_json({"type": "reset_ack"})
                        continue
                    else:
                        continue
                except (json.JSONDecodeError, KeyError):
                    continue
            else:
                continue

            # Decode JPEG bytes to OpenCV image
            np_arr = np.frombuffer(raw_bytes, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            client.total_frames += 1

            # --- MediaPipe Detection ---
            results = mediapipe_detection(frame, holistic)
            keypoints = extract_keypoints(results)

            # --- Rolling Buffer (always maintained) ---
            client.rolling_buffer.append(keypoints)
            client.rolling_buffer = client.rolling_buffer[-SEQUENCE_LENGTH:]

            # --- Movement Detection ---
            movement = calculate_hand_movement(keypoints, client.previous_keypoints)
            client.previous_keypoints = keypoints.copy()
            client.movement_history.append(movement)
            client.movement_history = client.movement_history[-SEQUENCE_LENGTH:]

            has_movement = is_significant_movement(movement, client.movement_threshold)
            client.frames_since_prediction += 1

            if has_movement:
                client.consecutive_movement_frames += 1
                if not client.movement_detected:
                    client.movement_detected = True
            else:
                client.consecutive_movement_frames = 0
                client.movement_detected = False

            # --- Prediction Logic ---
            should_predict = (
                len(client.rolling_buffer) == SEQUENCE_LENGTH
                and client.movement_detected
                and client.consecutive_movement_frames >= client.min_movement_frames
                and client.frames_since_prediction >= client.prediction_cooldown
            )

            prediction_result = None

            if should_predict:
                client.total_predictions += 1
                client.frames_since_prediction = 0

                input_data = np.expand_dims(client.rolling_buffer, axis=0)
                res = model.predict(input_data, verbose=0)[0]

                best_idx = int(np.argmax(res))
                confidence = float(res[best_idx])
                predicted_sign = str(ACTIONS[best_idx])

                # Top 5 for UI display
                top_5_indices = np.argsort(res)[-5:][::-1]
                top_5 = [
                    {"word": str(ACTIONS[i]), "confidence": round(float(res[i]), 4)}
                    for i in top_5_indices
                    if float(res[i]) > 0.05
                ]

                logger.info(
                    f"Prediction #{client.total_predictions}: "
                    f"{predicted_sign} ({confidence * 100:.1f}%)"
                )

                # Only accept predictions above 50% confidence
                if confidence > 0.5:
                    # Add to sentence (no consecutive duplicates)
                    if not client.sentence or predicted_sign != client.sentence[-1]:
                        client.sentence.append(predicted_sign)
                        client.pending_predictions.append(predicted_sign)
                        client.last_prediction_time = time.time()

                    if len(client.sentence) > 5:
                        client.sentence = client.sentence[-5:]

                prediction_result = {
                    "type": "prediction",
                    "word": predicted_sign,
                    "confidence": round(confidence, 4),
                    "top5": top_5,
                    "sentence": list(client.sentence),
                    "accepted": confidence > 0.5,
                }

            # --- Send status update ---
            status_msg = {
                "type": "status",
                "bufferSize": len(client.rolling_buffer),
                "bufferMax": SEQUENCE_LENGTH,
                "movementDetected": client.movement_detected,
                "consecutiveFrames": client.consecutive_movement_frames,
                "totalPredictions": client.total_predictions,
                "sentence": list(client.sentence),
            }

            if prediction_result:
                # Send prediction first, then status
                await ws.send_json(prediction_result)

            await ws.send_json(status_msg)

            # --- Check if pending predictions should be sent to LLM ---
            if (
                client.last_prediction_time
                and time.time() - client.last_prediction_time > client.prediction_timeout
                and client.pending_predictions
            ):
                refined = await refine_with_llm(
                    client.pending_predictions,
                    session_id=session_id,
                )
                await ws.send_json({
                    "type": "refined",
                    "original": " ".join(client.pending_predictions),
                    "refined": refined,
                })
                client.pending_predictions = []
                client.last_prediction_time = None

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected — session {session_id}")
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}", exc_info=True)
    finally:
        holistic.close()
        # Clean up conversation history
        conversation_histories.pop(session_id, None)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("🌉 SignBridge SA — Backend Server")
    logger.info("=" * 70)
    logger.info(f"Model: {MODEL_FILE}")
    logger.info(f"Actions ({len(ACTIONS)}): {list(ACTIONS)}")
    logger.info(f"Server: http://{HOST}:{PORT}")
    logger.info(f"WebSocket: ws://{HOST}:{PORT}/ws/predict")
    logger.info("=" * 70)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
