document.addEventListener("DOMContentLoaded", () => {
    // 1. Tab Switching Handler
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");

            tabBtns.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const activeContent = document.getElementById(targetTab);
            if (activeContent) activeContent.classList.add("active");

            if (targetTab === "tab-history") loadDetectionHistory();
        });
    });

    // 2. DOM Elements
    const camResult = document.getElementById("camResult");
    const audResult = document.getElementById("audResult");
    const deterrenceState = document.getElementById("deterrenceState");
    const cropStateBadge = document.getElementById("cropStateBadge");
    const overallPriorityBadge = document.getElementById("overallPriorityBadge");
    const reasonText = document.getElementById("reasonText");

    // Header Controls
    const btnEmergencyStop = document.getElementById("btnEmergencyStop");
    const btnMute = document.getElementById("btnMute");
    const btnTestMode = document.getElementById("btnTestMode");

    // Executive Overview Metrics
    const ovBirdsConfirmed = document.getElementById("ovBirdsConfirmed");
    const ovDeterrenceTriggers = document.getElementById("ovDeterrenceTriggers");
    const ovMotorcycleRejections = document.getElementById("ovMotorcycleRejections");
    const ovTomatoesLogged = document.getElementById("ovTomatoesLogged");

    // Bird Telemetry Counters
    const cntSparrow = document.getElementById("cntSparrow");
    const cntMyna = document.getElementById("cntMyna");
    const cntCrow = document.getElementById("cntCrow");
    const cntParrot = document.getElementById("cntParrot");
    const cntPigeon = document.getElementById("cntPigeon");
    const cntPeacock = document.getElementById("cntPeacock");

    // Crop Condition Elements
    const csHeroBadge = document.getElementById("csHeroBadge");
    const csHeroReason = document.getElementById("csHeroReason");
    const csRipeCount = document.getElementById("csRipeCount");
    const csHalfCount = document.getElementById("csHalfCount");
    const csGreenCount = document.getElementById("csGreenCount");
    const csRipeRatio = document.getElementById("csRipeRatio");
    const rowsGrid = document.getElementById("rowsGrid");

    // Actuators
    const actDetState = document.getElementById("actDetState");
    const actMotorState = document.getElementById("actMotorState");
    const actSpeakerState = document.getElementById("actSpeakerState");

    // Upload Elements
    const imgBirdInput = document.getElementById("imgBirdInput");
    const btnUploadBirdImg = document.getElementById("btnUploadBirdImg");
    const birdUploadResult = document.getElementById("birdUploadResult");

    const imgTomatoInput = document.getElementById("imgTomatoInput");
    const btnUploadTomatoImg = document.getElementById("btnUploadTomatoImg");
    const tomatoUploadResult = document.getElementById("tomatoUploadResult");

    const audInput = document.getElementById("audInput");
    const btnUploadAud = document.getElementById("btnUploadAud");
    const audResultBox = document.getElementById("audResultBox");

    // Mock Audio Elements
    const mockSpeciesSelect = document.getElementById("mockSpeciesSelect");
    const btnGenMock = document.getElementById("btnGenMock");
    const btnPlayMock = document.getElementById("btnPlayMock");
    let currentMockWavUrl = null;

    // Manual Diagnostic Buttons & Logs
    const manualTestBtns = document.querySelectorAll(".btn-test");
    const manualTestLog = document.getElementById("manualTestLog");

    // Reports & History
    const btnGenReports = document.getElementById("btnGenReports");
    const btnRefreshHistory = document.getElementById("btnRefreshHistory");
    const historyTableBody = document.getElementById("historyTableBody");

    // 3. Status Polling Loop
    async function pollStatus() {
        try {
            const res = await fetch("/api/status");
            if (!res.ok) return;
            const data = await res.json();

            const dec = data.decision || {};
            const fusion = data.fusion || {};
            const telemetry = data.telemetry || {};
            const tomatoTel = data.tomato_telemetry || {};
            const controls = data.controls || {};
            const spBreakdown = telemetry.species_breakdown || {};

            // Decision Banner
            camResult.textContent = fusion.camera_prediction || "No bird";
            audResult.textContent = fusion.audio_prediction || "No sound";

            if (dec.deterrence_active) {
                deterrenceState.textContent = "ON";
                deterrenceState.className = "dec-value status-on";
                if (actDetState) actDetState.textContent = "ON";
            } else {
                deterrenceState.textContent = "OFF";
                deterrenceState.className = "dec-value status-off";
                if (actDetState) actDetState.textContent = "OFF";
            }

            reasonText.textContent = dec.reason || "System operating normally.";

            // Overview Metrics
            ovBirdsConfirmed.textContent = telemetry.total_birds_confirmed || 0;
            ovDeterrenceTriggers.textContent = telemetry.total_deterrence_triggers || 0;
            ovMotorcycleRejections.textContent = telemetry.motorcycle_rejections || 0;
            ovTomatoesLogged.textContent = telemetry.total_tomatoes_logged || 0;

            // Bird Species Breakdown
            cntSparrow.textContent = spBreakdown["House Sparrow"] || 0;
            cntMyna.textContent = spBreakdown["Common Myna"] || 0;
            cntCrow.textContent = spBreakdown["Crow"] || 0;
            cntParrot.textContent = spBreakdown["Parrot"] || 0;
            cntPigeon.textContent = spBreakdown["Pigeon"] || 0;
            cntPeacock.textContent = spBreakdown["Peacock"] || 0;

            // Tomato Crop State
            const cState = tomatoTel.crop_state || {};
            const cMetrics = tomatoTel.metrics || {};
            const rowsStats = tomatoTel.rows_stats || [];

            cropStateBadge.textContent = cState.crop_state || "State 6 — Insufficient Data";
            csHeroBadge.textContent = cState.crop_state || "State 6 — Insufficient Data";
            csHeroReason.textContent = cState.reason || "Field camera connected and analyzing maturity.";

            csRipeCount.textContent = cMetrics.fully_ripened_count || 0;
            csHalfCount.textContent = cMetrics.half_ripened_count || 0;
            csGreenCount.textContent = cMetrics.green_count || 0;
            csRipeRatio.textContent = `${(cMetrics.fully_ripened_pct || 0).toFixed(1)}%`;

            // Max Priority
            let maxPrio = "Low";
            rowsStats.forEach(r => {
                if (r.priority === "Critical") maxPrio = "Critical";
                else if (r.priority === "High" && maxPrio !== "Critical") maxPrio = "High";
                else if (r.priority === "Medium" && maxPrio === "Low") maxPrio = "Medium";
            });
            overallPriorityBadge.textContent = maxPrio;
            overallPriorityBadge.className = `badge badge-priority-${maxPrio.toLowerCase()}`;

            // Render Row Cards
            renderRowCards(rowsStats);

            // Controls Badges
            btnEmergencyStop.style.background = controls.emergency_stop ? "#ef4444" : "";
            btnMute.style.background = controls.mute_mode ? "#f59e0b" : "";
            btnTestMode.style.background = controls.manual_test_mode ? "#06b6d4" : "";

            if (actMotorState) actMotorState.textContent = dec.motor_active ? "ON" : "OFF";
            if (actSpeakerState) actSpeakerState.textContent = dec.speaker_active ? "ACTIVE" : "OFF";

        } catch (err) {
            console.error("Status polling error:", err);
        }
    }

    function renderRowCards(rowsStats) {
        if (!rowsGrid) return;
        if (!rowsStats || rowsStats.length === 0) {
            rowsGrid.innerHTML = `<div class="row-card"><h3>Field Rows</h3><p>No row statistics recorded yet.</p></div>`;
            return;
        }

        rowsGrid.innerHTML = rowsStats.map(r => `
            <div class="row-card">
                <h3>Row ${r.row_id}</h3>
                <span class="badge badge-priority-${(r.priority || 'low').toLowerCase()}">${r.priority} Priority</span>
                <p><strong>Total Tomatoes:</strong> ${r.tomato_count}</p>
                <p>🔴 Fully Ripened: ${r.fully_ripened_count}</p>
                <p>🟡 Half Ripened: ${r.half_ripened_count}</p>
                <p>🟢 Green: ${r.green_count}</p>
                <p class="tab-desc" style="margin-top:6px;"><em>${r.reason}</em></p>
            </div>
        `).join("");
    }

    // 4. Control Button Event Listeners
    btnEmergencyStop.addEventListener("click", async () => {
        await fetch("/api/controls/emergency_stop", { method: "POST" });
        pollStatus();
    });

    btnMute.addEventListener("click", async () => {
        await fetch("/api/controls/mute", { method: "POST" });
        pollStatus();
    });

    btnTestMode.addEventListener("click", async () => {
        await fetch("/api/controls/manual_test_mode", { method: "POST" });
        pollStatus();
    });

    // 5. Media Upload Handlers
    if (btnUploadBirdImg) {
        btnUploadBirdImg.addEventListener("click", async () => {
            if (!imgBirdInput.files[0]) return alert("Please select an image file first.");
            const formData = new FormData();
            formData.append("file", imgBirdInput.files[0]);

            birdUploadResult.textContent = "Analyzing bird species with 6-class model...";
            try {
                const res = await fetch("/api/detect/image", { method: "POST", body: formData });
                const data = await res.json();
                const dets = data.detections || [];
                if (dets.length > 0) {
                    birdUploadResult.innerHTML = `<strong>Detections:</strong> ${dets.map(d => `${d.display_name} (${Math.round(d.confidence*100)}%)`).join(", ")}`;
                } else {
                    birdUploadResult.textContent = "No supported bird species detected in uploaded image.";
                }
                pollStatus();
            } catch (err) {
                birdUploadResult.textContent = "Image analysis error: " + err;
            }
        });
    }

    if (btnUploadTomatoImg) {
        btnUploadTomatoImg.addEventListener("click", async () => {
            if (!imgTomatoInput.files[0]) return alert("Please select a tomato image file first.");
            const formData = new FormData();
            formData.append("file", imgTomatoInput.files[0]);

            tomatoUploadResult.textContent = "Analyzing tomato maturity and count...";
            try {
                const res = await fetch("/api/tomato/detect/image", { method: "POST", body: formData });
                const data = await res.json();
                const counts = data.counts || {};
                tomatoUploadResult.innerHTML = `
                    <strong>Tomato Maturity Result:</strong><br>
                    🔴 Fully Ripened: ${counts.fully_ripened || 0} | 🟡 Half Ripened: ${counts.half_ripened || 0} | 🟢 Green: ${counts.green || 0}<br>
                    <strong>State:</strong> ${data.crop_state.crop_state}
                `;
                pollStatus();
            } catch (err) {
                tomatoUploadResult.textContent = "Tomato analysis error: " + err;
            }
        });
    }

    if (btnUploadAud) {
        btnUploadAud.addEventListener("click", async () => {
            if (!audInput.files[0]) return alert("Please select an audio file first.");
            const formData = new FormData();
            formData.append("file", audInput.files[0]);

            audResultBox.textContent = "Analyzing audio spectrum & noise filtering...";
            try {
                const res = await fetch("/api/detect/audio", { method: "POST", body: formData });
                const data = await res.json();
                const aud = data.audio_result || {};
                audResultBox.innerHTML = `<strong>Audio Classification:</strong> ${aud.display_name} (Conf: ${Math.round((aud.confidence||0)*100)}%)<br><em>${aud.message||''}</em>`;
                pollStatus();
            } catch (err) {
                audResultBox.textContent = "Audio analysis error: " + err;
            }
        });
    }

    // 6. Synthetic Mock Audio Generator
    if (btnGenMock) {
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
                if (btnPlayMock) btnPlayMock.disabled = false;

                alert(`Synthetic Mock WAV Generated for ${mock.display_name} (${mock.duration_sec}s).\nWarning: ${mock.warning}`);
                pollStatus();
            } catch (err) {
                alert("Error generating mock audio: " + err);
            } finally {
                btnGenMock.disabled = false;
                btnGenMock.textContent = "Generate Mock Audio WAV";
            }
        });
    }

    if (btnPlayMock) {
        btnPlayMock.addEventListener("click", () => {
            alert("Playing synthetic mock audio test track...");
        });
    }

    // 7. Manual Diagnostic Buttons
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

    // 8. History Loader
    async function loadDetectionHistory() {
        if (!historyTableBody) return;
        try {
            const res = await fetch("/api/history");
            const data = await res.json();

            const bHist = data.bird_history || [];
            const tHist = data.tomato_history || [];

            const combined = [
                ...bHist.map(b => ({ ...b, module_name: "Module A — Bird" })),
                ...tHist.map(t => ({ ...t, module_name: "Module B — Tomato", species: t.class_name, deterrence_triggered: 0 }))
            ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

            if (combined.length === 0) {
                historyTableBody.innerHTML = `<tr><td colspan="7">No detection history logged in SQLite database yet.</td></tr>`;
                return;
            }

            historyTableBody.innerHTML = combined.map(item => `
                <tr>
                    <td>${item.timestamp}</td>
                    <td>${item.module_name}</td>
                    <td>${item.source}</td>
                    <td><strong>${item.display_name}</strong></td>
                    <td>${Math.round(item.confidence * 100)}%</td>
                    <td>${item.prediction_mode || 'Real Inference'}</td>
                    <td><span style="color:${item.deterrence_triggered ? '#ef4444' : '#10b981'};font-weight:600;">${item.deterrence_triggered ? 'Deterrence Triggered' : 'Normal Log'}</span></td>
                </tr>
            `).join("");
        } catch (err) {
            historyTableBody.innerHTML = `<tr><td colspan="7">Error loading history: ${err}</td></tr>`;
        }
    }

    if (btnRefreshHistory) {
        btnRefreshHistory.addEventListener("click", loadDetectionHistory);
    }

    // 9. Reports Handler
    if (btnGenReports) {
        btnGenReports.addEventListener("click", async () => {
            btnGenReports.disabled = true;
            btnGenReports.textContent = "Generating...";

            try {
                const res = await fetch("/api/reports/generate", { method: "POST" });
                const data = await res.json();
                if (data.status === "success") {
                    alert("Unified PDF and CSV Reports generated successfully!");
                }
            } catch (err) {
                alert("Error generating reports: " + err);
            } finally {
                btnGenReports.disabled = false;
                btnGenReports.textContent = "🔄 Generate Fresh PDF & CSV Reports";
            }
        });
    }

    // Start Polling Loop
    setInterval(pollStatus, 1000);
    pollStatus();
});
