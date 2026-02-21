import { useState, useRef, useCallback, useEffect } from 'react';
import { Camera, StopCircle, Play, Download, RefreshCw, Video, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface RecordedVideo {
  url: string;
  timestamp: Date;
  duration: number;
}

export default function VideoCapture() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const animationRef = useRef<number | null>(null);
  
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedVideos, setRecordedVideos] = useState<RecordedVideo[]>([]);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isPlaying, setIsPlaying] = useState<string | null>(null);

  // Initialize camera
  const initCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        }, 
        audio: true 
      });
      
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      setHasPermission(true);
    } catch (err) {
      console.error('Error accessing camera:', err);
      setHasPermission(false);
    }
  }, []);

  useEffect(() => {
    initCamera();
    
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [initCamera]);

  // Recording timer
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    
    if (isRecording && !isPaused) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    }
    
    return () => clearInterval(interval);
  }, [isRecording, isPaused]);

  const startRecording = () => {
    if (!streamRef.current) return;
    
    const chunks: Blob[] = [];
    const mediaRecorder = new MediaRecorder(streamRef.current, {
      mimeType: 'video/webm;codecs=vp9,opus'
    });
    
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunks.push(e.data);
      }
    };
    
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'video/webm' });
      const url = URL.createObjectURL(blob);
      
      setRecordedVideos(prev => [{
        url,
        timestamp: new Date(),
        duration: recordingTime
      }, ...prev]);
      
      setRecordingTime(0);
    };
    
    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start(1000);
    setIsRecording(true);
    setIsPaused(false);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        setIsPaused(false);
      } else {
        mediaRecorderRef.current.pause();
        setIsPaused(true);
      }
    }
  };

  const playVideo = (url: string) => {
    if (videoRef.current) {
      if (isPlaying === url) {
        videoRef.current.pause();
        videoRef.current.srcObject = streamRef.current;
        setIsPlaying(null);
      } else {
        videoRef.current.srcObject = null;
        videoRef.current.src = url;
        videoRef.current.play();
        setIsPlaying(url);
      }
    }
  };

  const downloadVideo = (url: string, index: number) => {
    const a = document.createElement('a');
    a.href = url;
    a.download = `signbridge-recording-${index + 1}.webm`;
    a.click();
  };

  const deleteVideo = (index: number) => {
    setRecordedVideos(prev => {
      const newVideos = [...prev];
      URL.revokeObjectURL(newVideos[index].url);
      newVideos.splice(index, 1);
      return newVideos;
    });
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (hasPermission === false) {
    return (
      <div className="bg-kaleo-cream rounded-2xl p-8 text-center">
        <Camera className="w-16 h-16 mx-auto text-kaleo-terracotta mb-4" />
        <h3 className="font-display text-2xl text-kaleo-earth mb-2">Camera Access Required</h3>
        <p className="text-kaleo-earth/70 mb-4">
          Please allow camera access to use the video capture feature.
        </p>
        <Button 
          onClick={initCamera}
          className="bg-kaleo-terracotta hover:bg-kaleo-earth text-kaleo-cream"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="bg-kaleo-cream rounded-2xl overflow-hidden shadow-lg">
      {/* Video Preview */}
      <div className="relative aspect-video bg-kaleo-charcoal">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover"
        />
        
        {/* Recording Indicator */}
        {isRecording && (
          <div className="absolute top-4 left-4 flex items-center gap-2 bg-kaleo-charcoal/80 px-3 py-1.5 rounded-full">
            <div className={`w-3 h-3 rounded-full ${isPaused ? 'bg-yellow-400' : 'bg-red-500 animate-pulse'}`} />
            <span className="text-kaleo-cream text-sm font-medium">
              {isPaused ? 'PAUSED' : 'REC'} {formatTime(recordingTime)}
            </span>
          </div>
        )}
        
        {/* Camera Overlay */}
        {!isRecording && !isPlaying && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-20 h-20 border-2 border-kaleo-cream/30 rounded-full flex items-center justify-center">
              <div className="w-16 h-16 border border-kaleo-cream/20 rounded-full" />
            </div>
          </div>
        )}
      </div>
      
      {/* Controls */}
      <div className="p-6">
        <div className="flex items-center justify-center gap-4 mb-6">
          {!isRecording ? (
            <Button
              onClick={startRecording}
              className="bg-red-500 hover:bg-red-600 text-white rounded-full w-16 h-16 flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
            >
              <Video className="w-6 h-6" />
            </Button>
          ) : (
            <>
              <Button
                onClick={pauseRecording}
                variant="outline"
                className="rounded-full w-14 h-14 border-2 border-kaleo-terracotta text-kaleo-terracotta hover:bg-kaleo-terracotta hover:text-kaleo-cream"
              >
                {isPaused ? <Play className="w-5 h-5" /> : <Square className="w-5 h-5" />}
              </Button>
              <Button
                onClick={stopRecording}
                className="bg-red-500 hover:bg-red-600 text-white rounded-full w-16 h-16 flex items-center justify-center shadow-lg"
              >
                <StopCircle className="w-6 h-6" />
              </Button>
            </>
          )}
        </div>
        
        {/* Recorded Videos */}
        {recordedVideos.length > 0 && (
          <div className="border-t border-kaleo-sand pt-4">
            <h4 className="font-display text-lg text-kaleo-earth mb-3">Recorded Videos</h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {recordedVideos.map((video, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between bg-kaleo-sand/50 rounded-lg p-3"
                >
                  <div className="flex items-center gap-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => playVideo(video.url)}
                      className="text-kaleo-terracotta hover:text-kaleo-earth"
                    >
                      {isPlaying === video.url ? <Square className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                    </Button>
                    <div>
                      <p className="text-sm font-medium text-kaleo-earth">
                        Recording {recordedVideos.length - index}
                      </p>
                      <p className="text-xs text-kaleo-earth/60">
                        {video.timestamp.toLocaleTimeString()} • {formatTime(video.duration)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => downloadVideo(video.url, index)}
                      className="text-kaleo-terracotta hover:text-kaleo-earth"
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteVideo(index)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <Square className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
