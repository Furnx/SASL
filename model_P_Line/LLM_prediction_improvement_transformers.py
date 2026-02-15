"""
LLM Prediction Improvement Integration for Transformer Model
Features:
- Monitors prediction_improvement_TRANSFORMERS.py output
- Collects predicted words into sentences
- Uses OpenAI API with LangChain for context and memory
- Displays refined text in popup window
- Text-to-Speech capability (disabled by default)
"""

import time
import json
import threading
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime
import queue
import os
from pathlib import Path

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Text-to-Speech (disabled by default)
# import pyttsx3  # Free TTS - uncomment when needed

# =============================================================================
# CONFIGURATION
# =============================================================================
class Config:
    # API Configuration (TO BE SET BY USER)
    OPENAI_API_KEY = "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"  # Set this
    
    # LLM Settings
    MODEL_NAME = "gpt-3.5-turbo"  # or "gpt-4" if available
    MAX_TOKENS = 150
    TEMPERATURE = 0.7
    
    # Memory Settings
    MEMORY_WINDOW_SIZE = 10  # Remember last 10 exchanges
    
    # Timing Settings
    PREDICTION_TIMEOUT = 6.0  # Seconds to wait before sending to LLM (longer for transformer)
    MONITOR_INTERVAL = 0.5   # How often to check for new predictions
    
    # File Paths
    SHARED_PREDICTIONS_FILE = "shared_predictions_transformer.json"
    CONVERSATION_LOG = "logs/llm_conversation_transformer.log"
    
    # TTS Settings (DISABLED)
    ENABLE_TTS = False  # Set to True when ready
    TTS_RATE = 180     # Words per minute
    TTS_VOLUME = 0.8   # Volume level

# =============================================================================
# LLM INTEGRATION CLASS
# =============================================================================
class LLMPredictorTransformer:
    def __init__(self):
        self.setup_logging()
        self.setup_llm()
        self.setup_memory()
        self.setup_tts()
        self.prediction_queue = queue.Queue()
        self.last_prediction_time = None
        self.current_sentence = []
        self.running = False
        
    def setup_logging(self):
        """Setup logging for conversation history."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        self.log_file = log_dir / "llm_conversation_transformer.log"
        
    def setup_llm(self):
        """Initialize OpenAI LLM with LangChain."""
        if Config.OPENAI_API_KEY == "your-openai-api-key-here":
            print("⚠️  WARNING: OpenAI API key not configured!")
            print("   Please set Config.OPENAI_API_KEY in the script.")
            self.llm = None
            return
            
        try:
            self.llm = ChatOpenAI(
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                openai_api_key=Config.OPENAI_API_KEY
            )
            print("✅ OpenAI LLM initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing OpenAI LLM: {e}")
            self.llm = None
    
    def setup_memory(self):
        """Initialize simple conversation memory."""
        self.conversation_history = []
        self.max_history = Config.MEMORY_WINDOW_SIZE * 2  # User + AI messages
        
        # Initial system message for context
        system_message = SystemMessage(content="""
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
- "hello welcome start" → "Hello, you're welcome to start" or "Hello, you are welcome, let's start"
- "goodbye no start" → "No, I'm not ready to start yet, goodbye" or "Goodbye, we won't start now"
- "thank you help" → "Thank you for your help" or "Thank you, I need help"
- "please sit down" → "Please, have a seat" or "Could you please sit down?"

Remember: Sign language often omits function words and uses different word order.
Your job is to fill in the gaps and make it sound like natural spoken English.
Be creative but contextually appropriate. Focus on what the person likely MEANT to say.
""")
        
        self.conversation_history.append(system_message)
        print("✅ Simple memory initialized (Transformer)")
    
    def setup_tts(self):
        """Initialize Text-to-Speech (disabled by default)."""
        if not Config.ENABLE_TTS:
            self.tts_engine = None
            print("🔇 Text-to-Speech is DISABLED")
            return
            
        try:
            # Uncomment when TTS is needed
            # self.tts_engine = pyttsx3.init()
            # self.tts_engine.setProperty('rate', Config.TTS_RATE)
            # self.tts_engine.setProperty('volume', Config.TTS_VOLUME)
            # print("🔊 Text-to-Speech initialized")
            self.tts_engine = None
            print("🔇 Text-to-Speech initialization skipped (disabled)")
        except Exception as e:
            print(f"❌ Error initializing TTS: {e}")
            self.tts_engine = None
    
    def log_conversation(self, user_input, ai_response):
        """Log the conversation to file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] TRANSFORMER MODEL\n")
            f.write(f"Signs: {user_input}\n")
            f.write(f"AI: {ai_response}\n")
            f.write("-" * 50 + "\n")
    
    def get_llm_response(self, sentence_text):
        """Get response from OpenAI LLM with context."""
        if not self.llm:
            return "⚠️ LLM not available (API key not configured)"
        
        try:
            # Create human message with the predicted signs
            human_message = HumanMessage(content=f"Transform these SASL words into natural English: '{sentence_text}'. Don't just repeat them - ADD missing words, fix grammar, and make it conversational. What would someone naturally SAY using these concepts?")
            
            # Prepare messages with conversation history
            messages = self.conversation_history + [human_message]
            
            print(f"\n🤖 Sending to LLM (Transformer): '{sentence_text}'")
            response = self.llm.invoke(messages)
            
            # Show the LLM response in terminal
            print(f"✨ LLM Response: '{response.content.strip()}'")
            
            # Add exchange to conversation history
            self.conversation_history.append(human_message)
            self.conversation_history.append(response)
            
            # Keep history within limits
            while len(self.conversation_history) > self.max_history:
                # Keep system message and remove oldest user/ai pair
                if len(self.conversation_history) > 3:  # system + at least 1 exchange
                    self.conversation_history.pop(1)  # Remove oldest user message
                    if len(self.conversation_history) > 2:
                        self.conversation_history.pop(1)  # Remove oldest AI message
                else:
                    break
            
            # Log the conversation
            self.log_conversation(sentence_text, response.content)
            
            return response.content.strip()
            
        except Exception as e:
            error_msg = f"Error getting LLM response: {e}"
            print(f"❌ {error_msg}")
            return f"⚠️ {error_msg}"
    
    def speak_text(self, text):
        """Convert text to speech (if enabled)."""
        if not Config.ENABLE_TTS or not self.tts_engine:
            return
            
        try:
            # Uncomment when TTS is needed
            # self.tts_engine.say(text)
            # self.tts_engine.runAndWait()
            pass
        except Exception as e:
            print(f"❌ TTS Error: {e}")
    
    def monitor_predictions(self):
        """Monitor the shared predictions file from prediction_improvement_TRANSFORMERS.py"""
        shared_file = Path(Config.SHARED_PREDICTIONS_FILE)
        last_modified = 0
        
        while self.running:
            try:
                if shared_file.exists():
                    current_modified = shared_file.stat().st_mtime
                    
                    if current_modified > last_modified:
                        last_modified = current_modified
                        
                        # Read new predictions
                        with open(shared_file, 'r') as f:
                            data = json.load(f)
                            
                        if data.get('predictions'):
                            for prediction in data['predictions']:
                                self.prediction_queue.put(prediction)
                                self.last_prediction_time = time.time()
                            
                            # Clear processed predictions
                            with open(shared_file, 'w') as f:
                                json.dump({'predictions': []}, f)
                
                # Check if we should process accumulated predictions
                if (self.last_prediction_time and 
                    time.time() - self.last_prediction_time > Config.PREDICTION_TIMEOUT and 
                    not self.prediction_queue.empty()):
                    
                    self.process_accumulated_predictions()
                
                time.sleep(Config.MONITOR_INTERVAL)
                
            except Exception as e:
                print(f"❌ Error monitoring predictions: {e}")
                time.sleep(1)
    
    def process_accumulated_predictions(self):
        """Process all accumulated predictions."""
        predictions = []
        
        # Get all predictions from queue
        while not self.prediction_queue.empty():
            try:
                prediction = self.prediction_queue.get_nowait()
                predictions.append(prediction)
            except queue.Empty:
                break
        
        if predictions:
            sentence_text = " ".join(predictions)
            print(f"\n📝 Accumulated sentence (Transformer): '{sentence_text}'")
            
            # Get LLM response
            refined_text = self.get_llm_response(sentence_text)
            
            # Display in popup
            self.display_result(sentence_text, refined_text)
            
            # Speak if enabled
            if Config.ENABLE_TTS:
                threading.Thread(target=self.speak_text, args=(refined_text,), daemon=True).start()
        
        self.last_prediction_time = None
    
    def display_result(self, original_text, refined_text):
        """Display results in popup window."""
        if hasattr(self, 'popup_window') and self.popup_window:
            # Update existing window
            self.update_popup_display(original_text, refined_text)
        else:
            # Create new popup window
            self.create_popup_window(original_text, refined_text)
    
    def create_popup_window(self, original_text, refined_text):
        """Create popup window for displaying results."""
        self.popup_window = tk.Toplevel()
        self.popup_window.title("🤖 LLM SASL Interpreter (Transformer)")
        self.popup_window.geometry("500x400")
        self.popup_window.configure(bg='#2b2b45')  # Slightly different color for transformer
        
        # Make it stay on top
        self.popup_window.attributes('-topmost', True)
        
        # Header
        header = tk.Label(self.popup_window, 
                         text="🤖 AI Sign Language Interpreter (Transformer)", 
                         font=("Arial", 14, "bold"),
                         bg='#2b2b45', fg='#ffffff')
        header.pack(pady=10)
        
        # Original predictions
        orig_label = tk.Label(self.popup_window, 
                             text="📋 Detected Signs:", 
                             font=("Arial", 10, "bold"),
                             bg='#2b2b45', fg='#ffaa00')
        orig_label.pack(anchor='w', padx=10)
        
        self.orig_text = scrolledtext.ScrolledText(self.popup_window, 
                                                  height=3, 
                                                  font=("Arial", 10),
                                                  bg='#404060', fg='#ffffff',
                                                  wrap=tk.WORD)
        self.orig_text.pack(fill='x', padx=10, pady=(0, 10))
        
        # Refined text
        refined_label = tk.Label(self.popup_window, 
                                text="🤖 AI Interpretation:", 
                                font=("Arial", 10, "bold"),
                                bg='#2b2b45', fg='#00ff88')
        refined_label.pack(anchor='w', padx=10)
        
        self.refined_text = scrolledtext.ScrolledText(self.popup_window, 
                                                     height=6, 
                                                     font=("Arial", 11),
                                                     bg='#404060', fg='#ffffff',
                                                     wrap=tk.WORD)
        self.refined_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Status bar
        self.status_label = tk.Label(self.popup_window, 
                                    text=f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')} | Transformer Model", 
                                    font=("Arial", 8),
                                    bg='#2b2b45', fg='#888888')
        self.status_label.pack(side='bottom', fill='x', padx=10, pady=5)
        
        # Initial content
        self.update_popup_display(original_text, refined_text)
        
        # Handle window close
        self.popup_window.protocol("WM_DELETE_WINDOW", self.on_popup_close)
    
    def update_popup_display(self, original_text, refined_text):
        """Update the popup window with new content."""
        if not hasattr(self, 'popup_window') or not self.popup_window:
            return
            
        try:
            # Update original text
            self.orig_text.delete(1.0, tk.END)
            self.orig_text.insert(1.0, original_text)
            
            # Update refined text
            self.refined_text.delete(1.0, tk.END)
            self.refined_text.insert(1.0, refined_text)
            
            # Update timestamp
            self.status_label.config(text=f"🔄 Last updated: {datetime.now().strftime('%H:%M:%S')} | Transformer Model")
            
            # Flash the window to get attention
            self.popup_window.attributes('-topmost', False)
            self.popup_window.attributes('-topmost', True)
            
        except Exception as e:
            print(f"❌ Error updating popup: {e}")
    
    def on_popup_close(self):
        """Handle popup window close."""
        if hasattr(self, 'popup_window'):
            self.popup_window.destroy()
            self.popup_window = None
    
    def start(self):
        """Start the LLM prediction improvement system."""
        print("=" * 80)
        print("🤖 LLM PREDICTION IMPROVEMENT - TRANSFORMER MODEL")
        print("=" * 80)
        print("✅ Starting LLM integration...")
        print(f"📁 Monitoring: {Config.SHARED_PREDICTIONS_FILE}")
        print(f"⏰ Timeout: {Config.PREDICTION_TIMEOUT} seconds")
        print(f"🔇 TTS: {'Enabled' if Config.ENABLE_TTS else 'Disabled'}")
        print("=" * 80)
        
        self.running = True
        
        # Create shared predictions file
        shared_file = Path(Config.SHARED_PREDICTIONS_FILE)
        if not shared_file.exists():
            with open(shared_file, 'w') as f:
                json.dump({'predictions': []}, f)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_predictions, daemon=True)
        monitor_thread.start()
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping LLM integration...")
            self.running = False

# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    predictor = LLMPredictorTransformer()
    predictor.start()