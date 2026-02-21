/**
 * Conversation Service
 *
 * Manages the two-way conversation flow between:
 * - Deaf person (signs → text → voice)
 * - Hearing person (voice → text)
 *
 * Orchestrates:
 * 1. Sign prediction from video via backend WebSocket
 * 2. Sentence refinement via backend LLM
 * 3. Text-to-speech for hearing person
 * 4. Speech-to-text for deaf person
 */

import {
  predictionService,
  type PredictionBatch,
  type BackendStatus,
  type RefinedResult,
} from './predictionService';
import { llmService, type RefinementResult } from './llmService';

export type Speaker = 'deaf' | 'hearing';

export interface ConversationMessage {
  id: string;
  speaker: Speaker;
  text: string;
  timestamp: number;
  type: 'sign' | 'voice';
}

export interface ConversationState {
  messages: ConversationMessage[];
  currentSpeaker: Speaker;
  isProcessing: boolean;
  lastPrediction: PredictionBatch | null;
  lastRefinement: RefinementResult | null;
  backendConnected: boolean;
  backendStatus: BackendStatus | null;
}

export interface ConversationCallbacks {
  onNewMessage?: (message: ConversationMessage) => void;
  onProcessingStart?: () => void;
  onProcessingEnd?: () => void;
  onRefinedText?: (text: string) => void;
  onError?: (error: string) => void;
  onBackendStatus?: (status: BackendStatus) => void;
  onConnectionChange?: (connected: boolean) => void;
  onSpeakingChange?: (isSpeaking: boolean) => void;
  onSpeechTranscript?: (text: string, isFinal: boolean) => void;
  onListeningChange?: (isListening: boolean) => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type SpeechRecognitionType = any;

class ConversationService {
  private state: ConversationState = {
    messages: [],
    currentSpeaker: 'deaf',
    isProcessing: false,
    lastPrediction: null,
    lastRefinement: null,
    backendConnected: false,
    backendStatus: null,
  };

  private callbacks: ConversationCallbacks = {};
  private speechSynthesis: SpeechSynthesis | null = null;
  private speechRecognition: SpeechRecognitionType | null = null;
  private isListening: boolean = false;
  private shouldBeListening: boolean = false;
  private sttRetryCount: number = 0;
  private readonly MAX_STT_RETRIES = 5;

  constructor() {
    // Initialize speech synthesis
    if ('speechSynthesis' in window) {
      this.speechSynthesis = window.speechSynthesis;
    }

    // Initialize speech recognition
    const SpeechRecognitionAPI =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognitionAPI) {
      this.speechRecognition = new SpeechRecognitionAPI();
      this.speechRecognition.continuous = true;
      this.speechRecognition.interimResults = true;
      this.speechRecognition.lang = 'en-US';
    }
  }

  /**
   * Set callbacks for conversation events.
   */
  setCallbacks(callbacks: ConversationCallbacks): void {
    this.callbacks = callbacks;
  }

  /**
   * Initialize all services.
   */
  async initialize(): Promise<boolean> {
    try {
      // Initialize prediction service (WebSocket to backend)
      const predictionReady = await predictionService.initialize();

      // Initialize LLM service (health check)
      await llmService.initialize();

      // Set up prediction callback — fires when model detects a sign
      predictionService.onPrediction(this.handlePrediction.bind(this));

      // Set up backend status callback — fires on every frame with buffer/movement info
      predictionService.onStatus((status: BackendStatus) => {
        this.state.backendStatus = status;
        this.callbacks.onBackendStatus?.(status);
      });

      // Set up refined text callback — fires when LLM finishes refining
      predictionService.onRefined((result: RefinedResult) => {
        this.handleRefinedText(result);
      });

      // Set up connection callback
      predictionService.onConnection((connected: boolean) => {
        this.state.backendConnected = connected;
        this.callbacks.onConnectionChange?.(connected);
      });

      // Set up speech recognition callback
      if (this.speechRecognition) {
        this.speechRecognition.onresult =
          this.handleSpeechResult.bind(this);
        this.speechRecognition.onerror =
          this.handleSpeechError.bind(this);
      }

      this.state.backendConnected = predictionService.isBackendConnected();

      return predictionReady;
    } catch (error) {
      console.error('Failed to initialize conversation service:', error);
      return false;
    }
  }

  /**
   * Start a conversation session.
   */
  startConversation(): void {
    this.state.messages = [];
    this.state.currentSpeaker = 'deaf';
    this.state.isProcessing = false;
  }

  /**
   * Process sign language video frame — call this for each frame from the camera.
   */
  processVideoFrame(frame: ImageData): void {
    if (this.state.currentSpeaker === 'deaf') {
      predictionService.addFrame(frame);
    }
  }

  /**
   * Handle prediction results from the model.
   */
  private async handlePrediction(result: PredictionBatch): Promise<void> {
    this.state.lastPrediction = result;

    this.callbacks.onProcessingStart?.();

    try {
      // If backend is connected, the backend handles LLM refinement automatically
      // via the WebSocket. But for mock mode, we refine locally:
      if (predictionService.isMockMode()) {
        const context = this.getConversationContext();
        const refinement = await llmService.refineSentence(
          result.rawWords,
          context
        );
        this.state.lastRefinement = refinement;

        this.callbacks.onRefinedText?.(refinement.refinedText);

        // Speak the refined text
        await this.speakText(refinement.refinedText);

        // Add to conversation
        this.addMessage({
          id: this.generateId(),
          speaker: 'deaf',
          text: refinement.refinedText,
          timestamp: Date.now(),
          type: 'sign',
        });

        // Switch to hearing person
        this.state.currentSpeaker = 'hearing';
        this.startListening();
      }
      // In backend mode, predictions arrive one at a time.
      // The "refined" message comes later when the backend LLM processes
      // accumulated predictions. We just log individual predictions here.
    } catch (error) {
      console.error('Prediction handling error:', error);
      this.callbacks.onError?.('Failed to process sign language');
    } finally {
      this.callbacks.onProcessingEnd?.();
    }
  }

  /**
   * Handle refined text from the backend (WebSocket "refined" message).
   */
  private async handleRefinedText(result: RefinedResult): Promise<void> {
    const refinement: RefinementResult = {
      originalText: result.original,
      refinedText: result.refined,
      isComplete: /[.!?]$/.test(result.refined.trim()),
    };
    this.state.lastRefinement = refinement;

    this.callbacks.onRefinedText?.(refinement.refinedText);

    // Speak the refined text
    await this.speakText(refinement.refinedText);

    // Add to conversation
    this.addMessage({
      id: this.generateId(),
      speaker: 'deaf',
      text: refinement.refinedText,
      timestamp: Date.now(),
      type: 'sign',
    });

    // Switch to hearing person
    this.state.currentSpeaker = 'hearing';
    this.startListening();
  }

  /**
   * Convert text to speech — tries ElevenLabs via backend first, falls back to browser.
   */
  private async speakText(text: string): Promise<void> {
    // Notify UI that speaking has started
    this.callbacks.onSpeakingChange?.(true);

    try {
      // Try ElevenLabs TTS via backend
      const spoken = await this.speakWithElevenLabs(text);
      if (spoken) return;
    } catch (err) {
      console.warn('[SignBridge] ElevenLabs TTS failed, falling back to browser:', err);
    }

    // Fallback: browser SpeechSynthesis
    try {
      await this.speakWithBrowser(text);
    } catch (err) {
      console.error('[SignBridge] Browser TTS also failed:', err);
      this.callbacks.onSpeakingChange?.(false);
    }
  }

  /**
   * Speak text using ElevenLabs TTS via backend /api/tts endpoint.
   * Returns true if successful, false otherwise.
   */
  private async speakWithElevenLabs(text: string): Promise<boolean> {
    // Try proxied URL first, then direct backend
    const urls = ['/api/tts', 'http://localhost:8000/api/tts'];

    for (const url of urls) {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text }),
        });

        if (!response.ok) {
          console.warn(`[SignBridge] ElevenLabs TTS returned ${response.status}`);
          continue;
        }

        // Check if we got audio back (not a JSON error)
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.includes('audio')) {
          console.warn('[SignBridge] ElevenLabs TTS did not return audio');
          continue;
        }

        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);

        console.log(`[SignBridge] 🔊 ElevenLabs TTS playing: "${text.substring(0, 50)}..."`);

        return new Promise<boolean>((resolve) => {
          audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
            this.callbacks.onSpeakingChange?.(false);
            resolve(true);
          };
          audio.onerror = () => {
            URL.revokeObjectURL(audioUrl);
            this.callbacks.onSpeakingChange?.(false);
            resolve(false);
          };
          audio.play().catch(() => {
            URL.revokeObjectURL(audioUrl);
            this.callbacks.onSpeakingChange?.(false);
            resolve(false);
          });
        });
      } catch {
        continue;
      }
    }

    return false;
  }

  /**
   * Fallback: speak text using browser SpeechSynthesis.
   */
  private async speakWithBrowser(text: string): Promise<void> {
    if (!this.speechSynthesis) {
      console.warn('[SignBridge] Browser speech synthesis not available');
      this.callbacks.onSpeakingChange?.(false);
      return;
    }

    this.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.volume = 1;

    const voices = this.speechSynthesis.getVoices();
    const naturalVoice = voices.find(
      (v) => v.lang.startsWith('en') && v.name.includes('Natural')
    );
    if (naturalVoice) {
      utterance.voice = naturalVoice;
    }

    console.log(`[SignBridge] 🔊 Browser TTS playing: "${text.substring(0, 50)}..."`);

    return new Promise((resolve) => {
      utterance.onend = () => {
        this.callbacks.onSpeakingChange?.(false);
        resolve();
      };
      utterance.onerror = () => {
        this.callbacks.onSpeakingChange?.(false);
        resolve();
      };
      this.speechSynthesis?.speak(utterance);
    });
  }

  /**
   * Start listening for hearing person's voice.
   */
  startListening(): void {
    if (!this.speechRecognition) {
      console.warn('[SignBridge] Speech recognition not available in this browser');
      this.callbacks.onError?.('Speech recognition not available. Try using Chrome.');
      return;
    }

    this.shouldBeListening = true;
    this.sttRetryCount = 0;

    if (this.isListening) {
      console.log('[SignBridge] Already listening, skipping start');
      return;
    }

    this.doStartListening();
  }

  /**
   * Internal: actually start the speech recognition engine.
   */
  private doStartListening(): void {
    if (!this.speechRecognition || !this.shouldBeListening) return;

    try {
      // Re-attach handlers every time (they may get cleared)
      this.speechRecognition.onresult = this.handleSpeechResult.bind(this);
      this.speechRecognition.onerror = this.handleSpeechError.bind(this);
      this.speechRecognition.onend = () => {
        console.log('[SignBridge] SpeechRecognition ended');
        this.isListening = false;

        // Auto-restart if we should still be listening
        if (this.shouldBeListening && this.sttRetryCount < this.MAX_STT_RETRIES) {
          this.sttRetryCount++;
          console.log(`[SignBridge] Auto-restarting speech recognition (attempt ${this.sttRetryCount}/${this.MAX_STT_RETRIES})`);
          setTimeout(() => this.doStartListening(), 500);
        } else if (this.sttRetryCount >= this.MAX_STT_RETRIES) {
          console.error('[SignBridge] Max STT retries reached. Giving up.');
          this.callbacks.onError?.('Speech recognition failed after multiple retries. Check microphone & internet.');
          this.callbacks.onListeningChange?.(false);
        }
      };

      this.speechRecognition.start();
      this.isListening = true;
      this.callbacks.onListeningChange?.(true);
      console.log('[SignBridge] 🎙️ Speech recognition started — speak now');
    } catch (err) {
      console.error('[SignBridge] Speech recognition start error:', err);
      this.isListening = false;

      // Retry after a delay
      if (this.shouldBeListening && this.sttRetryCount < this.MAX_STT_RETRIES) {
        this.sttRetryCount++;
        setTimeout(() => this.doStartListening(), 1000);
      }
    }
  }

  /**
   * Stop listening.
   */
  stopListening(): void {
    this.shouldBeListening = false;
    this.sttRetryCount = 0;

    if (!this.speechRecognition || !this.isListening) return;

    try {
      this.speechRecognition.stop();
      this.isListening = false;
      this.callbacks.onListeningChange?.(false);
      console.log('[SignBridge] 🎙️ Speech recognition stopped');
    } catch {
      console.error('[SignBridge] Error stopping speech recognition');
    }
  }

  /**
   * Handle speech recognition results.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private handleSpeechResult(event: any): void {
    const results = event.results;
    if (results.length > 0) {
      const lastResult = results[results.length - 1];
      const transcript = lastResult[0].transcript.trim();

      if (!lastResult.isFinal) {
        // Interim result — show partial text in UI
        if (transcript) {
          this.callbacks.onSpeechTranscript?.(transcript, false);
          console.log(`[SignBridge] 🎙️ Hearing (interim): "${transcript}"`);
        }
      } else {
        // Final result — commit to conversation
        if (transcript) {
          console.log(`[SignBridge] 🎙️ Hearing (final): "${transcript}"`);
          this.callbacks.onSpeechTranscript?.(transcript, true);
          this.stopListening();
          this.addMessage({
            id: this.generateId(),
            speaker: 'hearing',
            text: transcript,
            timestamp: Date.now(),
            type: 'voice',
          });
          this.state.currentSpeaker = 'deaf';
          predictionService.clearBuffer();
        }
      }
    }
  }

  /**
   * Handle speech recognition errors.
   */
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private handleSpeechError(event: any): void {
    const error = event.error;
    console.error('[SignBridge] Speech recognition error:', error);

    // These errors are transient — the onend handler will auto-restart
    const transientErrors = ['network', 'aborted', 'no-speech', 'audio-capture'];
    if (transientErrors.includes(error)) {
      console.log(`[SignBridge] Transient STT error '${error}' — will auto-restart`);
      return; // onend handler will fire and auto-restart
    }

    // Fatal error
    this.isListening = false;
    this.shouldBeListening = false;
    this.callbacks.onListeningChange?.(false);
    this.callbacks.onError?.('Speech recognition error: ' + error);
  }

  /**
   * Add a message to the conversation.
   */
  private addMessage(message: ConversationMessage): void {
    this.state.messages.push(message);
    this.callbacks.onNewMessage?.(message);
  }

  /**
   * Get conversation context for LLM.
   */
  private getConversationContext(): string {
    const recentMessages = this.state.messages.slice(-3);
    return recentMessages.map((m) => `${m.speaker}: ${m.text}`).join('\n');
  }

  // --- PUBLIC GETTERS ---

  getMessages(): ConversationMessage[] {
    return [...this.state.messages];
  }

  getCurrentSpeaker(): Speaker {
    return this.state.currentSpeaker;
  }

  isProcessing(): boolean {
    return this.state.isProcessing;
  }

  isListeningForSpeech(): boolean {
    return this.isListening;
  }

  isBackendConnected(): boolean {
    return this.state.backendConnected;
  }

  getBackendStatus(): BackendStatus | null {
    return this.state.backendStatus;
  }

  clearConversation(): void {
    this.state.messages = [];
    this.state.currentSpeaker = 'deaf';
    predictionService.clearBuffer();
  }

  hasSpeechSynthesis(): boolean {
    return this.speechSynthesis !== null;
  }

  hasSpeechRecognition(): boolean {
    return this.speechRecognition !== null;
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const conversationService = new ConversationService();
export default conversationService;
