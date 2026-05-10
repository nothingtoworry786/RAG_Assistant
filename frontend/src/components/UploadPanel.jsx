import { useRef, useState } from "react";
import { ingestFile } from "../api.js";
export default function UploadPanel({ onDocReady }) {
  const [status, setStatus] = useState("idle");
  const [info, setInfo] = useState(null);
  const [progress, setProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef();
  async function handleFile(file) {
    if (!file) return;
    setStatus("uploading");
    setProgress(0);
    setInfo(null);
    try {
      const result = await ingestFile(
        file,
        setProgress
      );
      setInfo(result);
      setStatus("done");
      onDocReady(
        result.docId,
        result.filename
      );
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  }
  function onInputChange(e) {
    handleFile(e.target.files[0]);
  }
  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }
  return (
    <div className="upload-panel">
      <div className="panel-header">
        <div>
          <h2>Document Upload</h2>
          <p className="panel-sub">
            Upload PDF or TXT files
          </p>
        </div>
      </div>
      <div
        className={`drop-zone ${
          dragOver ? "drag-over" : ""
        } ${status === "done" ? "done" : ""}`}
        onClick={() =>
          status !== "uploading" &&
          inputRef.current.click()
        }
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() =>
          setDragOver(false)
        }
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          style={{ display: "none" }}
          onChange={onInputChange}
        />
        {status === "idle" && (
          <>
            <div className="hero-icon">
            </div>
            <h3>
              Drop your document here
            </h3>
            <p>
              Drag & drop your files or click
              to browse
            </p>
            <div className="file-tags">
              <span>PDF</span>
              <span>TXT</span>
            </div>
          </>
        )}
        {status === "uploading" && (
          <>
            <div className="hero-icon spin">
            </div>
            <h3>
              Processing document...
            </h3>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${progress}%`,
                }}
              />
            </div>
            <p>{progress}% uploaded</p>
          </>
        )}
        {status === "done" && info && (
          <>
            <div className="hero-icon">
            </div>
            <h3>{info.filename}</h3>
            <p>
              {info.chunkCount} chunks indexed
            </p>
            <button
              className="primary-btn"
              onClick={(e) => {
                e.stopPropagation();
                setStatus("idle");
                setInfo(null);
                onDocReady(null, null);
              }}
            >
              Upload New Document
            </button>
          </>
        )}
        {status === "error" && (
          <>
            <div className="hero-icon">
            </div>
            <h3>Upload Failed</h3>
            <p>
              Something went wrong while
              processing your file.
            </p>
            <button
              className="primary-btn"
              onClick={(e) => {
                e.stopPropagation();
                setStatus("idle");
              }}
            >
              Try Again
            </button>
          </>
        )}
      </div>
    </div>
  );
}