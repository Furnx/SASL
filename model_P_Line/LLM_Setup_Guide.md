# 🤖 LLM Prediction Improvement Setup Guide

## Overview
This system integrates OpenAI's LLM with your SASL prediction models to refine and contextualize predicted sign language sentences using LangChain for memory and conversation history.

## Files Created
- `LLM_prediction_improvement.py` - For regular prediction model
- `LLM_prediction_improvement_transformers.py` - For transformer model  
- `llm_requirements.txt` - Dependencies needed
- Modified `prediction_improvement.py` - Now shares predictions with LLM
- Modified `prediction_improvement_TRANSFORMERS.py` - Now shares predictions with LLM

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r llm_requirements.txt
```

### 2. Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy your API key

### 3. Configure API Keys
Edit both LLM files and replace:
```python
OPENAI_API_KEY = "your-openai-api-key-here"  # Replace with your actual key
```

### 4. Optional: Enable Text-to-Speech
To enable TTS later:
1. Uncomment TTS imports:
   ```python
   import pyttsx3  # Uncomment this line
   ```
2. Set in Config class:
   ```python
   ENABLE_TTS = True  # Change to True
   ```
3. Install pyttsx3:
   ```bash
   pip install pyttsx3
   ```

## How to Use

### Option 1: Regular Model + LLM
Terminal 1:
```bash
python prediction_improvement.py
```
Terminal 2:
```bash
python LLM_prediction_improvement.py
```

### Option 2: Transformer Model + LLM  
Terminal 1:
```bash
python prediction_improvement_TRANSFORMERS.py
```
Terminal 2:
```bash
python LLM_prediction_improvement_transformers.py
```

## How It Works

1. **Sign Detection**: Your prediction script detects sign language and builds sentences
2. **Prediction Sharing**: Each predicted word is shared via JSON file
3. **LLM Processing**: After 5-6 seconds of no new predictions, sentences are sent to OpenAI
4. **Context & Memory**: LangChain maintains conversation history for better context
5. **Refined Output**: AI-refined sentences appear in popup window
6. **TTS Ready**: Optional text-to-speech for AI responses (disabled by default)

## Configuration Options

### Timing Settings
```python
PREDICTION_TIMEOUT = 5.0  # Seconds to wait before sending to LLM
MONITOR_INTERVAL = 0.5   # How often to check for new predictions
```

### LLM Settings
```python
MODEL_NAME = "gpt-3.5-turbo"  # or "gpt-4" if available
MAX_TOKENS = 150             # Response length limit
TEMPERATURE = 0.7            # Creativity level (0-1)
```

### Memory Settings
```python
MEMORY_WINDOW_SIZE = 10  # Remember last 10 conversation exchanges
```

## File Locations
- Shared predictions: `shared_predictions_regular.json` / `shared_predictions_transformer.json`
- Conversation logs: `logs/llm_conversation_regular.log` / `logs/llm_conversation_transformer.log`

## Troubleshooting

### "LLM not available" Error
- Check that your OpenAI API key is correctly set
- Ensure you have internet connectivity
- Verify your OpenAI account has credits

### No Predictions Appearing
- Make sure both scripts are running
- Check that shared JSON files are being created
- Verify the prediction scripts are detecting signs

### Popup Window Issues
- Ensure tkinter is available (usually included with Python)
- Try running with administrator privileges if needed

## Future Enhancements
- ElevenLabs API integration for better TTS
- Custom voice selection
- Real-time streaming responses
- Multi-language support
- Custom LLM fine-tuning for SASL

## API Costs
- GPT-3.5-turbo: ~$0.002 per 1K tokens (very affordable)
- GPT-4: ~$0.03 per 1K tokens (more expensive but better quality)
- Estimate: 50 sign sentences ≈ $0.01-0.10 depending on model

## Notes
- The system waits for natural pauses in signing before processing
- Conversation memory helps maintain context across multiple sign sequences
- TTS is disabled by default to avoid interrupting the signing session
- All conversations are logged for review and improvement