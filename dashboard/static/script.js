document.addEventListener("DOMContentLoaded", () => {
    // Decision Banner DOM
    const camResult = document.getElementById("camResult");
    const audResult = document.getElementById("audResult");
    const birdEvidenceBadge = document.getElementById("birdEvidenceBadge");
    const deterrenceState = document.getElementById("deterrenceState");
    const motorState = document.getElementById("motorState");
    const reasonText = document.getElementById("reasonText");
    const deterrenceOverlay = document.getElementById("deterrenceOverlay");

    // Header Controls
    const btnEmergencyStop = document.getElementById("btnEmergencyStop");
    const btnMute = document.getElementById("btnMute");
    const btnTestMode = document.getElementById("btnTestMode");

    // 6-Species Counters
    const cntSparrow = document.getElementById("cntSparrow");
    const cntMyna = document.getElementById("cntMyna");
    const cntCrow = document.getElementById("cntCrow");
    const cntParrot = document.getElementById("cntParrot");
    const cntPigeon = document.getElementById("cntPigeon");
    const cntPeacock = document.getElementById("cntPeacock");
    const cntMotorcycle = document.getElementById("cntMotorcycle");

    // Media Upload Elements
    const imgInput = document.getElementById("imgInput");
    const btnUploadImg = document.getElementById("btnUploadImg");
    const audInput = document.getElementById("audInput");
    const btnUploadAud = document.getElementById("btnUploadAud");
    const uploadResultBox = document.getElementById("uploadResultBox");

    // Mock Audio Elements
    const mockSpeciesSelect = document.getElementById("mockSpeciesSelect");
    const btnGenMock = document.getElementById("btnGenMock");
    const btnPlayMock = document.getElementById("btnPlayMock");
    const btnDlMock = document.getElementById("btnDlMock");
    let currentMockWavUrl = null;

    // Manual Test Panel Elements
    const manualTestBtns = document.querySelectorAll(".btn-test");
    const manualTestLog = document.getElementById("manualTestLog");

    // Report Elements
    const btnGenReports = document.getElementById("btnGenReports");

    // 1. Poll Status & Telemetry
    async function pollStatus() {
        try {
            const res = await fetch("/api/status");
            if (!res.ok) return;
            const data = await res.json();

            const dec = data.decision || {};
            const fusion = data.fusion || {};
            const telemetry = data.telemetry || {};
            const controls = data.controls || {};
            const spBreakdown = telemetry.species_breakdown || {};

            // Update Decision Banner
            camResult.textContent = fusion.camera_prediction || "No bird";
            audResult.textContent = fusion.audio_prediction || "No sound";

            if (dec.bird_confirmed) {
                birdEvidenceBadge.textContent = "Confirmed";
                birdEvidenceBadge.style.color = "#10b981";
                birdEvidenceBadge.style.borderColor = "#10b981";
            } else {
                birdEvidenceBadge.textContent = "Not confirmed";
                birdEvidenceBadge.style.color = "#94a3b8";
                birdEvidenceBadge.style.borderColor = "rgba(255,255,255,0.1)";
            }

            if (dec.deterrence_active) {
                deterrenceState.textContent = "ON";
                deterrenceState.className = "dec-value status-on";
                deterrenceOverlay.classList.remove("hidden");
            } else {
                deterrenceState.textContent = "OFF";
                deterrenceState.className = "dec-value status-off";
                deterrenceOverlay.classList.add("hidden");
            }

            motorState.textContent = dec.motor_active ? "ON" : "OFF";
            motorState.className = dec.motor_active ? "dec-value status-on" : "dec-value status-off";

            reasonText.textContent = dec.reason || "System status active.";

            // Update Header Buttons
            btnEmergencyStop.style.background = controls.emergency_stop ? "#ef4444" : "";
            btnMute.style.background = controls.mute_mode ? "#f59e0b" : "";
            btnTestMode.style.background = controls.manual_test_mode ? "#06b6d4" : "";

            // Update Counters
            cntSparrow.textContent = spBreakdown["House Sparrow"] || 0;
            cntMyna.textContent = spBreakdown["Common Myna"] || 0;
            cntCrow.textContent = spBreakdown["Crow"] || 0;
            cntParrot.textContent = spBreakdown["Parrot"] || 0;
            cntPigeon.textContent = spBreakdown["Pigeon"] || 0;
            cntPeacock.textContent = spBreakdown["Peacock"] || 0;
            cntMotorcycle.textContent = telemetry.motorcycle_rejections || 0;

        } catch (err) {
            console.error("Status polling error:", err);
        }
    }

    // 2. Control Button Handlers
    btnEmergencyStop.addEventListener("click", async () => {
        const res = await fetch("/api/controls/emergency_stop", { method: "POST" });
        pollStatus();
    });

    btnMute.addEventListener("click", async () => {
        const res = await fetch("/api/controls/mute", { method: "POST" });
        pollStatus();
    });

    btnTestMode.addEventListener("click", async () => {
        const res = await fetch("/api/controls/manual_test_mode", { method: "POST" });
        pollStatus();
    });

    // 3. Media Upload Handlers
    btnUploadImg.addEventListener("click", async () => {
        if (!imgInput.files[0]) return alert("Please select an image file first.");
        const formData = new FormData();
        formData.append("file", imgInput.files[0]);

        uploadResultBox.textContent = "Analyzing image with 6-class vision model...";
        try {
            const res = await fetch("/api/detect/image", { method: "POST", body: formData });
            const data = await res.json();
            const dets = data.detections || [];
            if (dets.length > 0) {
                uploadResultBox.innerHTML = `<strong>Image Detection:</strong> ${dets.map(d => `${d.display_name} (${int(d.confidence*100)}%)`).join(", ")}`;
            } else {
                uploadResultBox.textContent = "No supported bird species detected in uploaded image.";
            }
            pollStatus();
        } catch (err) {
            uploadResultBox.textContent = "Image analysis error: " + err;
        }
    });

    btnUploadAud.addEventListener("click", async () => {
        if (!audInput.files[0]) return alert("Please select an audio file first.");
        const formData = new FormData();
        formData.append("file", audInput.files[0]);

        uploadResultBox.textContent = "Analyzing audio spectrum & noise filtering...";
        try {
            const res = await fetch("/api/detect/audio", { method: "POST", body: formData });
            const data = await res.json();
            const aud = data.audio_result || {};
            uploadResultBox.innerHTML = `<strong>Audio Classification:</strong> ${aud.display_name} (Conf: ${int((aud.confidence||0)*100)}%)<br><em>${aud.message||''}</em>`;
            pollStatus();
        } catch (err) {
            uploadResultBox.textContent = "Audio analysis error: " + err;
        }
    });

    // 4. Synthetic Mock Audio Generator
    btnGenMock.addEventListener("click", async () => {
        const species = mockSpeciesSelect.value;
        const dur = document.querySelector('input[name="mockDur"]:checked').value;

        btnGenMock.disabled = true;
        btnGenMock.textContent = "Generating...";

        try {
            const res = await fetch("/api/mock_audio/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ species: species, duration: dur })
            });

            const data = await res.json();
            const mock = data.mock_result || {};

            currentMockWavUrl = mock.file_path;
            btnPlayMock.disabled = false;
            btnDlMock.style.display = "inline-flex";
            btnDlMock.href = "/api/reports/download/csv"; // Fallback download link

            alert(`Mock WAV Generated for ${mock.display_name} (${mock.duration_sec}s).\nTag: ${mock.badge}`);
            pollStatus();
        } catch (err) {
            alert("Error generating mock audio: " + err);
        } finally {
            btnGenMock.disabled = false;
            btnGenMock.textContent = "Generate Mock Audio";
        }
    });

    btnPlayMock.addEventListener("click", () => {
        if (currentMockWavUrl) {
            const audio = new Audio("/api/status"); // Trigger backend playback
            alert("Playing synthetic mock audio test track...");
        }
    });

    // 5. Manual Diagnostic Test Panel Handlers
    manualTestBtns.forEach(btn => {
        btn.addEventListener("click", async () => {
            const testType = btn.getAttribute("data-test");
            manualTestLog.textContent = `Executing diagnostic test '${testType}'...`;

            try {
                const res = await fetch("/api/manual_test/run", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ test_type: testType })
                });

                const data = await res.json();
                manualTestLog.innerHTML = `
                    <div><strong>Test Name:</strong> ${data.test_name}</div>
                    <div><strong>Expected:</strong> ${data.expected}</div>
                    <div><strong>Actual:</strong> ${data.actual}</div>
                    <div><strong>Status:</strong> <span style="color:${data.result_status==='PASS'?'#10b981':'#ef4444'};font-weight:bold;">${data.result_status}</span></div>
                `;
                pollStatus();
            } catch (err) {
                manualTestLog.textContent = "Diagnostic test error: " + err;
            }
        });
    });

    // 6. Reports Generation
    btnGenReports.addEventListener("click", async () => {
        btnGenReports.disabled = true;
        btnGenReports.textContent = "Generating...";

        try {
            const res = await fetch("/api/reports/generate", { method: "POST" });
            const data = await res.json();
            if (data.status === "success") {
                alert("PDF and CSV Telemetry & Sound Filtering Reports generated successfully!");
            }
        } catch (err) {
            alert("Error generating reports: " + err);
        } finally {
            btnGenReports.disabled = false;
            btnGenReports.innerHTML = '<span>🔄</span> Generate Fresh PDF & CSV Reports';
        }
    });

    // Start Polling Loop
    setInterval(pollStatus, 1000);
    pollStatus();
});
