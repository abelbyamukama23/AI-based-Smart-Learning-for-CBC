import { useState, useRef, useCallback, useEffect } from "react";

/**
 * Hook for handling the Web Speech API recognition.
 * @param {function} onResult - Callback fired with the transcribed text.
 * @param {function} onError - Callback fired when an error or unsupported browser is encountered.
 * @returns {object} { listening, toggleVoice }
 */
export function useVoiceInput({ onResult, onError }) {
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const toggleVoice = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      onError?.("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      return;
    }

    const rec = new SpeechRecognition();
    rec.lang = "en-UG"; // Uganda English by default
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      onResult?.(transcript);
    };

    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);
    
    rec.start();
    recognitionRef.current = rec;
    setListening(true);
  }, [listening, onResult, onError]);

  return { listening, toggleVoice };
}
