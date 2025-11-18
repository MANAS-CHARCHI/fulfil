import { useState, useEffect } from "react";
import axios from "axios";

export default function CSVImporter() {
    const [uploadProgress, setUploadProgress] = useState(0);
    const [taskId, setTaskId] = useState(null);
    const [processingState, setProcessingState] = useState(null);

    const [uploadStatus, setUploadStatus] = useState("Idle");

    // -----------------------------------------------------
    // 1. Handle file upload
    // -----------------------------------------------------
    const handleUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploadStatus("Uploading...");
        setUploadProgress(0);
        setProcessingState(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await axios.post(
                "http://localhost:5000/products/upload/",
                formData,
                {
                    headers: { "Content-Type": "multipart/form-data" },
                    onUploadProgress: (evt) => {
                        const percent = Math.round((evt.loaded / evt.total) * 100);
                        setUploadProgress(percent);
                    }
                }
            );

            setUploadStatus("Upload Complete ✓");
            setTaskId(res.data.task_id);

        } catch (err) {
            setUploadStatus("Upload Failed ❌");
            console.error(err);
        }
    };

    // -----------------------------------------------------
    // 2. Listen to SSE progress events
    // -----------------------------------------------------
    useEffect(() => {
        if (!taskId) return;

        const events = new EventSource(
            `http://localhost:5000/products/progress/${taskId}/`
        );

        events.onmessage = (e) => {
            const data = JSON.parse(e.data);
            setProcessingState(data);

            if (data.stage === "completed" || data.stage === "error") {
                events.close();
            }
        };

        return () => events.close();
    }, [taskId]);

    // -----------------------------------------------------
    // Helper for ASCII progress bar
    // -----------------------------------------------------
    const renderBar = (percent) => {
        const total = 20; // 20 characters width
        const filled = Math.round((percent / 100) * total);
        const empty = total - filled;

        return (
            <>
                <span style={{ fontFamily: "monospace" }}>
                    {"█".repeat(filled)}
                    {"░".repeat(empty)}
                </span>
                <span> {percent}%</span>
            </>
        );
    };

    // -----------------------------------------------------
    // UI Render
    // -----------------------------------------------------
    return (
        <div style={{ padding: 20, fontFamily: "Arial" }}>
            <h2>CSV Import</h2>

            <input type="file" accept=".csv" onChange={handleUpload} />

            {/* Upload progress */}
            {uploadProgress > 0 && (
                <div style={{ marginTop: 10 }}>
                    <strong>{uploadStatus}</strong>
                    <div>{renderBar(uploadProgress)}</div>
                </div>
            )}

            {/* Processing progress */}
            {processingState && processingState.stage !== "completed" && (
                <div style={{ marginTop: 20 }}>
                    <h3>Processing: {processingState.stage}</h3>

                    {/* Show processing bar only if we know totals */}
                    {processingState.total > 0 && (
                        <div>
                            {renderBar(
                                Math.round(
                                    (processingState.processed / processingState.total) * 100
                                )
                            )}
                        </div>
                    )}

                    <div style={{ marginTop: 5 }}>
                        Rows processed: {processingState.processed} /{" "}
                        {processingState.total || "?"}
                    </div>

                    <div style={{ color: "#888" }}>{processingState.message}</div>
                </div>
            )}

            {/* Completed */}
            {processingState?.stage === "completed" && (
                <div style={{ marginTop: 20, color: "green", fontWeight: "bold" }}>
                    ✓ Import Completed!
                </div>
            )}

            {/* Error */}
            {processingState?.stage === "error" && (
                <div style={{ marginTop: 20, color: "red", fontWeight: "bold" }}>
                    ❌ Error: {processingState.message}
                </div>
            )}
        </div>
    );
}
