'use client';

import { useEffect, useRef, useState } from 'react';
import { notify } from '../core/notify.js';
import { readStorage, writeStorage } from '../core/storage.js';

function cleanSpeechText(text = '') {
  return String(text || '')
    .replace(/```[\s\S]*?```/g, ' bloque de codigo. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/^\s*\d+[.)]\s+/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/[_*~>#|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function splitTextIntoChunks(text, maxChunkLength = 250) {
  if (!text) return [];
  const words = text.split(/\s+/);
  const chunks = [];
  let currentChunk = "";
  
  for (const word of words) {
    if (!word) continue;
    const testChunk = currentChunk ? `${currentChunk} ${word}` : word;
    if (testChunk.length > maxChunkLength) {
      if (currentChunk) {
        chunks.push(currentChunk);
        currentChunk = word;
      } else {
        chunks.push(word);
        currentChunk = "";
      }
    } else {
      currentChunk = testChunk;
    }
  }
  
  if (currentChunk) {
    chunks.push(currentChunk);
  }
  
  return chunks;
}

function selectNaturalSpanishVoice() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  const spanishVoices = voices.filter(v => v.lang.toLowerCase().startsWith('es'));
  if (spanishVoices.length === 0) return null;

  const naturalVoices = spanishVoices.filter(v => {
    const name = v.name.toLowerCase();
    return name.includes('natural') || name.includes('online') || name.includes('google') || name.includes('neural');
  });

  if (naturalVoices.length > 0) {
    const femaleNatural = naturalVoices.find(v => {
      const name = v.name.toLowerCase();
      return name.includes('dalia') || name.includes('helena') || name.includes('sabina') || name.includes('elena') || name.includes('female') || name.includes('mujer') || name.includes('paula') || name.includes('hilda') || name.includes('zira') || name.includes('daria');
    });
    if (femaleNatural) return femaleNatural;
    return naturalVoices[0];
  }

  const femaleFallback = spanishVoices.find(v => {
    const name = v.name.toLowerCase();
    return name.includes('dalia') || name.includes('helena') || name.includes('sabina') || name.includes('elena') || name.includes('female') || name.includes('mujer') || name.includes('paula') || name.includes('hilda') || name.includes('zira') || name.includes('daria');
  });
  if (femaleFallback) return femaleFallback;

  return spanishVoices[0];
}

function getVoiceToUse() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices();
  const storedName = readStorage('yelia_selected_voice', '');
  if (storedName) {
    const match = voices.find(v => v.name === storedName);
    if (match) return match;
  }
  return selectNaturalSpanishVoice();
}

export function useSpeech() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabledState] = useState(true);
  const voiceEnabledRef = useRef(voiceEnabled);
  const pausedByToggleRef = useRef(false);
  const audioRef = useRef(null);
  const audioUrlRef = useRef('');
  const speakingTimerRef = useRef(null);

  const chunksRef = useRef([]);
  const chunkIndexRef = useRef(0);
  
  const recognitionRef = useRef(null);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [selectedVoiceName, setSelectedVoiceNameState] = useState('');

  function clearSpeakingTimer() {
    if (!speakingTimerRef.current) return;
    window.clearTimeout(speakingTimerRef.current);
    speakingTimerRef.current = null;
  }

  function finishSpeaking() {
    clearSpeakingTimer();
    pausedByToggleRef.current = false;
    setSpeaking(false);
  }

  function armSpeakingFallback(text = '') {
    clearSpeakingTimer();
    const seconds = Math.min(90, Math.max(5, Math.ceil(String(text || '').length / 14)));
    speakingTimerRef.current = window.setTimeout(finishSpeaking, seconds * 1000);
  }

  useEffect(() => {
    const next = readStorage('yelia_voice_enabled', '1') !== '0';
    setVoiceEnabledState(next);
    voiceEnabledRef.current = next;
    setSelectedVoiceNameState(readStorage('yelia_selected_voice', ''));
  }, []);

  useEffect(() => {
    voiceEnabledRef.current = voiceEnabled;
  }, [voiceEnabled]);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.speechSynthesis) return;

    const updateVoices = () => {
      const allVoices = window.speechSynthesis.getVoices();
      const spanish = allVoices.filter(v => v.lang.toLowerCase().startsWith('es'));
      setAvailableVoices(spanish);
    };

    updateVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = updateVoices;
    }
  }, []);

  useEffect(() => {
    const stopSpeech = () => stop();
    window.addEventListener('beforeunload', stopSpeech);
    window.addEventListener('pagehide', stopSpeech);
    return () => {
      stop();
      clearSpeakingTimer();
      window.removeEventListener('beforeunload', stopSpeech);
      window.removeEventListener('pagehide', stopSpeech);
    };
  }, []);

  function setVoiceEnabled(value) {
    const next = Boolean(value);
    setVoiceEnabledState(next);
    writeStorage('yelia_voice_enabled', next ? '1' : '0');
    voiceEnabledRef.current = next;
    if (!('speechSynthesis' in window)) return;
    if (!next) {
      if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
        window.speechSynthesis.pause();
        pausedByToggleRef.current = true;
        clearSpeakingTimer();
        setSpeaking(false);
      }
      return;
    }
    if (pausedByToggleRef.current && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      pausedByToggleRef.current = false;
      setSpeaking(true);
      armSpeakingFallback(chunksRef.current[chunkIndexRef.current] || '');
    }
  }

  function playNextChunk() {
    if (chunksRef.current.length === 0 || chunkIndexRef.current >= chunksRef.current.length) {
      finishSpeaking();
      return;
    }

    const chunk = chunksRef.current[chunkIndexRef.current];
    const provider = readStorage('yelia_tts_provider', process.env.NEXT_PUBLIC_TTS_PROVIDER || 'browser');
    if (provider === 'google') {
      playGoogleTtsChunk(chunk);
    } else {
      playBrowserTtsChunk(chunk);
    }
  }

  function playBrowserTtsChunk(text) {
    if (!('speechSynthesis' in window)) {
      chunkIndexRef.current += 1;
      playNextChunk();
      return;
    }
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      const voice = getVoiceToUse();
      
      if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
      } else {
        utterance.lang = 'es-EC';
      }

      utterance.rate = 0.90; // moderate speed (between 0.88 and 0.95)
      utterance.pitch = 1.04; // warmer pitch (between 1.0 and 1.08)
      utterance.volume = 1.0;

      utterance.onstart = () => {
        setSpeaking(true);
        armSpeakingFallback(text);
      };
      utterance.onend = () => {
        chunkIndexRef.current += 1;
        playNextChunk();
      };
      utterance.onerror = (e) => {
        console.warn("SpeechSynthesis error handled:", e);
        chunksRef.current = [];
        chunkIndexRef.current = 0;
        finishSpeaking();
      };
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("SpeechSynthesis speak failed synchronously:", err);
      chunksRef.current = [];
      chunkIndexRef.current = 0;
      finishSpeaking();
    }
  }

  async function playGoogleTtsChunk(text) {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = '';
    }
    if (!text) {
      chunkIndexRef.current += 1;
      playNextChunk();
      return;
    }
    try {
      setSpeaking(true);
      armSpeakingFallback(text);
      const response = await fetch('/api/voice/tts', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', Accept: 'audio/mpeg' },
        body: JSON.stringify({ text, lang: 'es' }),
      });
      if (!response.ok) throw new Error(`TTS ${response.status}`);
      const blob = await response.blob();
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = URL.createObjectURL(blob);
      const audio = new Audio(audioUrlRef.current);
      audioRef.current = audio;
      audio.onended = () => {
        chunkIndexRef.current += 1;
        playNextChunk();
      };
      audio.onerror = () => {
        playBrowserTtsChunk(text);
      };
      await audio.play();
    } catch {
      playBrowserTtsChunk(text);
    }
  }

  function speak(text, options = {}) {
    if (!options.force && !voiceEnabledRef.current) return false;
    
    stop();

    const cleaned = cleanSpeechText(text);
    if (!cleaned) return false;

    const chunks = splitTextIntoChunks(cleaned, 250);
    if (chunks.length === 0) return false;

    chunksRef.current = chunks;
    chunkIndexRef.current = 0;

    playNextChunk();
    return true;
  }

  function stop() {
    chunksRef.current = [];
    chunkIndexRef.current = 0;
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = '';
    }
    pausedByToggleRef.current = false;
    finishSpeaking();
  }

  function listen(onResult) {
    if (listening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setListening(false);
      return false;
    }

    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      notify('Tu navegador no soporta reconocimiento de voz. Prueba en Chrome o Edge actualizado.', 'error');
      return false;
    }
    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      const recognition = new Recognition();
      recognitionRef.current = recognition;
      recognition.lang = 'es-EC';
      recognition.interimResults = false;
      recognition.onstart = () => setListening(true);
      recognition.onend = () => {
        setListening(false);
        recognitionRef.current = null;
      };
      recognition.onerror = (e) => {
        setListening(false);
        recognitionRef.current = null;
        console.error("Speech recognition error:", e);
        notify('Error en reconocimiento de voz. Revisa permisos del micrófono.', 'error');
      };
      recognition.onresult = (event) => {
        const text = event.results?.[0]?.[0]?.transcript || '';
        onResult?.(text);
      };
      recognition.start();
      return true;
    } catch (err) {
      setListening(false);
      recognitionRef.current = null;
      console.error("Speech recognition start failed:", err);
      notify('No pude iniciar el dictado por voz. Revisa permisos del microfono.', 'error');
      return false;
    }
  }

  return { 
    listening, 
    speaking, 
    voiceEnabled, 
    setVoiceEnabled, 
    speak, 
    stop, 
    listen,
    availableVoices,
    selectedVoiceName,
    setSelectedVoiceName: (name) => {
      setSelectedVoiceNameState(name);
      writeStorage('yelia_selected_voice', name);
    }
  };
}
