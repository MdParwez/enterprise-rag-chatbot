import React from "react";

const ITEMS = [
  { id: "chat", label: "Chat", hint: "Query the knowledge base" },
  { id: "documents", label: "Documents", hint: "Ingest & manage sources" },
  { id: "evaluation", label: "Evaluation", hint: "RAGAS quality scores" },
];

export default function Sidebar({ view, onChange }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark">◆</span>
        <span className="brand-name">Enterprise RAG</span>
      </div>
      <nav>
        {ITEMS.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${view === item.id ? "active" : ""}`}
            onClick={() => onChange(item.id)}
          >
            <span className="nav-label">{item.label}</span>
            <span className="nav-hint">{item.hint}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <span className="stack-label">STACK</span>
        <span className="stack-line">FastAPI · ChromaDB</span>
        <span className="stack-line">Groq · RAGAS</span>
      </div>
    </aside>
  );
}
