import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface VoiceVisualizerProps {
  onVolumeChange?: (volume: number) => void;
}

export default function VoiceVisualizer({ onVolumeChange }: VoiceVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationRef = useRef<number | null>(null);
  
  const [isListening, setIsListening] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [volume, setVolume] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [visualizationMode, setVisualizationMode] = useState<'waveform' | 'frequency' | 'circular'>('waveform');

  const drawWaveform = useCallback((dataArray: Uint8Array, bufferLength: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    // Draw background gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(140, 123, 107, 0.1)');
    gradient.addColorStop(0.5, 'rgba(140, 123, 107, 0.05)');
    gradient.addColorStop(1, 'rgba(140, 123, 107, 0.1)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // Draw waveform
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#8C7B6B';
    ctx.beginPath();
    
    const sliceWidth = width / bufferLength;
    let x = 0;
    
    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * height) / 2;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      
      x += sliceWidth;
    }
    
    ctx.lineTo(width, height / 2);
    ctx.stroke();
    
    // Draw center line
    ctx.strokeStyle = 'rgba(140, 123, 107, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height / 2);
    ctx.lineTo(width, height / 2);
    ctx.stroke();
  }, []);

  const drawFrequency = useCallback((dataArray: Uint8Array, bufferLength: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    const barWidth = (width / bufferLength) * 2.5;
    let barHeight;
    let x = 0;
    
    for (let i = 0; i < bufferLength; i++) {
      barHeight = (dataArray[i] / 255) * height * 0.8;
      
      const gradient = ctx.createLinearGradient(0, height - barHeight, 0, height);
      gradient.addColorStop(0, '#8C7B6B');
      gradient.addColorStop(1, 'rgba(140, 123, 107, 0.3)');
      
      ctx.fillStyle = gradient;
      ctx.fillRect(x, height - barHeight, barWidth, barHeight);
      
      x += barWidth + 1;
    }
  }, []);

  const drawCircular = useCallback((dataArray: Uint8Array, bufferLength: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) * 0.5;
    
    ctx.clearRect(0, 0, width, height);
    
    // Draw circular visualization
    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (dataArray[i] / 255) * radius * 0.8;
      const angle = (i / bufferLength) * Math.PI * 2;
      
      const x1 = centerX + Math.cos(angle) * radius;
      const y1 = centerY + Math.sin(angle) * radius;
      const x2 = centerX + Math.cos(angle) * (radius + barHeight);
      const y2 = centerY + Math.sin(angle) * (radius + barHeight);
      
      const gradient = ctx.createLinearGradient(x1, y1, x2, y2);
      gradient.addColorStop(0, 'rgba(140, 123, 107, 0.3)');
      gradient.addColorStop(1, '#8C7B6B');
      
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    }
    
    // Draw center circle
    ctx.fillStyle = 'rgba(140, 123, 107, 0.2)';
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.3, 0, Math.PI * 2);
    ctx.fill();
  }, []);

  const visualize = useCallback(() => {
    if (!analyserRef.current) return;
    
    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!isListening) return;
      
      animationRef.current = requestAnimationFrame(draw);
      
      if (visualizationMode === 'waveform') {
        analyser.getByteTimeDomainData(dataArray);
        drawWaveform(dataArray, bufferLength);
      } else if (visualizationMode === 'frequency') {
        analyser.getByteFrequencyData(dataArray);
        drawFrequency(dataArray, bufferLength);
      } else {
        analyser.getByteFrequencyData(dataArray);
        drawCircular(dataArray, bufferLength);
      }
      
      // Calculate volume
      const sum = dataArray.reduce((a, b) => a + b, 0);
      const avg = sum / bufferLength;
      const normalizedVolume = Math.min(avg / 128, 1);
      setVolume(normalizedVolume);
      onVolumeChange?.(normalizedVolume);
    };
    
    draw();
  }, [isListening, visualizationMode, drawWaveform, drawFrequency, drawCircular, onVolumeChange]);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current);
      
      setIsListening(true);
      setHasPermission(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setHasPermission(false);
    }
  };

  const stopListening = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    setIsListening(false);
    setVolume(0);
    
    // Clear canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  };

  const toggleMute = () => {
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach(track => {
        track.enabled = isMuted;
      });
      setIsMuted(!isMuted);
    }
  };

  useEffect(() => {
    if (isListening) {
      visualize();
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isListening, visualize]);

  // Set canvas size
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
    }
  }, []);

  if (hasPermission === false) {
    return (
      <div className="bg-kaleo-cream rounded-2xl p-8 text-center">
        <MicOff className="w-16 h-16 mx-auto text-kaleo-terracotta mb-4" />
        <h3 className="font-display text-2xl text-kaleo-earth mb-2">Microphone Access Required</h3>
        <p className="text-kaleo-earth/70 mb-4">
          Please allow microphone access to use the voice visualization feature.
        </p>
        <Button 
          onClick={startListening}
          className="bg-kaleo-terracotta hover:bg-kaleo-earth text-kaleo-cream"
        >
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-kaleo-cream rounded-2xl overflow-hidden shadow-lg">
      {/* Visualization Canvas */}
      <div className="relative aspect-video bg-kaleo-charcoal">
        <canvas
          ref={canvasRef}
          className="w-full h-full"
        />
        
        {/* Volume Indicator */}
        {isListening && (
          <div className="absolute top-4 right-4 flex items-center gap-2 bg-kaleo-charcoal/80 px-3 py-1.5 rounded-full">
            <Activity className={`w-4 h-4 ${volume > 0.3 ? 'text-green-400' : 'text-kaleo-terracotta'}`} />
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map((i) => (
                <div
                  key={i}
                  className={`w-1 rounded-full transition-all duration-100 ${
                    volume > i * 0.2 ? 'bg-kaleo-terracotta' : 'bg-kaleo-terracotta/30'
                  }`}
                  style={{ height: `${i * 4 + 4}px` }}
                />
              ))}
            </div>
          </div>
        )}
        
        {/* Mode Selector */}
        {isListening && (
          <div className="absolute bottom-4 left-4 flex gap-2">
            {(['waveform', 'frequency', 'circular'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setVisualizationMode(mode)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  visualizationMode === mode
                    ? 'bg-kaleo-terracotta text-kaleo-cream'
                    : 'bg-kaleo-charcoal/80 text-kaleo-cream/70 hover:text-kaleo-cream'
                }`}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* Controls */}
      <div className="p-6">
        <div className="flex items-center justify-center gap-4">
          {!isListening ? (
            <Button
              onClick={startListening}
              className="bg-kaleo-terracotta hover:bg-kaleo-earth text-kaleo-cream rounded-full w-16 h-16 flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
            >
              <Mic className="w-6 h-6" />
            </Button>
          ) : (
            <>
              <Button
                onClick={toggleMute}
                variant="outline"
                className="rounded-full w-12 h-12 border-2 border-kaleo-terracotta text-kaleo-terracotta hover:bg-kaleo-terracotta hover:text-kaleo-cream"
              >
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
              </Button>
              <Button
                onClick={stopListening}
                className="bg-red-500 hover:bg-red-600 text-white rounded-full w-16 h-16 flex items-center justify-center shadow-lg"
              >
                <MicOff className="w-6 h-6" />
              </Button>
            </>
          )}
        </div>
        
        <p className="text-center text-sm text-kaleo-earth/60 mt-4">
          {isListening 
            ? 'Speak to see your voice visualized' 
            : 'Click the microphone to start visualizing your voice'}
        </p>
      </div>
    </div>
  );
}
