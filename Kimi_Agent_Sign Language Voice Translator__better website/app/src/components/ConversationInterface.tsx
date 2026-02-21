import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Mic,
  Video,
  MessageCircle,
  Volume2,
  RotateCcw,
  Hand,
  User,
  Loader2,
  Wifi,
  WifiOff,
  Activity,
  AudioLines,
  Send,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  conversationService,
  type ConversationMessage,
  type Speaker,
} from '../services/conversationService';
import { predictionService, type BackendStatus } from '../services/predictionService';

export default function ConversationInterface() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [isActive, setIsActive] = useState(false);
  const [hasCameraPermission, setHasCameraPermission] = useState<boolean | null>(null);
  const [currentSpeaker, setCurrentSpeaker] = useState<Speaker>('deaf');
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const [backendStatus, setBackendStatus] = useState<BackendStatus | null>(null);
  const [lastRefined, setLastRefined] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [pendingCameraStart, setPendingCameraStart] = useState(false);

  // Auto-scroll conversation to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);



  // Initialize conversation service
  useEffect(() => {
    conversationService.setCallbacks({
      onNewMessage: (message) => {
        setMessages((prev) => [...prev, message]);
        setCurrentSpeaker(message.speaker === 'deaf' ? 'hearing' : 'deaf');
      },
      onProcessingStart: () => setIsProcessing(true),
      onProcessingEnd: () => setIsProcessing(false),
      onRefinedText: (text) => {
        setLastRefined(text);
        console.log('Refined text:', text);
      },
      onError: (error) => {
        console.error('Conversation error:', error);
        setIsProcessing(false);
      },
      onBackendStatus: (status) => {
        setBackendStatus(status);
      },
      onConnectionChange: (connected) => {
        setBackendConnected(connected);
      },
      onSpeakingChange: (speaking) => {
        setIsSpeaking(speaking);
      },
    });

    conversationService.initialize().then(() => {
      setBackendConnected(conversationService.isBackendConnected());
    });

    return () => {
      stopCamera();
      conversationService.stopListening();
    };
  }, []);

  // Use a ref for currentSpeaker so the animation loop always reads the latest value
  const currentSpeakerRef = useRef<Speaker>(currentSpeaker);
  useEffect(() => {
    currentSpeakerRef.current = currentSpeaker;
  }, [currentSpeaker]);

  // Start camera for sign detection
  const startCamera = useCallback(async () => {
    console.log('[SignBridge] startCamera called, videoRef:', !!videoRef.current);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
        audio: false,
      });
      console.log('[SignBridge] Camera stream obtained:', stream.getTracks().map(t => t.label));

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        console.log('[SignBridge] Stream attached to video element');

        // Wait for the video to load metadata and start playing
        await new Promise<void>((resolve) => {
          const video = videoRef.current!;
          video.onloadedmetadata = () => {
            console.log('[SignBridge] Video metadata loaded:', video.videoWidth, 'x', video.videoHeight);
            video.play()
              .then(() => {
                console.log('[SignBridge] Video playing successfully');
                resolve();
              })
              .catch((e) => {
                console.error('[SignBridge] Video play failed:', e);
                resolve();
              });
          };
          // In case metadata is already loaded
          if (video.readyState >= 1) {
            console.log('[SignBridge] Video metadata already loaded, readyState:', video.readyState);
            video.play()
              .then(() => {
                console.log('[SignBridge] Video playing (already loaded)');
                resolve();
              })
              .catch((e) => {
                console.error('[SignBridge] Video play failed (already loaded):', e);
                resolve();
              });
          }
        });
      } else {
        console.error('[SignBridge] videoRef.current is NULL — video element not yet rendered!');
      }

      setHasCameraPermission(true);
      startFrameCapture();
    } catch (err) {
      console.error('[SignBridge] Camera error:', err);
      setHasCameraPermission(false);
    }
  }, []);

  // Start camera AFTER the component renders the <video> element
  useEffect(() => {
    if (pendingCameraStart && isActive && videoRef.current) {
      console.log('[SignBridge] Video element ready, starting camera...');
      startCamera();
      setPendingCameraStart(false);
    }
  }, [pendingCameraStart, isActive, startCamera]);

  // Stop camera
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  // Capture frames from video for prediction
  const startFrameCapture = useCallback(() => {
    console.log('[SignBridge] startFrameCapture called, canvas:', !!canvasRef.current, 'video:', !!videoRef.current);
    if (!canvasRef.current || !videoRef.current) {
      console.error('[SignBridge] Cannot start frame capture — missing canvas or video ref');
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frameCount = 0;
    const captureFrame = () => {
      const video = videoRef.current;
      if (video && currentSpeakerRef.current === 'deaf' && video.videoWidth > 0 && video.videoHeight > 0) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        try {
          const frameData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          conversationService.processVideoFrame(frameData);
          frameCount++;
          if (frameCount % 100 === 0) {
            console.log(`[SignBridge] Sent ${frameCount} frames to prediction service`);
          }
        } catch {
          // Ignore cross-origin errors
        }
      }

      animationFrameRef.current = requestAnimationFrame(captureFrame);
    };

    captureFrame();
  }, []);

  // Start conversation
  const startConversation = async () => {
    console.log('[SignBridge] Starting conversation...');
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('[SignBridge] Microphone permission granted');
    } catch (err) {
      console.error('[SignBridge] Microphone permission denied:', err);
      return;
    }

    // Set active FIRST so the <video> element renders,
    // then start camera in the useEffect above
    conversationService.startConversation();
    setIsActive(true);
    setCurrentSpeaker('deaf');
    setPendingCameraStart(true);
  };

  // Stop conversation
  const stopConversation = () => {
    stopCamera();
    conversationService.stopListening();
    conversationService.clearConversation();
    setIsActive(false);
    setMessages([]);
    setLastRefined(null);
    setBackendStatus(null);
    setIsSpeaking(false);
  };

  // Manually flush accumulated predictions to LLM
  const triggerPrediction = () => {
    predictionService.flushBuffer();
  };

  // Get last message from hearing person
  const lastHearingMessage = messages.filter((m) => m.speaker === 'hearing').pop();

  // Calculate buffer progress percentage
  const bufferProgress = backendStatus
    ? (backendStatus.bufferSize / backendStatus.bufferMax) * 100
    : 0;

  // Check if there are pending predictions to flush
  const hasPendingPredictions = backendStatus && backendStatus.sentence.length > 0;

  if (!isActive) {
    return (
      <div className="bg-kaleo-cream rounded-2xl p-8 text-center">
        <div className="w-20 h-20 bg-kaleo-terracotta/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <MessageCircle className="w-10 h-10 text-kaleo-terracotta" />
        </div>
        <h3 className="font-display text-2xl text-kaleo-earth mb-3">
          Start a Conversation
        </h3>
        <p className="text-kaleo-earth/70 mb-6 max-w-md mx-auto">
          Enable your camera and microphone to begin communicating. Sign to
          speak, and hear responses converted to text.
        </p>

        {/* Backend Connection Status */}
        <div className="flex items-center justify-center gap-2 mb-4">
          {backendConnected ? (
            <>
              <Wifi className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-600 font-medium">
                AI Backend Connected
              </span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-yellow-600 font-medium">
                Running in Demo Mode
              </span>
            </>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={startConversation}
            className="bg-kaleo-terracotta hover:bg-kaleo-earth text-kaleo-cream px-8 py-6 text-lg"
          >
            <Video className="w-5 h-5 mr-2" />
            Start Conversation
          </Button>
          <Button
            variant="outline"
            onClick={() => setShowDebug(!showDebug)}
            className="border-kaleo-terracotta text-kaleo-terracotta"
          >
            {showDebug ? 'Hide' : 'Show'} Debug Info
          </Button>
        </div>

        {showDebug && (
          <div className="mt-6 text-left bg-kaleo-sand/50 rounded-lg p-4 text-sm">
            <p className="font-medium text-kaleo-earth mb-2">System Status:</p>
            <ul className="space-y-1 text-kaleo-earth/70">
              <li>
                Backend:{' '}
                {backendConnected
                  ? '✓ Connected (Transformer Model)'
                  : '✗ Not Connected (Mock Mode)'}
              </li>
              <li>
                Speech Synthesis:{' '}
                {conversationService.hasSpeechSynthesis()
                  ? '✓ Available'
                  : '✗ Not Available'}
              </li>
              <li>
                Speech Recognition:{' '}
                {conversationService.hasSpeechRecognition()
                  ? '✓ Available'
                  : '✗ Not Available'}
              </li>
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-kaleo-cream rounded-2xl overflow-hidden shadow-lg">
      {/* Header */}
      <div className="bg-kaleo-terracotta px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
              }`}
          />
          <span className="text-kaleo-cream font-medium">
            {isSpeaking
              ? '🔊 Speaking your message...'
              : currentSpeaker === 'deaf'
                ? '🤟 Your Turn to Sign'
                : '🎙️ Listening for Response...'}
          </span>
          {/* Connection indicator */}
          {backendConnected ? (
            <Wifi className="w-4 h-4 text-green-300" />
          ) : (
            <WifiOff className="w-4 h-4 text-yellow-300" />
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={stopConversation}
          className="text-kaleo-cream hover:bg-kaleo-cream/20"
        >
          <RotateCcw className="w-4 h-4 mr-1" />
          End
        </Button>
      </div>

      <div className="grid md:grid-cols-2 gap-0">
        {/* ===== DEAF PERSON (Signer) VIEW ===== */}
        <div className="p-6 border-b md:border-b-0 md:border-r border-kaleo-sand">
          <div className="flex items-center gap-2 mb-4">
            <Hand className="w-5 h-5 text-kaleo-terracotta" />
            <h4 className="font-medium text-kaleo-earth">You (Sign)</h4>
            {currentSpeaker === 'deaf' && (
              <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-medium animate-pulse">
                YOUR TURN
              </span>
            )}
          </div>

          {/* Camera Preview — mirrored so you see yourself naturally */}
          <div className="relative aspect-video bg-kaleo-charcoal rounded-lg overflow-hidden mb-4">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
              style={{ transform: 'scaleX(-1)' }}
            />

            {/* Hidden canvas for frame capture */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Camera Status */}
            {!hasCameraPermission && (
              <div className="absolute inset-0 flex items-center justify-center bg-kaleo-charcoal/90">
                <p className="text-kaleo-cream text-sm">
                  Camera access required
                </p>
              </div>
            )}

            {/* Processing Indicator */}
            {isProcessing && (
              <div className="absolute top-2 right-2 bg-kaleo-terracotta/90 text-kaleo-cream px-3 py-1 rounded-full text-xs flex items-center gap-2">
                <Loader2 className="w-3 h-3 animate-spin" />
                Processing...
              </div>
            )}

            {/* ===== TURN-TAKING: Block signing when it's the hearing person's turn ===== */}
            {currentSpeaker === 'hearing' && (
              <div className="absolute inset-0 bg-kaleo-charcoal/70 backdrop-blur-sm flex flex-col items-center justify-center z-10 turn-block-overlay">
                <div className="w-16 h-16 rounded-full bg-amber-500/20 flex items-center justify-center mb-3 animate-pulse">
                  <AlertCircle className="w-8 h-8 text-amber-400" />
                </div>
                <p className="text-white font-medium text-base">
                  Wait — Other person is speaking
                </p>
                <p className="text-white/60 text-sm mt-1">
                  You'll be able to sign when they finish
                </p>
              </div>
            )}

            {/* ===== TTS Speaking Overlay ===== */}
            {isSpeaking && currentSpeaker === 'deaf' && (
              <div className="absolute inset-0 bg-kaleo-charcoal/60 backdrop-blur-sm flex flex-col items-center justify-center z-10">
                <div className="speaking-wave-container mb-3">
                  <div className="speaking-wave-bar" />
                  <div className="speaking-wave-bar" />
                  <div className="speaking-wave-bar" />
                  <div className="speaking-wave-bar" />
                  <div className="speaking-wave-bar" />
                </div>
                <p className="text-white font-medium">
                  🔊 Speaking your message...
                </p>
              </div>
            )}

            {/* Backend Status Overlay */}
            {backendConnected && backendStatus && currentSpeaker === 'deaf' && !isSpeaking && (
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                {/* Buffer Progress Bar */}
                <div className="mb-2">
                  <div className="flex justify-between text-xs text-white/80 mb-1">
                    <span>
                      Buffer: {backendStatus.bufferSize}/{backendStatus.bufferMax}
                    </span>
                    <span>
                      {backendStatus.movementDetected ? (
                        <span className="text-green-400 flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          Movement ({backendStatus.consecutiveFrames}f)
                        </span>
                      ) : (
                        <span className="text-yellow-400">No Movement</span>
                      )}
                    </span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all duration-300 ${bufferProgress >= 100
                        ? 'bg-green-400'
                        : 'bg-yellow-400'
                        }`}
                      style={{ width: `${Math.min(bufferProgress, 100)}%` }}
                    />
                  </div>
                </div>

                {/* Current sentence */}
                {backendStatus.sentence.length > 0 && (
                  <p className="text-white text-sm font-medium truncate">
                    📝 {backendStatus.sentence.join(' ')}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Process Sign Button — only show when there are pending predictions */}
          {hasPendingPredictions && currentSpeaker === 'deaf' && !isSpeaking && (
            <Button
              onClick={triggerPrediction}
              className="w-full bg-green-600 hover:bg-green-700 text-white py-3 flex items-center justify-center gap-2"
            >
              <Send className="w-4 h-4" />
              Send Message ({backendStatus?.sentence.join(' ')})
            </Button>
          )}
        </div>

        {/* ===== HEARING PERSON VIEW ===== */}
        <div className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-5 h-5 text-kaleo-terracotta" />
            <h4 className="font-medium text-kaleo-earth">
              Other Person (Voice)
            </h4>
            {currentSpeaker === 'hearing' && (
              <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium animate-pulse">
                THEIR TURN
              </span>
            )}
          </div>

          {/* Voice Status Panel */}
          <div className="relative aspect-video bg-kaleo-sand/50 rounded-lg flex flex-col items-center justify-center mb-4 overflow-hidden">
            {/* ===== TTS Speaking: Show animated audio indicator ===== */}
            {isSpeaking ? (
              <>
                <div className="speaking-wave-container mb-4">
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                  <div className="speaking-wave-bar speaking-wave-bar-lg" />
                </div>
                <p className="text-kaleo-earth font-medium text-lg">
                  🔊 Speaking...
                </p>
                <p className="text-kaleo-earth/60 text-sm mt-1">
                  Your signed message is being spoken aloud
                </p>
              </>
            ) : currentSpeaker === 'hearing' ? (
              <>
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-3">
                  <Mic className="w-8 h-8 text-blue-600 animate-pulse" />
                </div>
                <p className="text-kaleo-earth font-medium">🎙️ Listening...</p>
                <p className="text-kaleo-earth/60 text-sm mt-1">Speak now — your words will appear as text</p>
              </>
            ) : (
              <>
                {/* Deaf person's turn — hearing person waits */}
                <div className="absolute inset-0 bg-kaleo-sand/30 flex flex-col items-center justify-center">
                  <div className="w-16 h-16 bg-kaleo-terracotta/10 rounded-full flex items-center justify-center mb-3">
                    <Volume2 className="w-8 h-8 text-kaleo-terracotta/40" />
                  </div>
                  <p className="text-kaleo-earth/50 font-medium">Waiting for signs...</p>
                  <p className="text-kaleo-earth/40 text-sm mt-1">
                    The signer is composing their message
                  </p>
                </div>
              </>
            )}

            {/* Last Refined Text */}
            {lastRefined && !isSpeaking && (
              <div className="mt-3 px-4 py-2 bg-green-50 border border-green-200 rounded-lg max-w-[90%]">
                <p className="text-xs text-green-600 mb-0.5">AI says:</p>
                <p className="text-green-800 text-sm font-medium">
                  {lastRefined}
                </p>
              </div>
            )}
          </div>

          {/* Last Heard Text */}
          {lastHearingMessage && (
            <div className="bg-kaleo-sand rounded-lg p-3">
              <p className="text-xs text-kaleo-earth/60 mb-1">Last heard:</p>
              <p className="text-kaleo-earth">{lastHearingMessage.text}</p>
            </div>
          )}
        </div>
      </div>

      {/* Conversation History */}
      {messages.length > 0 && (
        <div className="border-t border-kaleo-sand px-6 py-4">
          <h5 className="text-sm font-medium text-kaleo-earth/70 mb-3">
            Conversation
          </h5>
          <div className="space-y-3 max-h-48 overflow-y-auto scroll-smooth">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.speaker === 'deaf' ? 'justify-end' : 'justify-start'
                  }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${message.speaker === 'deaf'
                    ? 'bg-kaleo-terracotta text-kaleo-cream'
                    : 'bg-kaleo-sand text-kaleo-earth'
                    }`}
                >
                  <div className="flex items-center gap-1 mb-0.5">
                    {message.speaker === 'deaf' ? (
                      <Hand className="w-3 h-3 opacity-60" />
                    ) : (
                      <Mic className="w-3 h-3 opacity-60" />
                    )}
                    <span className="text-xs opacity-60">
                      {message.speaker === 'deaf' ? 'You (signed)' : 'Them (spoken)'}
                    </span>
                  </div>
                  <p className="text-sm">{message.text}</p>
                  <p className="text-xs opacity-60 mt-1">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className={`px-6 py-3 text-center transition-colors duration-300 ${isSpeaking
        ? 'bg-green-50 border-t border-green-200'
        : currentSpeaker === 'deaf'
          ? 'bg-kaleo-sand/50'
          : 'bg-blue-50 border-t border-blue-200'
        }`}>
        <p className={`text-sm font-medium ${isSpeaking
          ? 'text-green-700'
          : currentSpeaker === 'deaf'
            ? 'text-kaleo-earth/70'
            : 'text-blue-700'
          }`}>
          {isSpeaking ? (
            <>
              <AudioLines className="w-4 h-4 inline mr-1" />
              Your message is being spoken aloud. Wait for it to finish...
            </>
          ) : currentSpeaker === 'deaf' ? (
            'Sign your message. It will be converted to voice for the other person.'
          ) : (
            <>
              <Mic className="w-4 h-4 inline mr-1" />
              The other person is speaking. Their words will appear as text.
            </>
          )}
        </p>
      </div>
    </div>
  );
}
