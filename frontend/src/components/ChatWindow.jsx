import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";
import MessageBubble from "./MessageBubble.jsx";
import { sendMessageStream } from "../store/chatSlice.js";

export default function ChatWindow() {
  const dispatch = useDispatch();
  const messages = useSelector((state) => state.chat.messages);
  const status = useSelector((state) => state.chat.status);
  const busy = status === "streaming";

  const [input, setInput] = useState("");
  const endRef = useRef(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition,
  } = useSpeechRecognition();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Mirror the live transcript into the input box while the mic is listening
  useEffect(() => {
    if (listening) setInput(transcript);
  }, [transcript, listening]);

  const stopListening = () => {
    if (listening) {
      SpeechRecognition.stopListening();
      resetTranscript();
    }
  };

  const toggleListening = () => {
    if (listening) {
      stopListening();
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true, interimResults: true });
    }
  };

  const handleSend = () => {
    const question = input.trim();
    if (!question || busy) return;
    stopListening();
    setInput("");
    dispatch(sendMessageStream(question));
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-window">
      <header className="panel-header">
        <h1>Chat</h1>
        <p>Ask a question grounded in your ingested documents. Responses stream over SSE.</p>
      </header>

      <div className="message-list">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>No messages yet. Upload documents on the Documents tab, then ask a question here.</p>
          </div>
        )}
        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            id={m.id}
            role={m.role}
            content={m.content}
            sources={m.sources}
            latencyMs={m.latencyMs}
            cached={m.cached}
            streaming={m.streaming}
            error={m.error}
          />
        ))}
        <div ref={endRef} />
      </div>

      <div className="composer">
        {browserSupportsSpeechRecognition && (
          <button
            type="button"
            className={`mic-btn ${listening ? "listening" : ""}`}
            onClick={toggleListening}
            title={listening ? "Stop voice input" : "Ask by voice"}
            aria-label={listening ? "Stop voice input" : "Ask by voice"}
          >
            {listening ? "◼" : "🎤"}
          </button>
        )}
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            browserSupportsSpeechRecognition
              ? "Ask about your knowledge base, or tap the mic..."
              : "Ask about your knowledge base..."
          }
          rows={2}
        />
        <button onClick={handleSend} disabled={busy || !input.trim()}>
          {busy ? "…" : "Send"}
        </button>
      </div>

      {!browserSupportsSpeechRecognition && (
        <p className="speech-support-hint">
          Voice input isn't supported in this browser. Try Chrome or Edge.
        </p>
      )}
      {listening && <p className="listening-hint">Listening… tap the mic again to stop.</p>}
    </div>
  );
}
