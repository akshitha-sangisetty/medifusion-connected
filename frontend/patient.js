// =======================================================
// patient.js — Patient Dashboard (Fixed & Unified)
// =======================================================

// ── Auth Guard ──────────────────────────────────────────
function getToken() {
    return localStorage.getItem("token");
}

function guardAuth() {
    const token = getToken();
    const role = localStorage.getItem("role");
    // Only redirect on actual dashboard page, not on submit page
    if (window.location.pathname.includes("patient_dashboard")) {
        if (!token) { window.location.href = "login.html"; return false; }
        if (role && role !== "patient") { window.location.href = "login.html"; return false; }
    }
    return true;
}

function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// ── Tab Switching ────────────────────────────────────────
function showTab(tabName) {
    // Hide all panels
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));

    // Show target panel
    const panel = document.getElementById("tab-" + tabName);
    const nav = document.getElementById("nav-" + tabName);
    if (panel) panel.classList.add("active");
    if (nav) nav.classList.add("active");
}

// ── Submit Case ──────────────────────────────────────────
async function submitCase() {
    const token = getToken();
    if (!token) { window.location.href = "login.html"; return; }

    const sym = document.getElementById("symInput")?.value.trim();
    const desc = document.getElementById("descInput")?.value.trim();
    const msgEl = document.getElementById("submitMsg");
    const btn = document.getElementById("submitBtn");

    if (!sym) {
        showSubmitMsg("Please enter your symptoms.", "error");
        return;
    }

    btn.disabled = true;
    btn.textContent = "⏳ Processing...";

    const symptoms = [sym];
    if (desc) symptoms.push(desc);

    try {
        const res = await fetch(`${API_BASE}/predict/symptoms`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ symptoms })
        });

        const data = await res.json();

        if (data.case_id) {
            showSubmitMsg("✅ Case submitted! AI analysis complete. Redirecting to overview...", "success");
            setTimeout(() => {
                showTab("overview");
                loadPatientCase();
            }, 1500);
        } else {
            showSubmitMsg("Error: " + (data.detail || "Failed to submit case."), "error");
        }
    } catch (err) {
        console.error(err);
        showSubmitMsg("Connection error. Please try again.", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "🚀 Submit to AI & Doctor";
    }
}

function showSubmitMsg(msg, type) {
    const el = document.getElementById("submitMsg");
    if (!el) return;
    el.style.display = "block";
    el.style.padding = "12px 16px";
    el.style.borderRadius = "10px";
    el.style.fontSize = "14px";
    el.style.fontWeight = "600";
    el.style.marginBottom = "16px";
    if (type === "error") {
        el.style.background = "rgba(248,113,113,0.12)";
        el.style.border = "1px solid rgba(248,113,113,0.3)";
        el.style.color = "#F87171";
    } else {
        el.style.background = "rgba(52,211,153,0.12)";
        el.style.border = "1px solid rgba(52,211,153,0.3)";
        el.style.color = "#34D399";
    }
    el.textContent = msg;
}

// ── Load Dashboard Data ──────────────────────────────────
let aiChartInstance = null;

async function loadPatientCase() {
    const token = getToken();
    if (!token) return;

    // Show loading
    const overviewInfo = document.getElementById("overviewCaseInfo");
    if (overviewInfo) {
        overviewInfo.innerHTML = `<div style="text-align:center;padding:30px;"><div class="loading-dots"><span></span><span></span><span></span></div><p style="color:var(--muted);margin-top:12px;">Loading your data...</p></div>`;
    }

    try {
        const res = await fetch(`${API_BASE}/patient/latest`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.exists) {
            if (overviewInfo) {
                overviewInfo.innerHTML = `
                    <div class="empty-state">
                        <span class="empty-icon">📋</span>
                        <p>No cases found. Submit your first case to get started.</p>
                        <button class="btn-primary" onclick="showTab('submit')">Submit First Case</button>
                    </div>`;
            }
            // Reset stats
            setEl("statCaseId", "—");
            setEl("statStatus", "—");
            setEl("statAI", "—");
            setEl("statReview", "—");
            return;
        }

        const c = data.case;

        // ── Update Stats ──
        setEl("statCaseId", "#" + c.id);
        setEl("statStatus", c.status ? c.status.charAt(0).toUpperCase() + c.status.slice(1) : "—");
        setEl("statAI", c.ai_result ? "✅ Done" : "⏳ Pending");
        setEl("statReview", c.status === "reviewed" ? "✅ Done" : "⏳ Pending");

        // ── Overview Case Info ──
        if (overviewInfo) {
            overviewInfo.innerHTML = `
                <div class="info-item">
                    <div class="info-label">Case ID</div>
                    <div class="info-value">#${c.id}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Status</div>
                    <div class="info-value"><span class="badge badge-${c.status}">${c.status}</span></div>
                </div>
                <div class="info-item">
                    <div class="info-label">Symptoms Reported</div>
                    <div class="info-value">${c.symptoms || "None"}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">X-Ray / Document</div>
                    <div class="info-value">${c.xray_result ? "✅ Attached" : "Not uploaded"}</div>
                </div>
            `;
        }

        // ── AI Results Tab ──
        const aiRaw = document.getElementById("aiRawOutput");
        const aiSymSum = document.getElementById("aiSymptomSummary");

        if (c.ai_result) {
            let aiObj = {};
            try {
                aiObj = typeof c.ai_result === "string" ? JSON.parse(c.ai_result) : c.ai_result;
            } catch(e) {
                aiObj = { [c.ai_result]: 1.0 };
            }

            // Render raw output
            if (aiRaw) {
                aiRaw.innerHTML = Object.entries(aiObj).map(([k, v]) =>
                    `<div class="info-item">
                        <div class="info-label">${k}</div>
                        <div class="info-value" style="color:var(--accent); font-size:20px; font-weight:800;">${(parseFloat(v) * 100).toFixed(1)}%</div>
                    </div>`
                ).join("");
            }

            // Render chart
            renderAIChart(aiObj, "aiChartWrap");
            renderAIChart(aiObj, "chartWrap");   // also on overview tab
        }

        if (aiSymSum) {
            aiSymSum.innerHTML = `
                <div class="info-item">
                    <div class="info-label">Reported Symptoms</div>
                    <div class="info-value">${c.symptoms || "No symptoms recorded"}</div>
                </div>
                ${c.xray_result ? `<div class="info-item">
                    <div class="info-label">Image Analysis</div>
                    <div class="info-value">${c.xray_result}</div>
                </div>` : ""}
            `;
        }

        // ── Doctor Review Tab ──
        renderDoctorReview(c);

    } catch (err) {
        console.error("loadPatientCase error:", err);
        if (overviewInfo) {
            overviewInfo.innerHTML = `<div style="color:var(--danger);padding:20px;text-align:center;">⚠️ Error loading case. Please refresh.</div>`;
        }
    }
}

function renderDoctorReview(c) {
    const doctorDiv = document.getElementById("doctorReviewContent");
    const overviewDr = document.getElementById("overviewDoctorReview");

    if (c.status === "reviewed") {
        const html = `
            <div class="card-grid">
                <div class="glass-card">
                    <div class="card-title">🏥 Final Diagnosis</div>
                    <div class="info-item" style="border-left-color: var(--success)">
                        <div class="info-label">Diagnosis</div>
                        <div class="info-value" style="color:var(--success); font-size:18px; font-weight:700;">${c.final_diagnosis || "—"}</div>
                    </div>
                </div>
                <div class="glass-card">
                    <div class="card-title">💊 Treatment Plan</div>
                    <div class="info-item">
                        <div class="info-label">Prescribed Tests / Medication</div>
                        <div class="info-value">${c.treatment_plan || "—"}</div>
                    </div>
                </div>
                <div class="glass-card card-full">
                    <div class="card-title">📝 Doctor's Notes</div>
                    <div class="info-item">
                        <div class="info-label">Clinical Observations</div>
                        <div class="info-value">${c.doctor_notes || "No additional notes provided."}</div>
                    </div>
                </div>
            </div>
        `;
        if (doctorDiv) doctorDiv.innerHTML = html;
        if (overviewDr) overviewDr.innerHTML = `
            <div class="info-item" style="border-left-color:var(--success)">
                <div class="info-label">Final Diagnosis</div>
                <div class="info-value" style="color:var(--success); font-weight:700;">${c.final_diagnosis || "—"}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Treatment Plan</div>
                <div class="info-value">${c.treatment_plan || "—"}</div>
            </div>
        `;
    } else {
        if (overviewDr) {
            overviewDr.innerHTML = `
                <div class="empty-state">
                    <span class="empty-icon">⏳</span>
                    <p>Your case is being reviewed by a specialist. You'll be notified instantly when ready.</p>
                </div>`;
        }
        if (doctorDiv) {
            doctorDiv.innerHTML = `
                <div class="glass-card">
                    <div class="card-title">👨‍⚕️ Review Pending</div>
                    <div class="empty-state">
                        <span class="empty-icon">⏳</span>
                        <p>Your case is awaiting doctor review. You'll receive a live notification here as soon as it's ready.</p>
                    </div>
                </div>`;
        }
    }
}

function setEl(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}

// ── Render Chart.js Chart ──────────────────────────────
function renderAIChart(aiObj, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const labels = Object.keys(aiObj);
    const values = Object.values(aiObj).map(v => {
        const n = parseFloat(v);
        return (n <= 1 ? n * 100 : n);
    });

    // Clear old content
    container.innerHTML = "";
    const canvas = document.createElement("canvas");
    canvas.id = containerId + "_canvas";
    container.appendChild(canvas);

    if (aiChartInstance && aiChartInstance.canvas?.id === canvas.id) {
        aiChartInstance.destroy();
    }

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: ["#38BDF8", "#818CF8", "#34D399", "#FBBF24", "#F87171", "#A78BFA"],
                borderWidth: 0,
                hoverOffset: 12
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: "#F1F5F9",
                        font: { family: "Outfit", size: 13 },
                        padding: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${parseFloat(ctx.raw).toFixed(1)}%`
                    }
                }
            }
        }
    });
}

// ── Socket.IO Real-time ──────────────────────────────────
function initSocket() {
    const token = getToken();
    const username = localStorage.getItem("username");
    if (!token || !username) return;

    const SOCKET_URL = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
        ? "http://localhost:8000"
        : "https://medifusion-api-11yd.onrender.com";

    const socket = io(SOCKET_URL, {
        transports: ["websocket", "polling"],
        auth: { token }
    });

    socket.on("connect", () => {
        console.log("[Socket] Connected:", socket.id);
        socket.emit("join_patient_room", { username });
    });

    socket.on("case_reviewed", (data) => {
        console.log("[Socket] case_reviewed:", data);

        // Flash live toast banner
        const toast = document.getElementById("liveToast");
        if (toast) {
            toast.innerHTML = `🟢 <strong>Live Update!</strong> Dr. completed your review. Diagnosis: <em>${data.final_diagnosis}</em>`;
            toast.style.display = "block";
            setTimeout(() => { toast.style.display = "none"; }, 12000);
        }

        // Update review tabs in-place (no reload)
        renderDoctorReview({
            status: "reviewed",
            final_diagnosis: data.final_diagnosis,
            treatment_plan: data.treatment_plan,
            doctor_notes: data.doctor_notes
        });

        // Update stats
        setEl("statReview", "✅ Done");
        setEl("statStatus", "Reviewed");
    });

    socket.on("connect_error", (err) => {
        console.warn("[Socket] Error (graceful):", err.message);
    });
}

// ── Boot ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    // Auth guard
    if (!guardAuth()) return;

    // Set username in sidebar
    const username = localStorage.getItem("username");
    const usernameEl = document.getElementById("sidebarUsername");
    if (usernameEl && username) usernameEl.textContent = username;

    // Load data and init socket
    loadPatientCase();
    initSocket();
});
