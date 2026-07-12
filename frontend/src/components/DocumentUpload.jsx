import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { fetchDocuments, uploadFiles, removeDocument } from "../store/documentsSlice.js";

export default function DocumentUpload() {
  const dispatch = useDispatch();
  const { items, status, lastUploadMessage, error } = useSelector((s) => s.documents);
  const [dragOver, setDragOver] = useState(false);
  const uploading = status === "uploading";

  useEffect(() => {
    dispatch(fetchDocuments());
  }, [dispatch]);

  const handleFiles = (fileList) => {
    const files = Array.from(fileList);
    if (files.length === 0) return;
    dispatch(uploadFiles(files));
  };

  return (
    <div className="documents-view">
      <header className="panel-header">
        <h1>Documents</h1>
        <p>Ingest PDF, DOCX, TXT, or MD files into the vector store.</p>
      </header>

      <div
        className={`dropzone ${dragOver ? "drag-over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
      >
        <p>Drag files here, or</p>
        <label className="file-input-label">
          Browse files
          <input type="file" multiple hidden onChange={(e) => handleFiles(e.target.files)} />
        </label>
        {uploading && <p className="uploading-hint">Ingesting…</p>}
        {!uploading && lastUploadMessage && <p className="status-hint">{lastUploadMessage}</p>}
        {!uploading && error && <p className="status-hint error">{error}</p>}
      </div>

      <div className="document-table">
        <div className="document-table-header">
          <span>Source</span>
          <span>Chunks</span>
          <span></span>
        </div>
        {items.length === 0 && <p className="empty-state">No documents ingested yet.</p>}
        {items.map((d) => (
          <div key={d.source} className="document-row">
            <span className="doc-name">{d.source}</span>
            <span className="doc-chunks">{d.chunks}</span>
            <button className="delete-btn" onClick={() => dispatch(removeDocument(d.source))}>
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
