/**
 * Sign Language Prediction Service
 *
 * Connects to the Python FastAPI backend via WebSocket to stream video frames
 * and receive real-time transformer model predictions.
 *
 * Falls back to mock mode when the backend is unavailable.
 */

export interface PredictionResult {
  word: string;
  confidence: number;
  timestamp: number;
}

export interface PredictionBatch {
  predictions: PredictionResult[];
  rawWords: string[];
}

export interface BackendStatus {
  bufferSize: number;
  bufferMax: number;
  movementDetected: boolean;
  consecutiveFrames: number;
  totalPredictions: number;
  sentence: string[];
}

export interface RefinedResult {
  original: string;
  refined: string;
}

type PredictionCallback = (result: PredictionBatch) => void;
type StatusCallback = (status: BackendStatus) => void;
type RefinedCallback = (result: RefinedResult) => void;
type ConnectionCallback = (connected: boolean) => void;

class PredictionService {
  private ws: WebSocket | null = null;
  private isConnected: boolean = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly RECONNECT_DELAY = 3000;
  private readonly WS_URL: string;

  // Frame sending state
  private canvas: HTMLCanvasElement | null = null;
  private isProcessing: boolean = false;
  private frameSkipCount: number = 0;
  private readonly FRAME_SKIP: number = 2; // Send every 3rd frame to reduce load

  // Fallback mock state
  private useMock: boolean = false;
  private frameBuffer: ImageData[] = [];
  private readonly BUFFER_SIZE = 30;

  // Callbacks
  private onPredictionCallback: PredictionCallback | null = null;
  private onStatusCallback: StatusCallback | null = null;
  private onRefinedCallback: RefinedCallback | null = null;
  private onConnectionCallback: ConnectionCallback | null = null;

  constructor() {
    // Use relative WebSocket URL so the Vite proxy handles it
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.WS_URL = `${protocol}//${window.location.host}/ws/predict`;

    // Hidden canvas for frame encoding
    this.canvas = document.createElement('canvas');
  }

  /**
   * Initialize the prediction service.
   * Attempts WebSocket connection to backend; falls back to mock on failure.
   */
  async initialize(): Promise<boolean> {
    try {
      // Try to connect to the backend
      const connected = await this.connectWebSocket();
      if (connected) {
        this.useMock = false;
        console.log('✅ Prediction service connected to backend');
        return true;
      }
    } catch {
      console.warn('Backend not available, using mock mode');
    }

    // Fallback to mock mode
    this.useMock = true;
    console.log('⚠️ Prediction service running in mock mode');
    return true;
  }

  /**
   * Connect to the backend WebSocket.
   */
  private connectWebSocket(): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        this.ws = new WebSocket(this.WS_URL);

        const timeout = setTimeout(() => {
          if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
            this.ws.close();
            resolve(false);
          }
        }, 5000);

        this.ws.onopen = () => {
          clearTimeout(timeout);
          this.isConnected = true;
          this.useMock = false;
          console.log('WebSocket connected');
          this.onConnectionCallback?.(true);
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = () => {
          this.isConnected = false;
          this.onConnectionCallback?.(false);
          console.log('WebSocket disconnected');
          this.scheduleReconnect();
        };

        this.ws.onerror = (err) => {
          console.error('WebSocket error:', err);
          clearTimeout(timeout);
          resolve(false);
        };
      } catch {
        resolve(false);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages from the backend.
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'prediction': {
          if (data.accepted && this.onPredictionCallback) {
            const batch: PredictionBatch = {
              predictions: [{
                word: data.word,
                confidence: data.confidence,
                timestamp: Date.now(),
              }],
              rawWords: data.sentence || [data.word],
            };
            this.onPredictionCallback(batch);
          }
          break;
        }

        case 'status': {
          this.onStatusCallback?.({
            bufferSize: data.bufferSize,
            bufferMax: data.bufferMax,
            movementDetected: data.movementDetected,
            consecutiveFrames: data.consecutiveFrames,
            totalPredictions: data.totalPredictions,
            sentence: data.sentence,
          });
          break;
        }

        case 'refined': {
          this.onRefinedCallback?.({
            original: data.original,
            refined: data.refined,
          });
          break;
        }

        case 'reset_ack':
          console.log('Backend state reset');
          break;

        default:
          break;
      }
    } catch (err) {
      console.error('Error parsing WebSocket message:', err);
    }
  }

  /**
   * Schedule a reconnection attempt.
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      console.log('Attempting WebSocket reconnect...');
      const connected = await this.connectWebSocket();
      if (!connected) {
        this.useMock = true;
      }
    }, this.RECONNECT_DELAY);
  }

  // --- CALLBACK SETTERS ---

  onPrediction(callback: PredictionCallback): void {
    this.onPredictionCallback = callback;
  }

  onStatus(callback: StatusCallback): void {
    this.onStatusCallback = callback;
  }

  onRefined(callback: RefinedCallback): void {
    this.onRefinedCallback = callback;
  }

  onConnection(callback: ConnectionCallback): void {
    this.onConnectionCallback = callback;
  }

  // --- FRAME PROCESSING ---

  /**
   * Add a video frame for processing.
   * In WebSocket mode: encodes frame as JPEG and sends to backend.
   * In mock mode: buffers frames and returns mock predictions.
   */
  addFrame(frame: ImageData): void {
    if (this.useMock) {
      this.addFrameMock(frame);
      return;
    }

    if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    // Skip frames to reduce bandwidth
    this.frameSkipCount++;
    if (this.frameSkipCount % (this.FRAME_SKIP + 1) !== 0) {
      return;
    }

    this.sendFrame(frame);
  }

  /**
   * Encode an ImageData frame to JPEG and send over WebSocket.
   */
  private sendFrame(frame: ImageData): void {
    if (!this.canvas || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    this.canvas.width = frame.width;
    this.canvas.height = frame.height;
    const ctx = this.canvas.getContext('2d');
    if (!ctx) return;

    ctx.putImageData(frame, 0, 0);

    // Convert to JPEG blob and send as binary
    this.canvas.toBlob(
      (blob) => {
        if (blob && this.ws && this.ws.readyState === WebSocket.OPEN) {
          blob.arrayBuffer().then((buffer) => {
            this.ws?.send(buffer);
          });
        }
      },
      'image/jpeg',
      0.7 // Quality — balance between size and quality
    );
  }

  // --- MOCK MODE (fallback when backend is unavailable) ---

  private addFrameMock(frame: ImageData): void {
    if (this.isProcessing) return;

    this.frameBuffer.push(frame);
    if (this.frameBuffer.length >= this.BUFFER_SIZE) {
      this.processFramesMock();
    }
  }

  private async processFramesMock(): Promise<void> {
    if (this.frameBuffer.length === 0) return;

    this.isProcessing = true;
    this.frameBuffer = [];

    try {
      // Simulate processing delay
      await new Promise((resolve) => setTimeout(resolve, 500));

      const mockWords = ['HELLO', 'HOW', 'ARE', 'YOU'];
      const predictions: PredictionResult[] = mockWords.map((word, i) => ({
        word,
        confidence: 0.85 + Math.random() * 0.1,
        timestamp: Date.now() + i * 100,
      }));

      this.onPredictionCallback?.({ predictions, rawWords: mockWords });
    } catch (error) {
      console.error('Mock prediction error:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  // --- CONTROL METHODS ---

  /**
   * Flush the buffer — request backend to process any pending predictions via LLM.
   */
  async flushBuffer(): Promise<void> {
    if (this.useMock) {
      if (this.frameBuffer.length > 0) {
        await this.processFramesMock();
      }
      return;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'flush' }));
    }
  }

  /**
   * Reset the backend state for a new conversation.
   */
  resetState(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'reset' }));
    }
  }

  /**
   * Clear the frame buffer without processing.
   */
  clearBuffer(): void {
    this.frameBuffer = [];
    this.resetState();
  }

  /**
   * Check if the backend is connected.
   */
  isBackendConnected(): boolean {
    return this.isConnected && !this.useMock;
  }

  /**
   * Check if service is ready (always true — mock mode is always available).
   */
  isReady(): boolean {
    return true;
  }

  /**
   * Check if running in mock mode.
   */
  isMockMode(): boolean {
    return this.useMock;
  }

  /**
   * Get current buffer size (mock mode only).
   */
  getBufferSize(): number {
    return this.frameBuffer.length;
  }

  /**
   * Disconnect and clean up.
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }
}

// Export singleton instance
export const predictionService = new PredictionService();
export default predictionService;
