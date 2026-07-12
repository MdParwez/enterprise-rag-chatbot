import React from "react";

export default function SourceCard({ source }) {
  const pct = Math.round(source.score * 100);
  return (
    <div className="source-card">
      <div className="source-card-top">
        <span className="source-name">{source.source}{source.page ? ` · p.${source.page}` : ""}</span>
        <span className="source-score">{pct}%</span>
      </div>
      <div className="score-bar">
        <div className="score-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="source-text">{source.text.slice(0, 160)}{source.text.length > 160 ? "…" : ""}</p>
    </div>
  );
}
