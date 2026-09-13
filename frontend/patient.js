// =======================================================
// patient.js — Patient Dashboard
// =======================================================

function getToken() { return localStorage.getItem("token"); }

function guardAuth() {
    const token = getToken();
    const role = localStorage.getItem("role");
    if (window.location.pathname.includes("patient_dashboard")) {
        if (!token) { window.location.href = "login.html"; return false; }
        if (role && role !== "patient") { window.location.href = "login.html"; return false; }
    }
    return true;
}

function logout() { localStorage.clear(); window.location.href = "login.html"; }

// ── Tab Switching ────────────────────────────────────────
function showTab(tabName) {
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    const panel = document.getElementById("tab-" + tabName);
    const nav = document.getElementById("nav-" + tabName);
    if (panel) panel.classList.add("active");
    if (nav) nav.classList.add("active");

    const titles = {
        overview: ["My Health Overview", "Welcome back — here's your latest health status"],
        submit:   ["Submit New Case", "Describe your symptoms for AI analysis"],
        results:  ["AI Analysis Results", "Detailed breakdown of your diagnosis"],
        doctor:   ["Doctor's Review", "Your specialist's feedback and treatment plan"],
    };
    if (titles[tabName]) {
        setEl("topbarTitle", titles[tabName][0]);
        setEl("topbarSub", titles[tabName][1]);
    }
}

// ── Submit Case ──────────────────────────────────────────
async function submitCase() {
    const token = getToken();
    if (!token) { window.location.href = "login.html"; return; }

    const sym  = document.getElementById("symInput")?.value.trim();
    const desc = document.getElementById("descInput")?.value.trim();
    const btn  = document.getElementById("submitBtn");

    if (!sym) { showSubmitMsg("Please enter your symptoms.", "error"); return; }

    btn.disabled = true;
    btn.textContent = "⏳ Processing...";

    const symptoms = [sym];
    if (desc) symptoms.push(desc);

    try {
        const res = await fetch(`${API_BASE}/predict/symptoms`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify({ symptoms })
        });
        const data = await res.json();

        if (data.case_id) {
            showSubmitMsg("✅ Case submitted! AI analysis complete. Redirecting...", "success");
            setTimeout(() => { showTab("overview"); loadPatientCase(); }, 1500);
        } else {
            showSubmitMsg("Error: " + (data.detail || "Failed to submit case."), "error");
        }
    } catch (err) {
        showSubmitMsg("Connection error. Please try again.", "error");
    } finally {
        btn.disabled = false;
        btn.textContent = "🚀 Submit for AI Analysis";
    }
}

function showSubmitMsg(msg, type) {
    const el = document.getElementById("submitMsg");
    if (!el) return;
    el.className = "submit-msg " + type;
    el.style.display = "block";
    el.textContent = msg;
}

// ── Load Dashboard Data ──────────────────────────────────
let aiChartInstance = null;

async function loadPatientCase() {
    const token = getToken();
    if (!token) return;

    const overviewInfo = document.getElementById("overviewCaseInfo");
    if (overviewInfo) {
        overviewInfo.innerHTML = `<div style="text-align:center;padding:30px;"><div class="loading-dots"><span></span><span></span><span></span></div><p style="color:var(--muted);margin-top:12px;">Loading your data...</p></div>`;
    }

    try {
        const res = await fetch(`${API_BASE}/patient/latest`, { headers: { "Authorization": `Bearer ${token}` } });
        const data = await res.json();

        if (!data.exists) {
            if (overviewInfo) overviewInfo.innerHTML = `<div class="empty-state"><span class="empty-icon">📋</span><p>No cases found. Submit your first case to get started.</p><button class="btn-primary" onclick="showTab('submit')">Submit First Case</button></div>`;
            setEl("statCaseId","—"); setEl("statStatus","—"); setEl("statAI","—"); setEl("statReview","—");
            return;
        }

        const c = data.case;

        // Stats
        setEl("statCaseId", "#" + c.id);
        setEl("statStatus", c.status ? c.status.charAt(0).toUpperCase() + c.status.slice(1) : "—");
        setEl("statAI", c.patient_summary ? "✅ Done" : "⏳ Pending");
        setEl("statReview", c.status === "reviewed" ? "✅ Done" : "⏳ Pending");

        // Overview case info
        if (overviewInfo) {
            overviewInfo.innerHTML = `
                <div class="info-row"><div class="info-key">Case ID</div><div class="info-val">#${c.id}</div></div>
                <div class="info-row"><div class="info-key">Status</div><div class="info-val"><span class="badge badge-${c.status}">${c.status}</span></div></div>
                <div class="info-row"><div class="info-key">Symptoms</div><div class="info-val">${c.symptoms || "None"}</div></div>
                <div class="info-row"><div class="info-key">AI Result</div><div class="info-val">${c.raw_prediction_class || (c.patient_summary ? "✅ Analyzed" : "⏳ Pending")}</div></div>
            `;
        }

        // AI Results tab
        const aiRaw   = document.getElementById("aiRawOutput");
        const aiSymSum = document.getElementById("aiSymptomSummary");

        if (c.patient_summary) {
            if (aiRaw) {
                aiRaw.innerHTML = `
                    <div class="info-row"><div class="info-key">AI Summary</div><div class="info-val" style="line-height:1.7;">${c.patient_summary}</div></div>
                    ${c.raw_prediction_class ? `<div class="info-row"><div class="info-key">Classification</div><div class="info-val" style="color:var(--primary);font-weight:700;">${c.raw_prediction_class}</div></div>` : ""}
                `;
            }
            if (c.confidence_scores) {
                renderAIChart(c.confidence_scores, "aiChartWrap");
                renderAIChart(c.confidence_scores, "chartWrap");
            }
        } else {
            if (aiRaw) aiRaw.innerHTML = `<div class="info-row"><div class="info-key">Status</div><div class="info-val" style="color:var(--muted);font-style:italic;">⏳ Analysis pending...</div></div>`;
        }

        if (aiSymSum) {
            aiSymSum.innerHTML = `
                <div class="info-row"><div class="info-key">Symptoms</div><div class="info-val">${c.symptoms || "No symptoms recorded"}</div></div>
                ${c.patient_summary ? `<div class="info-row"><div class="info-key">What this means</div><div class="info-val" style="line-height:1.7;">${c.patient_summary}</div></div>` : ""}
            `;
        }

        renderDoctorReview(c);

    } catch (err) {
        console.error("loadPatientCase error:", err);
        if (overviewInfo) overviewInfo.innerHTML = `<div style="color:var(--danger);padding:20px;text-align:center;">⚠️ Error loading case. Please refresh.</div>`;
    }
}

function renderDoctorReview(c) {
    const doctorDiv  = document.getElementById("doctorReviewContent");
    const overviewDr = document.getElementById("overviewDoctorReview");

    if (c.status === "reviewed") {
        const html = `
            <div class="card-grid">
                <div class="card">
                    <div class="card-title">🏥 Final Diagnosis</div>
                    <div class="review-box highlight">
                        <div class="review-box-label">Diagnosis</div>
                        <div class="review-box-value">${c.final_diagnosis || "—"}</div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">💊 Treatment Plan</div>
                    <div class="review-box">
                        <div class="review-box-label">Prescribed Tests / Medication</div>
                        <div class="review-box-value">${c.treatment_plan || "—"}</div>
                    </div>
                </div>
                <div class="card card-full">
                    <div class="card-title">📝 Doctor's Notes</div>
                    <div class="review-box">
                        <div class="review-box-label">Clinical Observations</div>
                        <div class="review-box-value">${c.doctor_notes || "No additional notes."}</div>
                    </div>
                </div>
            </div>
        `;
        if (doctorDiv) doctorDiv.innerHTML = html;
        if (overviewDr) overviewDr.innerHTML = `
            <div class="info-row" style="border-left:3px solid var(--success);padding-left:12px;">
                <div class="info-key">Diagnosis</div>
                <div class="info-val" style="color:var(--success);font-weight:700;">${c.final_diagnosis || "—"}</div>
            </div>
            <div class="info-row" style="padding-left:12px;">
                <div class="info-key">Treatment</div>
                <div class="info-val">${c.treatment_plan || "—"}</div>
            </div>
        `;
    } else {
        const pending = `<div class="empty-state"><span class="empty-icon">⏳</span><p>Your case is awaiting doctor review. You'll be notified instantly when ready.</p></div>`;
        if (overviewDr) overviewDr.innerHTML = pending;
        if (doctorDiv) doctorDiv.innerHTML = `<div class="card"><div class="card-title">👨‍⚕️ Review Pending</div>${pending}</div>`;
    }
}

function setEl(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }

// ── Chart.js ─────────────────────────────────────────────
function renderAIChart(aiObj, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const labels = Object.keys(aiObj);
    const values = Object.values(aiObj).map(v => { const n = parseFloat(v); return n <= 1 ? n * 100 : n; });
    container.innerHTML = "";
    const canvas = document.createElement("canvas");
    container.appendChild(canvas);
    if (aiChartInstance && aiChartInstance.canvas?.id === canvas.id) aiChartInstance.destroy();
    aiChartInstance = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{ data: values, backgroundColor: ["#0057B8","#00b4d8","#16a34a","#d97706","#dc2626","#7c3aed"], borderWidth: 2, borderColor: "#fff", hoverOffset: 10 }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: "62%",
            plugins: {
                legend: { position: "right", labels: { color: "#1a2332", font: { family: "Inter", size: 12 }, padding: 14 } },
                tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${parseFloat(ctx.raw).toFixed(1)}%` } }
            }
        }
    });
}

// ── Socket.IO ────────────────────────────────────────────
function initSocket() {
    const token = getToken();
    const username = localStorage.getItem("username");
    if (!token || !username) return;

    const SOCKET_URL = ["localhost","127.0.0.1",""].includes(window.location.hostname)
        ? "http://localhost:8000"
        : "https://medifusion-api-11yd.onrender.com";

    const socket = io(SOCKET_URL, { transports: ["websocket","polling"], auth: { token } });

    socket.on("connect", () => { socket.emit("join_patient_room", { username }); });

    socket.on("case_reviewed", (data) => {
        const toast = document.getElementById("liveToast");
        if (toast) {
            toast.innerHTML = `🟢 <strong>Live Update!</strong> Dr. completed your review. Diagnosis: <em>${data.final_diagnosis}</em>`;
            toast.style.display = "block";
            setTimeout(() => { toast.style.display = "none"; }, 12000);
        }
        renderDoctorReview({ status: "reviewed", final_diagnosis: data.final_diagnosis, treatment_plan: data.treatment_plan, doctor_notes: data.doctor_notes });
        setEl("statReview", "✅ Done");
        setEl("statStatus", "Reviewed");
    });

    socket.on("connect_error", (err) => { console.warn("[Socket] graceful error:", err.message); });
}

// ── Boot ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    if (!guardAuth()) return;
    const username = localStorage.getItem("username");
    const el = document.getElementById("sidebarUsername");
    if (el && username) el.textContent = username;
    loadPatientCase();
    initSocket();
});
