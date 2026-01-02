import { Mic, MicOff, VideoOff } from "lucide-react";



export default function ControlBar({handsDetected,cameraActive,toggleCamera,isListening,toggleListening}){


    return(

    
      <div className=" controlPanel w-fullbackdrop-blur-md p-4 shrink-0 border-t z-30">
        <div className="max-w-4xl mx-auto">

         
          <div className="text-center mb-4">
            <p className="text-xs text-gray-400">
              <span className="text-blue-400 font-bold">Deaf Person:</span> Just enable camera - automatic hand detection! •
              <span className="text-green-400 font-bold ml-2">Hearing Person:</span> Click "Speak" to respond
            </p>
            {handsDetected && cameraActive && (
              <p className="text-xs text-blue-300 mt-1 animate-pulse">
                👋 Hands detected! Processing will start automatically...
              </p>
            )}
          </div>

          <div className="w-50% flex justify-center items-center gap-8 md:gap-12">

           
            <button
              onClick={toggleCamera}
              className="flex flex-col items-center gap-1 group focus:outline-none"
            >
              <div className={`p-4 rounded-full text-white transition-all duration-300 shadow-2xl transform group-hover:scale-110 active:scale-95 ring-4 ring-gray-800 ${
                cameraActive
                  ? 'bg-blue-600 ring-blue-500 group-hover:bg-red-600 group-hover:ring-red-400'
                  : 'bg-gray-700 ring-gray-600 group-hover:bg-blue-600 group-hover:ring-blue-400'
              }`}>
                {cameraActive ? (
                  handsDetected ? <span className="text-2xl animate-pulse">🤟</span> : <Video className="w-6 h-6" />
                ) : (
                  <VideoOff className="w-6 h-6" />
                )}
              </div>
              <span className="text-[10px] uppercase tracking-wider text-gray-400 font-bold group-hover:text-white transition-colors">
                {cameraActive ? (handsDetected ? "Hands Detected!" : "Camera On") : "Enable Camera"}
              </span>
            </button>

           
            <button
              onClick={toggleListening}
              className="flex flex-col items-center gap-1 group focus:outline-none"
            >
              <div className={`p-4 rounded-full text-white transition-all duration-300 shadow-2xl transform group-hover:scale-110 active:scale-95 ring-4 ring-gray-800 ${
                isListening
                  ? 'bg-green-600 listening-pulse ring-green-500'
                  : 'bg-green-600 group-hover:bg-green-500 group-hover:ring-green-400'
              }`}>
                {isListening ? <Mic className="w-6 h-6" /> : <MicOff className="w-6 h-6" />}
              </div>
              <span className="text-[10px] uppercase tracking-wider text-gray-400 font-bold group-hover:text-white transition-colors">
                {isListening ? "Listening..." : "Speak"}
              </span>
            </button>

          </div>
        </div>
      </div>
    );
}