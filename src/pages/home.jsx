
import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Activity, Video, VideoOff, Users } from 'lucide-react';
import ControlBar from '../components/controlsbar';
import Navbar from '../components/navbar';

export default function Home() {

  // <div style = {{display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100px'}}>
  //     <Navbar/>
  //      <h1>About Us</h1>
  // </div>
  // State for UI Logic
  const [cameraActive, setCameraActive] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [statusText, setStatusText] = useState("Camera Off");

  // Conversation State
  const [messages, setMessages] = useState([]);
  const [currentTurn, setCurrentTurn] = useState("deaf"); // "deaf" or "hearing"

  // Data State
  const [rawText, setRawText] = useState("--");
  const [refinedText, setRefinedText] = useState("--");

  // Processing State
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState(""); // "CAPTURING", "SENDING", etc.

  // Hand Detection State
  const [handsDetected, setHandsDetected] = useState(false);
  const [noHandsTimer, setNoHandsTimer] = useState(null);

  // Timer State for Sign Language Capture
  const [captureTimeLeft, setCaptureTimeLeft] = useState(0);
  const [isCapturing, setIsCapturing] = useState(false);
  const SIGN_CAPTURE_DURATION = 15; // 15 seconds for signing

  // Refs for accessing DOM elements and instances
  const videoRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const selectedVoiceRef = useRef(null);
  const captureTimerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const handDetectionIntervalRef = useRef(null);
  const noHandsTimeoutRef = useRef(null);

  // --- 1. Initialization (Voices & Speech Rec) ---
  useEffect(() => {
    // Load Voices
    const loadVoices = () => {
      const voices = synthRef.current.getVoices();
     if (selectedVoiceRef!=null)
      {
         selectedVoiceRef.current = voices.find(voice => voice.name.includes('Google US English')) || 
                                 voices.find(voice => voice.name.includes('Samantha')) ||
                                 voices.find(voice => voice.lang.includes('en-US')) || 
                                 voices[0];}
    };
    
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = loadVoices;
    }
    loadVoices();

    // Setup Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.lang = 'en-US';
      recognition.interimResults = false;

      recognition.onstart = () => {
        setIsListening(true);
        updateDisplay("Listening...", true);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        addMessage("hearing", text);
        speakAndDisplay(text);
        setCurrentTurn("deaf"); // Switch turn to deaf person
      };

      recognition.onerror = (event) => {
        console.warn("Speech error:", event.error);
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }

    // Cleanup on unmount
    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
      }
      if (synthRef.current.speaking) {
        synthRef.current.cancel();
      }
      if (captureTimerRef.current) {
        clearInterval(captureTimerRef.current);
      }
    }; <Route path = '/about' element= {<About/>}/>
  }, []);

  // --- 2. Action Handlers ---

  const toggleCamera = async () => {
    if (cameraActive) {
      // Stop Camera
      if (videoRef.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        videoRef.current.srcObject = null;
      }

      // Stop hand detection
      if (handDetectionIntervalRef.current) {
        clearInterval(handDetectionIntervalRef.current);
        handDetectionIntervalRef.current = null;
      }
      if (noHandsTimeoutRef.current) {
        clearTimeout(noHandsTimeoutRef.current);
        noHandsTimeoutRef.current = null;
      }

      setCameraActive(false);
      setStatusText("Camera Off");
      setHandsDetected(false);
    } else {
      // Start Camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        setCameraActive(true);
        setStatusText("Camera Active - Monitoring for hands...");
        updateDisplay("Camera ready.", true);

        // Start continuous hand detection
        startHandDetection();
      } catch (err) {
        console.error("Camera Error:", err);
        updateDisplay("Camera access denied.", true);
      }
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) return;
    
    if (synthRef.current.speaking) synthRef.current.cancel();
    setIsSpeaking(false);

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  // --- 3. Hand Detection & Sign Processing ---

  // Mock hand detection - simulates checking for hands in frame
  const detectHands = () => {
    // In real implementation, this would use MediaPipe or TensorFlow.js
    // For now, we'll simulate random hand detection
    const handsPresent = Math.random() > 0.3; // 70% chance hands are detected
    return handsPresent;
  };

  const startHandDetection = () => {
    // Check for hands every 500ms
    handDetectionIntervalRef.current = setInterval(() => {
      if (!cameraActive || isProcessing) return;

      const handsPresent = detectHands();

      if (handsPresent) {
        setHandsDetected(true);
        setStatusText("Camera Active - Hands detected! 🤟");

        // Clear any existing "no hands" timeout
        if (noHandsTimeoutRef.current) {
          clearTimeout(noHandsTimeoutRef.current);
          noHandsTimeoutRef.current = null;
        }

        // Start a new timeout - if hands stay still for 2 seconds, process
        noHandsTimeoutRef.current = setTimeout(() => {
          if (cameraActive && !isProcessing) {
            startSignProcessing();
          }
        }, 2000); // 2 seconds of hands detected = start processing

      } else {
        setHandsDetected(false);
        setStatusText("Camera Active - Waiting for hands...");

        // Clear timeout if hands disappear
        if (noHandsTimeoutRef.current) {
          clearTimeout(noHandsTimeoutRef.current);
          noHandsTimeoutRef.current = null;
        }
      }
    }, 500);
  };

  const startSignProcessing = async () => {
    if (!cameraActive) {
      return;
    }

    // Stop hand detection while processing
    if (handDetectionIntervalRef.current) {
      clearInterval(handDetectionIntervalRef.current);
      handDetectionIntervalRef.current = null;
    }
    if (noHandsTimeoutRef.current) {
      clearTimeout(noHandsTimeoutRef.current);
      noHandsTimeoutRef.current = null;
    }

    // Start Capture with Timer
    setIsCapturing(true);
    setIsProcessing(true);
    setProcessingStep("CAPTURING SIGNS...");
    setRawText("--"); // Reset raw text
    setRefinedText("--"); // Reset refined text
    setCaptureTimeLeft(SIGN_CAPTURE_DURATION);

    // Countdown Timer
    let timeLeft = SIGN_CAPTURE_DURATION;
    captureTimerRef.current = setInterval(() => {
      timeLeft -= 1;
      setCaptureTimeLeft(timeLeft);

      if (timeLeft <= 0) {
        clearInterval(captureTimerRef.current);
      }
    }, 1000);

    // Wait for capture duration
    await new Promise(resolve => setTimeout(resolve, SIGN_CAPTURE_DURATION * 1000));

    setIsCapturing(false);
    setProcessingStep("ANALYZING SIGNS...");

    // 1. Simulate CV Model
    const rawSigns = await mockSignLanguageModel();

    // Update UI after Capture
    setProcessingStep("REFINING MESSAGE...");
    setRawText(rawSigns);

    // 2. Simulate LLM
    const refinedSentence = await mockLLMRefinement(rawSigns);
    setRefinedText(refinedSentence);

    // Add to conversation
    addMessage("deaf", refinedSentence);

    // Finish
    setIsProcessing(false);
    setProcessingStep("");
    speakAndDisplay(refinedSentence);
    setCurrentTurn("hearing"); // Switch turn to hearing person

    // Restart hand detection after a short delay
    setTimeout(() => {
      if (cameraActive) {
        setStatusText("Camera Active - Monitoring for hands...");
        startHandDetection();
      }
    }, 3000); // Wait 3 seconds before resuming hand detection
  };

  const mockSignLanguageModel = () => {
    return new Promise(resolve => {
      setTimeout(() => {
        const simulatedModelOutputs = [
          "HELLO NICE MEET YOU",
          "HOW YOU TODAY",
          "THANK YOU HELP",
          "PLEASE WATER NEED",
          "UNDERSTAND YES",
          "SORRY NOT UNDERSTAND"
        ];
        const random = simulatedModelOutputs[Math.floor(Math.random() * simulatedModelOutputs.length)];
        resolve(random);
      }, 1500);
    });
  };

  const mockLLMRefinement = (rawText) => {
    return new Promise(resolve => {
      setTimeout(() => {
        let refined = "";
        if (rawText.includes("HELLO")) refined = "Hello, nice to meet you!";
        else if (rawText.includes("HOW YOU")) refined = "How are you today?";
        else if (rawText.includes("THANK")) refined = "Thank you for your help.";
        else if (rawText.includes("WATER")) refined = "Please, I need some water.";
        else if (rawText.includes("UNDERSTAND YES")) refined = "Yes, I understand.";
        else if (rawText.includes("SORRY")) refined = "Sorry, I don't understand.";
        else refined = "I am trying to communicate something.";
        resolve(refined);
      }, 1000);
    });
  };

  // --- 4. Helpers ---

  const addMessage = (sender, text) => {
    const newMessage = {
      id: Date.now(),
      sender: sender, // "deaf" or "hearing"
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, newMessage]);

    // Auto-scroll to bottom
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const speakAndDisplay = (text) => {
    if (synthRef.current.speaking) synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    if (selectedVoiceRef.current) utterance.voice = selectedVoiceRef.current;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    synthRef.current.speak(utterance);
  };

  // --- 5. Render ---
  return (
     <div className=" w-screen overflow-hidden flex flex-col relative font-sans text-white">
   
     {/* Embedded CSS for Animations */}
      <style>{`
        @keyframes pulse-ring {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        .listening-pulse { animation: pulse-ring 2s infinite; }
        
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          10% { opacity: 1; box-shadow: 0 0 10px #3b82f6; }
          90% { opacity: 1; box-shadow: 0 0 10px #3b82f6; }
          100% { top: 100%; opacity: 0; }
        }
        .scanning-line { animation: scan 2s linear infinite; }

        @keyframes sound-bars {
          0% { height: 10%; }
          50% { height: 100%; }
          100% { height: 10%; }
        }
        .animate-bar { animation: sound-bars 0.5s ease-in-out infinite; }
      `}</style>

      {/* Header */}
      <header className="w-full p-4 shrink-0 z-20 flex justify-between items-center backdrop-blur-sm">
      
        <div className="flex items-center gap-2 shrink-0">
          <div className={`w-3 h-3 rounded-full transition-colors duration-300 ${cameraActive ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-xs md:text-sm text-gray-400 font-medium hidden md:inline">{statusText}</span>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col md:flex-row items-stretch justify-center w-full max-w-7xl mx-auto px-4 gap-6 min-h-0 py-4">

        {/* Video Section */}
        <div className="relative w-full md:w-2/5 aspect-video  rounded-xl overflow-hidden shadow-2xl border border-gray-700 group shrink-1 max-h-[35vh] md:max-h-full md:h-auto">
          <video
            ref={videoRef}
            className="w-full h-full object-cover transform scale-x-[-1]"
            autoPlay
            playsInline
            muted
          />

          {/* Placeholder when Camera Off */}
          {!cameraActive && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500 z-10">
              <VideoOff className="w-12 h-12 md:w-20 md:h-20 mb-4 opacity-50" />
              <span className="text-sm md:text-lg font-medium">Camera Inactive</span>
            </div>
          )}

          {/* Capture Timer Overlay */}
          {isCapturing && (
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-30">
              <div className="bg-red-600 text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-3 animate-pulse">
                <div className="w-3 h-3 bg-white rounded-full animate-ping"></div>
                <span className="text-2xl font-bold">{captureTimeLeft}s</span>
              </div>
            </div>
          )}

          {/* Processing Overlay */}
          {isProcessing && !isCapturing && (
            <div className="absolute inset-0  flex flex-col items-center justify-center z-20 backdrop-blur-[2px]">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mb-2"></div>
              <span className="text-blue-100 font-mono tracking-widest text-sm text-center px-4">{processingStep}</span>
            </div>
          )}

          {/* Turn Indicator */}
          <div className="absolute bottom-4 left-4 right-4 z-20">
            <div className={`px-4 py-2 rounded-lg text-center font-bold text-sm transition-all duration-300 ${
              currentTurn === "deaf"
                ? "bg-blue-600/90 text-white"
                : "bg-green-600/90 text-white"
            }`}>
              {currentTurn === "deaf" ? " Deaf Person's Turn" : "🎤 Hearing Person's Turn"}
            </div>
          </div>
        </div>

        {/* Conversation Section */}
        <div className="w-full md:w-3/5 flex flex-col rounded-xl border border-gray-700 shadow-2xl overflow-hidden">

          {/* Conversation Header */}
          <div className=" px-4 py-3 border-b border-gray-700">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
               Conversation
            </h2>
            <p className="text-xs text-gray-400 mt-1">Real-time translation between sign language and speech</p>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[300px] max-h-[500px]">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-500">
                <Users className="w-16 h-16 mb-4 opacity-30" />
                <p className="text-sm">No messages yet. Start the conversation!</p>
                <p className="text-xs mt-2 text-gray-600">Deaf person uses sign language, hearing person uses voice</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender === "deaf" ? "justify-start" : "justify-end"}`}
                >
                  <div className={`max-w-[80%] rounded-lg px-4 py-3 ${
                    msg.sender === "deaf"
                      ? "bg-blue-600 text-white"
                      : "bg-green-600 text-white"
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold opacity-90">
                        {msg.sender === "deaf" ? "🤟 Deaf Person" : "🎤 Hearing Person"}
                      </span>
                      <span className="text-xs opacity-70">{msg.timestamp}</span>
                    </div>
                    <p className="text-sm md:text-base">{msg.text}</p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Current Processing Status */}
          {isProcessing && (
            <div className="bg-gray-900/80 px-4 py-4 border-t border-gray-700 space-y-3">
              <div className="flex items-center gap-3">
                <Activity className="w-5 h-5 animate-spin text-blue-400" />
                <p className="text-sm text-blue-300 font-bold">{processingStep}</p>
              </div>

              {/* Raw Data Display */}
              {rawText !== "--" && (
                <div className="bg-red-900/30 border border-red-700/50 rounded-lg p-3">
                  <p className="text-xs text-red-400 font-bold mb-1">🔴 RAW MODEL OUTPUT (CV Model):</p>
                  <p className="text-sm text-red-200 font-mono">{rawText}</p>
                </div>
              )}

              {/* Refined Text Display */}
              {refinedText !== "--" && (
                <div className="bg-green-900/30 border border-green-700/50 rounded-lg p-3">
                  <p className="text-xs text-green-400 font-bold mb-1">✅ REFINED OUTPUT (LLM):</p>
                  <p className="text-sm text-green-200 font-mono">{refinedText}</p>
                </div>
              )}
            </div>
          )}

          {/* Audio Visualizer */}
          {isSpeaking && (
            <div className="bg-gray-900/80 px-4 py-3 border-t border-gray-700">
              <div className="flex items-center gap-3">
                <div className="flex justify-center items-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <div
                      key={i}
                      className="w-1 bg-green-400 rounded-full animate-bar"
                      style={{ animationDelay: `${0.1 * (i + 1)}s` }}
                    ></div>
                  ))}
                </div>
                <p className="text-sm text-green-300">Speaking...</p>
              </div>
            </div>
          )}
        </div>

      </div>

   <ControlBar 
        cameraActive={cameraActive} 
        handsDetected={handsDetected}
        toggleCamera={toggleCamera}
        isListening={isListening}
        toggleListening={toggleListening}
        
        />
   </div>
  );
}