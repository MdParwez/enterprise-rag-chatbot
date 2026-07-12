import React, { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import ChatWindow from "./components/ChatWindow.jsx";
import DocumentUpload from "./components/DocumentUpload.jsx";
import EvaluationDashboard from "./components/EvaluationDashboard.jsx";

export default function App() {
  const [view, setView] = useState("chat");

  return (
    <div className="app-shell">
      <Sidebar view={view} onChange={setView} />
      <main className="main-panel">
        {view === "chat" && <ChatWindow />}
        {view === "documents" && <DocumentUpload />}
        {view === "evaluation" && <EvaluationDashboard />}
      </main>
    </div>
  );
}
