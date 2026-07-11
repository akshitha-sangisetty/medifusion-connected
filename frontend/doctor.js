// =======================================================
// doctor.js — Doctor Dashboard (Fixed & Complete)
// =======================================================

let currentCaseId = null;
let aiChartInstance = null;

// ── Auth Guard ───────────────────────────────────────────
function getToken() {
    return localStorage.getItem("token");
}

function guardDoctorAuth() {
    const token = getToken();
    const role = localStorage.getItem("role");
    if (!token) { window.location.href = "login.html"; return false; }
    if (role && role !== "doctor") { window.location.href = "login.html"; return false; }
    return true;
}

function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// ── Toast ────────────────────────────────────────────────
function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = "block";
    setTimeout(() => { toast.style.display = "none"; }, 4000);
}

// ── Load Cases into Sidebar ──────────────────────────────
async function loadAssignedCases() {
    const token = getToken();
    if (!token) return;

    const caseList = document.getElementById("caseList");
    if (caseList) caseList.innerHTML = `<div class="no-cases">Fetching cases...</div>`;

    try {
        const res = await fetch(`${API_BASE}/doctor/assigned`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (res.status === 401 || res.status === 403) {
            window.location.href = "login.html";
            return;
        }

        const data = await res.json();
        const cases = data.cases || [];

        if (!caseList) return;

        if (cases.length === 0) {
            caseList.innerHTML = `<div class="no-cases">No cases pending review yet.<br><br>Patients must submit cases first.</div>`;
            return;
        }

        caseList.innerHTML = "";
        cases.forEach(c => {
            const dotClass = c.status === "reviewed" ? "dot-reviewed" : c.status === "predicted" ? "dot-predicted" : "dot-new";
            const div = document.createElement("div");
            div.className = "case-item";
            div.id = `case-item-${c.id}`;
            div.innerHTML = `
                <div class="case-patient">
                    <span class="status-dot ${dotClass}"></span>
                    ${c.patient_name}
                </div>
                <div class="case-symptoms">${c.symptoms ? c.symptoms.substring(0, 70) + "…" : "No symptoms listed"}</div>
                <div class="case-meta">Case #${c.id} &bull; <strong>${c.status}</strong></div>
            `;
            div.onclick = () => openCase(c);
            caseList.appendChild(div);
        });

    } catch (err) {
        console.error("loadAssignedCases error:", err);
        if (caseList) caseList.innerHTML = `<div class="no-cases" style="color:var(--danger)">⚠️ Error loading cases. Check your connection.</div>`;
    }
}

// ── Open a Case for Review ───────────────────────────────
function openCase(c) {
    currentCaseId = c.id;

    // Highlight in sidebar
    document.querySelectorAll(".case-item").forEach(el => el.classList.remove("active"));
    const item = document.getElementById(`case-item-${c.id}`);
    if (item) item.classList.add("active");

    // Show review panel, hide empty state
    document.getElementById("emptyState").style.display = "none";
    document.getElementById("reviewPanel").style.display = "block";

    // Header
    const nameEl = document.getElementById("reviewPatientName");
    const idEl = document.getElementById("reviewCaseId");
    const statusEl = document.getElementById("reviewStatus");
    if (nameEl) nameEl.textContent = c.patient_name;
    if (idEl) idEl.textContent = `Case #${c.id}`;
    if (statusEl) {
        statusEl.textContent = c.status;
        statusEl.className = `badge badge-${c.status}`;
    }

    // Symptoms
    const symEl = document.getElementById("symptomsDisplay");
    if (symEl) symEl.textContent = c.symptoms || "No symptoms recorded.";

    // AI Chart + Result
    const aiWrap = document.getElementById("aiChartWrap");
    const aiText = document.getElementById("aiResultDisplay");

    if (c.symptom_result) {
        let aiObj = {};
        try {
            aiObj = typeof c.symptom_result === "string" ? JSON.parse(c.symptom_result) : c.symptom_result;
        } catch(e) {
            aiObj = { [c.symptom_result]: 1.0 };
        }

        // Text breakdown
        if (aiText) {
            aiText.textContent = Object.entries(aiObj)
                .map(([k, v]) => `${k}: ${(parseFloat(v) * 100).toFixed(1)}%`)
                .join("\n");
        }

        // Chart
        renderDoctorChart(aiObj, aiWrap);

    } else {
        if (aiText) aiText.textContent = "No AI symptom analysis available.";
        if (aiWrap) aiWrap.innerHTML = `<span style="color:var(--muted);font-style:italic;font-size:14px;">No AI data</span>`;
    }

    // X-Ray
    const xrayEl = document.getElementById("xrayDisplay");
    if (xrayEl) {
        if (c.xray_result) {
            let xObj = {};
            try {
                xObj = typeof c.xray_result === "string" ? JSON.parse(c.xray_result) : c.xray_result;
                xrayEl.textContent = Object.entries(xObj)
                    .map(([k, v]) => `${k}: ${(parseFloat(v) * 100).toFixed(1)}%`)
                    .join("\n");
            } catch(e) {
                xrayEl.textContent = String(c.xray_result);
            }
        } else {
            xrayEl.textContent = "No image or X-ray uploaded by patient.";
        }
    }

    // Pre-fill existing review fields
    const notesEl = document.getElementById("docNotes");
    const testsEl = document.getElementById("docTests");
    const diagEl = document.getElementById("finalDiag");
    if (notesEl) notesEl.value = c.doctor_notes || "";
    if (testsEl) testsEl.value = c.treatment_plan || "";
    if (diagEl) diagEl.value = c.final_diagnosis || "";
}

// ── Render Chart.js ──────────────────────────────────────
function renderDoctorChart(aiObj, container) {
    if (!container) return;

    const labels = Object.keys(aiObj);
    const values = Object.values(aiObj).map(v => {
        const n = parseFloat(v);
        return (n <= 1 ? n * 100 : n);
    });

    container.innerHTML = "";
    const canvas = document.createElement("canvas");
    container.appendChild(canvas);

    if (aiChartInstance) {
        try { aiChartInstance.destroy(); } catch(e) {}
    }

    aiChartInstance = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: ["#A78BFA", "#38BDF8", "#34D399", "#FBBF24", "#F87171", "#818CF8"],
                borderWidth: 0,
                hoverOffset: 14
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "65%",
            plugins: {
                legend: {
                    position: "right",
                    labels: { color: "#F1F5F9", font: { family: "Outfit", size: 13 }, padding: 16 }
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

// ── Submit Review ────────────────────────────────────────
async function submitReview() {
    const token = getToken();
    if (!token || !currentCaseId) {
        showToast("Please select a case first.", "error");
        return;
    }

    const notes = document.getElementById("docNotes")?.value.trim() || "";
    const tests = document.getElementById("docTests")?.value.trim() || "";
    const diag  = document.getElementById("finalDiag")?.value.trim() || "";

    if (!diag) {
        showToast("Please enter a final diagnosis before submitting.", "error");
        return;
    }

    const btn = document.getElementById("submitReviewBtn");
    if (btn) { btn.disabled = true; btn.textContent = "⏳ Submitting…"; }

    try {
        const res = await fetch(`${API_BASE}/doctor/review/${currentCaseId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ notes, tests, diag })
        });

        const data = await res.json();

        if (res.ok) {
            showToast("✅ Review submitted! Patient has been notified in real-time.", "success");

            // Update status badge
            const statusEl = document.getElementById("reviewStatus");
            if (statusEl) { statusEl.textContent = "reviewed"; statusEl.className = "badge badge-reviewed"; }

            // Refresh sidebar
            setTimeout(loadAssignedCases, 600);

        } else {
            showToast("Error: " + (data.detail || "Submission failed."), "error");
        }

    } catch (err) {
        console.error("submitReview error:", err);
        showToast("Connection error. Could not submit review.", "error");
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Submit Review & Notify Patient in Real-Time ⚡"; }
    }
}

// ── Socket.IO Real-time ──────────────────────────────────
function initDoctorSocket() {
    const token = getToken();
    if (!token) return;

    const SOCKET_URL = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
        ? "http://localhost:8000"
        : "https://medifusion-api-11yd.onrender.com";

    const socket = io(SOCKET_URL, {
        transports: ["websocket", "polling"],
        auth: { token }
    });

    socket.on("connect", () => {
        console.log("[Socket] Doctor connected:", socket.id);
        socket.emit("join_doctor_room", {});
    });

    socket.on("doctor_case_updated", (data) => {
        console.log("[Socket] Case updated:", data);
        // Silently refresh sidebar
        loadAssignedCases();
    });

    socket.on("connect_error", (err) => {
        console.warn("[Socket] Doctor socket graceful error:", err.message);
    });
}

// ── Boot ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    if (!guardDoctorAuth()) return;

    // Set doctor name in sidebar
    const username = localStorage.getItem("username");
    const nameEl = document.getElementById("doctorName");
    if (nameEl && username) nameEl.textContent = `Dr. ${username}`;

    loadAssignedCases();
    initDoctorSocket();
});
