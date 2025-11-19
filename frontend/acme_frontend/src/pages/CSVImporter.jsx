import React, { useState, useRef } from "react";

export default function UploadProducts() {
    const [jobId, setJobId] = useState(null);
    const [statusText, setStatusText] = useState("Waiting to upload…");

    const [phaseProgress, setPhaseProgress] = useState({
        parsing: 0,
        importing: 0,
        completed: 0,
    });

    const [phaseCounts, setPhaseCounts] = useState({
        parsing: { processed: 0, total: 0 },
        importing: { processed: 0, total: 0 },
        completed: { processed: 0, total: 0 },
    });

    const [steps, setSteps] = useState({
        parsing: false,
        importing: false,
        completed: false,
    });

    const [errorMessage, setErrorMessage] = useState(null);
    const [showRetry, setShowRetry] = useState(false);

    const eventSourceRef = useRef(null);

    const handleUpload = async (e) => {
        e.preventDefault();
        const file = e.target.file.files[0];
        if (!file) return alert("Please select a CSV file");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch("http://localhost:5000/products/upload/", {
                method: "POST",
                body: formData,
            });
            const data = await res.json();
            if (!res.ok) return alert(data.error || "Upload failed");

            setJobId(data.job_id);
            startEventSource(data.job_id);
        } catch (err) {
            setErrorMessage("Upload failed: " + err.message);
        }
    };

    const startEventSource = (id) => {
        if (eventSourceRef.current) eventSourceRef.current.close();
        const es = new EventSource(`http://localhost:5000/products/progress/${id}/`);
        eventSourceRef.current = es;

        es.onmessage = (event) => {
            if (event.data === "[DONE]") {
                es.close();
                return;
            }
            handleStatus(JSON.parse(event.data));
        };

        es.onerror = () => console.log("SSE connection closed");
    };

    const handleStatus = (data) => {
        if (data.error) {
            setErrorMessage(data.error);
            setStatusText("ERROR");
            setPhaseProgress({ parsing: 0, importing: 0, completed: 0 });
            setShowRetry(true);
            return;
        }

        const status = data.status;
        setStatusText(status);

        // update counts for live display
        if (data.processed !== undefined && data.total !== undefined) {
            setPhaseCounts((prev) => ({
                ...prev,
                [status]: { processed: data.processed, total: data.total },
            }));
        }

        // compute live percentage
        let percent = 0;
        if (data.total > 0) {
            percent = Math.round((data.processed / data.total) * 100);
        }

        // update phase progress dynamically
        setPhaseProgress((prev) => ({
            ...prev,
            [status]: percent,
        }));

        // mark step done only when processed === total
        setSteps((prev) => ({
            ...prev,
            [status]: data.processed === data.total,
        }));
    };

    const ProgressBar = ({ value, count }) => (
        <div style={{ marginBottom: "10px" }}>
            <div style={{
                width: "100%", background: "#eee", height: "24px",
                borderRadius: "6px", overflow: "hidden"
            }}>
                <div style={{
                    width: `${value}%`, height: "100%",
                    background: value === 100 ? "#28a745" : "#007bff",
                    transition: "width 0.2s ease"
                }} />
            </div>
            {count && (
                <div style={{ fontSize: "14px", marginTop: "2px" }}>
                    {count.processed.toLocaleString()} / {count.total.toLocaleString()} rows
                </div>
            )}
        </div>
    );

    const Step = ({ done, text }) => (
        <div style={{ display: "flex", alignItems: "center", marginBottom: "6px" }}>
            <span style={{ marginRight: "6px", color: done ? "#28a745" : "#555" }}>
                {done ? "✔" : "⏳"}
            </span>
            <span>{text}</span>
        </div>
    );

    return (
        <div style={{ padding: "40px", maxWidth: "750px", margin: "auto", fontFamily: "Arial, sans-serif" }}>
            <h2>Product CSV Import</h2>

            <form onSubmit={handleUpload} style={{ marginBottom: "20px" }}>
                <input type="file" name="file" accept=".csv" required />
                <button type="submit" style={{
                    marginLeft: "10px", padding: "6px 14px", background: "#007bff",
                    color: "#fff", border: "none", borderRadius: "4px", cursor: "pointer"
                }}>Upload</button>
            </form>

            {jobId && (
                <>
                    <h3>Status: <span style={{ color: errorMessage ? "red" : "#000" }}>{statusText}</span></h3>

                    <h4>1. Parsing CSV</h4>
                    <ProgressBar value={phaseProgress.parsing} count={phaseCounts.parsing} />

                    <h4>2. Importing / Staging</h4>
                    <ProgressBar value={phaseProgress.importing} count={phaseCounts.importing} />

                    <h4>3. Finalizing</h4>
                    <ProgressBar value={phaseProgress.completed} count={phaseCounts.completed} />

                    <h4>Steps</h4>
                    <Step done={steps.parsing} text="Parsing CSV" />
                    <Step done={steps.importing} text="Importing / Staging" />
                    <Step done={steps.completed} text="Completed" />

                    {errorMessage && (
                        <div style={{
                            color: "red", marginTop: "20px", padding: "10px",
                            border: "1px solid red", borderRadius: "6px", background: "#ffe5e5"
                        }}>
                            <b>Error:</b> {errorMessage}
                        </div>
                    )}

                    {showRetry && (
                        <button onClick={() => window.location.reload()} style={{
                            marginTop: "15px", padding: "10px 20px", background: "orange",
                            color: "#fff", border: "none", borderRadius: "6px", cursor: "pointer"
                        }}>
                            Retry
                        </button>
                    )}
                </>
            )}
        </div>
    );
}
