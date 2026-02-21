import { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, VolumeX, Settings, RefreshCw, Type } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface Voice {
  name: string;
  lang: string;
  voice: SpeechSynthesisVoice;
}

interface AudioHistory {
  text: string;
  timestamp: Date;
  duration: number;
}

export default function TextToVoice() {
  const [text, setText] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [rate, setRate] = useState(1);
  const [pitch, setPitch] = useState(1);
  const [volume, setVolume] = useState(1);
  const [history, setHistory] = useState<AudioHistory[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const startTimeRef = useRef<number>(0);

  // Load available voices
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
      return;
    }

    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      const formattedVoices = availableVoices.map(voice => ({
        name: voice.name,
        lang: voice.lang,
        voice: voice
      }));
      setVoices(formattedVoices);
      
      // Select default voice
      if (formattedVoices.length > 0 && !selectedVoice) {
        const defaultVoice = formattedVoices.find(v => v.lang.startsWith('en')) || formattedVoices[0];
        setSelectedVoice(defaultVoice.name);
      }
    };

    loadVoices();
    
    // Voices may load asynchronously
    window.speechSynthesis.onvoiceschanged = loadVoices;
    
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
    };
  }, [selectedVoice]);

  const speak = useCallback(() => {
    if (!text.trim()) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    const voice = voices.find(v => v.name === selectedVoice);
    
    if (voice) {
      utterance.voice = voice.voice;
    }
    
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = volume;
    
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
      startTimeRef.current = Date.now();
    };
    
    utterance.onend = () => {
      const duration = (Date.now() - startTimeRef.current) / 1000;
      setIsSpeaking(false);
      setIsPaused(false);
      
      // Add to history
      setHistory(prev => [{
        text: text.slice(0, 100) + (text.length > 100 ? '...' : ''),
        timestamp: new Date(),
        duration
      }, ...prev].slice(0, 10));
    };
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      setIsPaused(false);
    };
    
    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
  }, [text, selectedVoice, voices, rate, pitch, volume]);

  const pause = () => {
    if (isSpeaking && !isPaused) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    } else if (isPaused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  };

  const stop = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  };

  const clearText = () => {
    setText('');
    stop();
  };

  const replayHistory = (historyText: string) => {
    setText(historyText);
    setTimeout(() => speak(), 100);
  };

  const sampleTexts = [
    'Hello, how are you today?',
    'Thank you for using SignBridge.',
    'Communication is the key to understanding.',
    'Every voice deserves to be heard.',
  ];

  if (!isSupported) {
    return (
      <div className="bg-kaleo-cream rounded-2xl p-8 text-center">
        <VolumeX className="w-16 h-16 mx-auto text-kaleo-terracotta mb-4" />
        <h3 className="font-display text-2xl text-kaleo-earth mb-2">Text-to-Speech Not Supported</h3>
        <p className="text-kaleo-earth/70">
          Your browser doesn't support text-to-speech. Please try using a modern browser like Chrome, Safari, or Edge.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-kaleo-cream rounded-2xl overflow-hidden shadow-lg">
      {/* Text Input Area */}
      <div className="p-6">
        <div className="relative">
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type your message here..."
            className="min-h-[150px] bg-kaleo-sand/50 border-kaleo-sand focus:border-kaleo-terracotta focus:ring-kaleo-terracotta/20 resize-none text-kaleo-earth placeholder:text-kaleo-earth/40"
          />
          {text && (
            <button
              onClick={clearText}
              className="absolute top-2 right-2 p-1 text-kaleo-earth/40 hover:text-kaleo-earth transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
        
        {/* Sample Texts */}
        <div className="flex flex-wrap gap-2 mt-3">
          {sampleTexts.map((sample, index) => (
            <button
              key={index}
              onClick={() => setText(sample)}
              className="text-xs px-3 py-1 bg-kaleo-sand hover:bg-kaleo-terracotta/20 text-kaleo-earth/70 hover:text-kaleo-earth rounded-full transition-colors"
            >
              {sample}
            </button>
          ))}
        </div>
      </div>
      
      {/* Settings */}
      <Collapsible open={showSettings} onOpenChange={setShowSettings}>
        <CollapsibleTrigger asChild>
          <button className="w-full px-6 py-2 flex items-center justify-between text-sm text-kaleo-earth/70 hover:text-kaleo-earth hover:bg-kaleo-sand/30 transition-colors">
            <span className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Voice Settings
            </span>
            <span className="transform transition-transform">
              {showSettings ? '−' : '+'}
            </span>
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-6 pb-4 space-y-4">
            {/* Voice Selection */}
            <div>
              <label className="text-sm text-kaleo-earth/70 mb-1 block">Voice</label>
              <Select value={selectedVoice} onValueChange={setSelectedVoice}>
                <SelectTrigger className="bg-kaleo-sand/50 border-kaleo-sand">
                  <SelectValue placeholder="Select a voice" />
                </SelectTrigger>
                <SelectContent>
                  {voices.map((voice) => (
                    <SelectItem key={voice.name} value={voice.name}>
                      {voice.name} ({voice.lang})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            {/* Rate Slider */}
            <div>
              <div className="flex justify-between text-sm text-kaleo-earth/70 mb-1">
                <span>Speed</span>
                <span>{rate.toFixed(1)}x</span>
              </div>
              <Slider
                value={[rate]}
                onValueChange={(value) => setRate(value[0])}
                min={0.5}
                max={2}
                step={0.1}
                className="w-full"
              />
            </div>
            
            {/* Pitch Slider */}
            <div>
              <div className="flex justify-between text-sm text-kaleo-earth/70 mb-1">
                <span>Pitch</span>
                <span>{pitch.toFixed(1)}</span>
              </div>
              <Slider
                value={[pitch]}
                onValueChange={(value) => setPitch(value[0])}
                min={0.5}
                max={2}
                step={0.1}
                className="w-full"
              />
            </div>
            
            {/* Volume Slider */}
            <div>
              <div className="flex justify-between text-sm text-kaleo-earth/70 mb-1">
                <span>Volume</span>
                <span>{Math.round(volume * 100)}%</span>
              </div>
              <Slider
                value={[volume]}
                onValueChange={(value) => setVolume(value[0])}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
      
      {/* Playback Controls */}
      <div className="px-6 pb-6">
        <div className="flex items-center justify-center gap-4">
          {!isSpeaking ? (
            <Button
              onClick={speak}
              disabled={!text.trim()}
              className="bg-kaleo-terracotta hover:bg-kaleo-earth disabled:opacity-50 disabled:cursor-not-allowed text-kaleo-cream rounded-full w-16 h-16 flex items-center justify-center shadow-lg hover:shadow-xl transition-all"
            >
              <Play className="w-6 h-6 ml-1" />
            </Button>
          ) : (
            <>
              <Button
                onClick={pause}
                variant="outline"
                className="rounded-full w-14 h-14 border-2 border-kaleo-terracotta text-kaleo-terracotta hover:bg-kaleo-terracotta hover:text-kaleo-cream"
              >
                {isPaused ? <Play className="w-5 h-5 ml-0.5" /> : <Pause className="w-5 h-5" />}
              </Button>
              <Button
                onClick={stop}
                className="bg-red-500 hover:bg-red-600 text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg"
              >
                <VolumeX className="w-5 h-5" />
              </Button>
            </>
          )}
        </div>
        
        {/* Character Count */}
        <p className="text-center text-xs text-kaleo-earth/50 mt-3">
          {text.length} characters
        </p>
      </div>
      
      {/* History */}
      {history.length > 0 && (
        <div className="border-t border-kaleo-sand px-6 py-4">
          <h4 className="font-display text-sm text-kaleo-earth mb-3 flex items-center gap-2">
            <Type className="w-4 h-4" />
            Recent Messages
          </h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {history.map((item, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-kaleo-sand/50 rounded-lg p-2 text-sm"
              >
                <p className="text-kaleo-earth truncate flex-1 mr-3">{item.text}</p>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => replayHistory(item.text)}
                    className="p-1 text-kaleo-terracotta hover:text-kaleo-earth transition-colors"
                  >
                    <Play className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
