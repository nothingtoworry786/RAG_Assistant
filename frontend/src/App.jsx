// src/App.jsx

import { useState } from "react";
import UploadPanel from "./components/UploadPanel.jsx";
import ChatPanel from "./components/ChatPanel.jsx";
import "./App.css";

export default function App() {
  const [docId, setDocId] = useState(null);
  const [filename, setFilename] = useState(null);

  function handleDocReady(id, name) {
    setDocId(id);
    setFilename(name);
  }
  return (
    <div className="app">
      <header className="app-header">
          <div className="logo-section">
            <div>
              <h1>RAG Assistant</h1>
              <span className="header-sub">
                Intelligent Document Analysis
              </span>
            </div>
          </div>
      </header>
      <main className="app-body">
        <UploadPanel onDocReady={handleDocReady} />
        <ChatPanel
          docId={docId}
          filename={filename}
        />
      </main>
    </div>
  );
}