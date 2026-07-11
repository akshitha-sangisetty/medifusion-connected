// =======================================================
// doctor.js — Doctor Dashboard Integration & Review Logic
// =======================================================

let currentCaseId = null;
let aiChartInstance = null;

function getToken() {
    return localStorage.getItem("token");
}

function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// Set doctor name from localStorage
const storedUsername = localStorage.getItem("username");
const nameEl = document.getElementById("doctorName");
if (nameEl && storedUsername) nameEl.textContent = `Dr. ${storedUsername}`;

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = "block";
    setTimeout(() => { toast.style.display = "none"; }, 3500);
}

// ----------------------------------
// Load All Pending Cases for Sidebar
// ----------------------------------
async function loadAssignedCases() {
    const token = getToken();
    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const caseList = document.getElementById("caseList");
    caseList.innerHTML = `<div class="no-cases">Loading...</div>`;

    try {
        const res = await fetch(`${API_BASE}/doctor/assigned`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (res.status === 403) {
            window.location.href = "login.html";
            return;
        }

        const data = await res.json();
        const cases = data.cases || [];

        if (cases.length === 0) {
            caseList.innerHTML = `<div class="no-cases">No cases pending review.<br><br>Waiting for patients to submit cases.</div>`;
            return;
        }

        caseList.innerHTML = "";
        cases.forEach(c => {
            const statusClass = c.status === "reviewed" ? "dot-reviewed" : c.status === "predicted" ? "dot-predicted" : "dot-new";
            const item = document.createElement("div");
            item.className = "case-item";
            item.id = `case-item-${c.id}`;
            item.innerHTML = `
                <div class="case-item-name">
                    <span class="status-dot ${statusClass}"></span>
                    ${c.patient_name}
                </div>
                <div class="case-item-meta">${c.symptoms ? c.symptoms.substring(0, 60) + "..." : "No symptoms listed"}</div>
                <div style="margin-top: 8px; font-size: 12px; color: var(--text-secondary);">Case #${c.id} • ${c.status}</div>
            `;
            item.onclick = () => openCase(c);
            caseList.appendChild(item);
        });

    } catch (err) {
        console.error(err);
        caseList.innerHTML = `<div class="no-cases" style="color: var(--danger)">Error loading cases. Check connection.</div>`;
    }
}

// ----------------------------------
// Open a Specific Case for Review
// ----------------------------------
function openCase(c) {
    currentCaseId = c.id;

    // Highlight active case in sidebar
    document.querySelectorAll(".case-item").forEach(el => el.classList.remove("active"));
    const item = document.getElementById(`case-item-${c.id}`);
    if (item) item.classList.add("active");

    // Show review panel, hide empty state
    document.getElementById("emptyState").style.display = "none";
    document.getElementById("reviewPanel").style.display = "block";

    // Populate header info
    document.getElementById("reviewPatientName").textContent = `Patient: ${c.patient_name} (Case #${c.id})`;
    const statusEl = document.getElementById("reviewStatus");
    statusEl.textContent = c.status;
    statusEl.className = `status-badge status-${c.status}`;

    // Symptoms
    document.getElementById("symptomsDisplay").textContent = c.symptoms || "No symptoms recorded.";

    // AI Results
    const aiResult = c.symptom_result;
    if (aiResult) {
        let displayText = "";
        try {
            const parsed = typeof aiResult === "string" ? JSON.parse(aiResult) : aiResult;
            displayText = Object.entries(parsed).map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`).join("\n");
        } catch(e) {
            displayText = String(aiResult);
        }
        document.getElementById("aiResultDisplay").textContent = displayText;
        renderAIChart(aiResult);
    } else {
        document.getElementById("aiResultDisplay").textContent = "No AI symptom analysis available.";
        document.getElementById("chartFallback").style.display = "block";
        document.getElementById("aiChart").style.display = "none";
    }

    // X-Ray Result
    const xrayResult = c.xray_result;
    if (xrayResult) {
        let xrayText = "";
        try {
            const parsed = typeof xrayResult === "string" ? JSON.parse(xrayResult) : xrayResult;
            xrayText = Object.entries(parsed).map(([k, v]) => `${k}: ${(v * 100).toFixed(1)}%`).join("\n");
        } catch(e) {
            xrayText = String(xrayResult);
        }
        document.getElementById("xrayDisplay").textContent = xrayText;
    } else {
        document.getElementById("xrayDisplay").textContent = "No image/X-ray uploaded by patient.";
    }

    // Pre-fill existing review if already reviewed
    document.getElementById("docNotes").value = c.doctor_notes || "";
    document.getElementById("docTests").value = c.treatment_plan || "";
    document.getElementById("finalDiag").value = c.final_diagnosis || "";
}

// ----------------------------------
// Render Chart.js AI Visualization
// ----------------------------------
function renderAIChart(predictionData) {
    document.getElementById("chartFallback").style.display = "none";
    const canvas = document.getElementById("aiChart");
    canvas.style.display = "block";

    let prediction = {};
    try {
        prediction = typeof predictionData === "string" ? JSON.parse(predictionData) : predictionData;
    } catch(e) {
        if (typeof predictionData === "string") {
            prediction = { [predictionData]: 1.0 };
        }
    }

    const labels = Object.keys(prediction);
    const dataValues = Object.values(prediction).map(v => typeof v === "number" ? (v <= 1 ? parseFloat((v * 100).toFixed(1)) : v) : parseFloat(v) * 100);

    if (aiChartInstance) {
        aiChartInstance.destroy();
    }

    aiChartInstance = new Chart(canvas, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data: dataValues,
                backgroundColor: ["#A78BFA", "#38BDF8", "#10B981", "#F59E0B", "#EF4444"],
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
                        color: "#F8FAFC",
                        font: { family: "Outfit", size: 13 },
                        padding: 16
                    }
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.raw.toFixed(1)}%`
                    }
                }
            }
        }
    });
}

// ----------------------------------
// Submit Doctor Review
// ----------------------------------
async function submitReview() {
    const token = getToken();
    if (!token || !currentCaseId) {
        showToast("Please select a case first.", "error");
        return;
    }

    const notes = document.getElementById("docNotes").value.trim();
    const tests = document.getElementById("docTests").value.trim();
    const diag = document.getElementById("finalDiag").value.trim();

    if (!diag) {
        showToast("Please enter a final diagnosis before submitting.", "error");
        return;
    }

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
            showToast("✅ Review submitted! Patient has been notified.", "success");
            // Update the status badge
            const statusEl = document.getElementById("reviewStatus");
            statusEl.textContent = "reviewed";
            statusEl.className = "status-badge status-reviewed";
            // Refresh sidebar
            setTimeout(loadAssignedCases, 500);
        } else {
            showToast("Error: " + (data.detail || "Submission failed."), "error");
        }

    } catch (err) {
        console.error(err);
        showToast("Connection error. Could not submit review.", "error");
    }
}
