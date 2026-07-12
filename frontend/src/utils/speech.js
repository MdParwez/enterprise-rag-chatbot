/**
 * Thin wrapper around the browser's native Web Speech API for text-to-speech
 * (speechSynthesis). No external library needed here - browser support is
 * broad enough (Chrome, Edge, Safari; Firefox partial) that a dependency
 * would just add weight for no real benefit.
 *
 * Speech-to-text (query input) instead uses the `react-speech-recognition`
 * library, which wraps the same-family SpeechRecognition API with a much
 * nicer React hook interface - see components/ChatWindow.jsx.
 */

export function isSpeechSynthesisSupported() {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/**
 * Speaks the given text aloud. Cancels any speech currently in progress
 * first, since the browser can only speak one utterance at a time and we
 * want a new "read aloud" click (or a new streamed reply) to take over
 * immediately rather than queue behind the old one.
 */
export function speak(text, { rate = 1, pitch = 1, onStart, onEnd, onError } = {}) {
  if (!isSpeechSynthesisSupported() || !text) return null;

  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = rate;
  utterance.pitch = pitch;
  if (onStart) utterance.onstart = onStart;
  if (onEnd) utterance.onend = onEnd;
  if (onError) utterance.onerror = onError;

  window.speechSynthesis.speak(utterance);
  return utterance;
}

export function stopSpeaking() {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.cancel();
}

export function pauseSpeaking() {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.pause();
}

export function resumeSpeaking() {
  if (isSpeechSynthesisSupported()) window.speechSynthesis.resume();
}
