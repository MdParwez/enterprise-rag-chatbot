import React, { useState, useEffect, useRef } from "react";
import SourceCard from "./SourceCard.jsx";
import { speak, stopSpeaking, pauseSpeaking, resumeSpeaking, isSpeechSynthesisSupported } from "../utils/speech.js";

export default function MessageBubble({ id, role, content, sources, latencyMs, cached, streaming, error }) {
  const isUser = role === "user";
  const ttsSupported = isSpeechSynthesisSupported();

  // "idle" -> nothing playing | "speaking" -> playing | "paused" -> paused mid-utterance
  const [speechState, setSpeechState] = useState("idle");
  const utteranceRef = useRef(null);

  // stop this message's own speech if the bubble unmounts while it's playing
  useEffect(() => {
    return () => {
      if (speechState !== "idle") stopSpeaking();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleStart = () => {
    utteranceRef.current = speak(content, {
      onStart: () => setSpeechState("speaking"),
      onEnd: () => setSpeechState("idle"),
      onError: () => setSpeechState("idle"),
    });
  };

  const handlePauseResume = () => {
    if (speechState === "speaking") {
      pauseSpeaking();
      setSpeechState("paused");
    } else if (speechState === "paused") {
      resumeSpeaking();
      setSpeechState("speaking");
    }
  };

  const handleStop = () => {
    stopSpeaking();
    setSpeechState("idle");
  };

  return (
    <div className={`message-row ${isUser ? "from-user" : "from-assistant"}`}>
      <div className={`message-bubble ${error ? "has-error" : ""}`}>
        <div className="message-bubble-body">
          <p>{content}{streaming && <span className="cursor-blink">▍</span>}</p>
          {!isUser && !streaming && content && ttsSupported && (
            <div className="speak-controls">
              {speechState === "idle" && (
                <button className="speak-btn" onClick={handleStart} title="Read reply aloud" aria-label="Read reply aloud">
                  🔊
                </button>
              )}
              {speechState !== "idle" && (
                <>
                  <button
                    className="speak-btn active"
                    onClick={handlePauseResume}
                    title={speechState === "speaking" ? "Pause" : "Resume"}
                    aria-label={speechState === "speaking" ? "Pause reading" : "Resume reading"}
                  >
                    {speechState === "speaking" ? "⏸" : "▶"}
                  </button>
                  <button className="speak-btn" onClick={handleStop} title="Stop" aria-label="Stop reading">
                    ⏹
                  </button>
                </>
              )}
            </div>
          )}
        </div>
        {!isUser && !error && (latencyMs !== undefined && latencyMs !== null) && (
          <div className="trace-strip">
            <span className="trace-tag">{cached ? "CACHE HIT" : "RETRIEVED"}</span>
            <span className="trace-latency">{latencyMs.toFixed(0)}ms</span>
          </div>
        )}
        {!isUser && sources && sources.length > 0 && (
          <div className="sources-grid">
            {sources.map((s, i) => <SourceCard key={i} source={s} />)}
          </div>
        )}
      </div>
    </div>
  );
}
