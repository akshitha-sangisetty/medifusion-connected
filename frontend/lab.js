// =======================================================
// lab.js — Lab Technician Dashboard
// =======================================================

function getToken() { return localStorage.getItem("token"); }

function guardAuth() {
    const token = getToken();
    const role = localStorage.getItem("role");
    if (!token) { window.location.href = "login.html"; return false; }
    if (role && role !== "lab") { window.location.href = "login.html"; return false; }
    return true;
}

function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

// ── Tab Switching ────────────────────────────────────────
function showTab(tabName) {
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    const panel = document.getElementById("tab-" + tabName);
    const nav = document.getElementById("nav-" + tabName);
    if (panel) panel.classList.add("active");
    if (nav) nav.classList.add("active");

    if (tabName === "history") loadHistory();
    if (tabName === "overview") loadOverview();
}

// ── Show message helper ──────────────────────────────────
function showMsg(elId, text, type) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.textContent = text;
    el.className = `msg ${type}`;
    el.style.display = "block";
    if (type === "success") setTimeout(() => { el.style.display = "none"; }, 5000);
}

// ── Load Overview stats ──────────────────────────────────
async function loadOverview() {
    const token = getToken();
    if (!token) return;

    try {
        const data = await apiLabMyUploads(token);
        const uploads = data.uploads || [];

        // Unique case IDs
        const caseSet = new Set(uploads.map(u => u.case_id));
        document.getElementById("statUploads").textContent = uploads.length;
        document.getElementById("statCases").textContent = caseSet.size;

        // Recent 5 uploads
        const recentEl = document.getElementById("recentUploads");
        if (uploads.length === 0) {
            recentEl.innerHTML = `<div class="empty-state"><span class="empty-icon">📭</span><p>No reports uploaded yet.</p></div>`;
            document.getElementById("statReviewed").textContent = "0";
            return;
        }

        const rows = uploads.slice(0, 5).map(u => `
            <tr>
                <td>#${u.case_id}</td>
                <td>${u.original_filename || "—"}</td>
                <td>${u.file_type || "—"}</td>
                <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</td>
            </tr>
        `).join("");

        recentEl.innerHTML = `
            <table class="uploads-table">
                <thead><tr><th>Case ID</th><th>File</th><th>Type</th><th>Date</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;

        document.getElementById("statReviewed").textContent = "—";
    } catch (err) {
        console.error("loadOverview error:", err);
    }
}

// ── Patient Lookup ───────────────────────────────────────
let foundCaseId = null;

async function lookupPatient() {
    const token = getToken();
    const username = document.getElementById("lookupInput").value.trim();

    if (!username) {
        showMsg("lookupMsg", "Please enter a patient username.", "error");
        return;
    }

    showMsg("lookupMsg", "Searching...", "success");

    try {
        const data = await apiLabLookupPatient(token, username);

        if (data.detail) {
            showMsg("lookupMsg", data.detail, "error");
            document.getElementById("lookupResult").classList.remove("show");
            document.getElementById("uploadForm").style.display = "none";
            document.getElementById("uploadLocked").style.display = "block";
            return;
        }

        // Populate result card
        document.getElementById("lookupPatientName").textContent =
            `${data.patient_full_name || data.patient_username} (@${data.patient_username})`;
        document.getElementById("lookupCaseId").textContent = `#${data.case_id}`;
        document.getElementById("lookupSymptoms").textContent = data.symptoms || "Not recorded";
        document.getElementById("lookupAIPrediction").textContent = data.ai_prediction || "Pending";
        document.getElementById("lookupCaseStatus").innerHTML =
            `<span class="badge badge-${data.case_status}">${data.case_status}</span>`;

        const atts = data.existing_attachments || [];
        document.getElementById("lookupAttachments").textContent =
            atts.length > 0
                ? atts.map(a => `${a.uploaded_by}: ${a.original_filename}`).join(", ")
                : "None";

        document.getElementById("lookupResult").classList.add("show");

        // Unlock upload form
        foundCaseId = data.case_id;
        document.getElementById("uploadCaseId").value = data.case_id;
        document.getElementById("uploadLocked").style.display = "none";
        document.getElementById("uploadForm").style.display = "block";

        showMsg("lookupMsg", `✅ Found patient "${data.patient_username}" — Case #${data.case_id}`, "success");

    } catch (err) {
        console.error("lookupPatient error:", err);
        showMsg("lookupMsg", "Connection error. Please try again.", "error");
    }
}

// ── Upload Report ────────────────────────────────────────
async function uploadReport() {
    const token = getToken();
    const caseId = document.getElementById("uploadCaseId").value;
    const file = document.getElementById("fileUpload").files[0];
    const comments = document.getElementById("comments").value.trim();
    const btn = document.getElementById("uploadBtn");

    if (!caseId) { showMsg("uploadMsg", "Please search for a patient first.", "error"); return; }
    if (!file)   { showMsg("uploadMsg", "Please select a file to upload.", "error"); return; }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Uploading...';

    const formData = new FormData();
    formData.append("case_id", caseId);
    formData.append("file", file);
    formData.append("comments", comments);

    try {
        const data = await apiLabUploadReport(token, formData);

        if (data.attachment_id || data.message) {
            showMsg("uploadMsg", `✅ Report uploaded successfully to Case #${caseId}!`, "success");
            // Reset form
            document.getElementById("fileUpload").value = "";
            document.getElementById("comments").value = "";
            foundCaseId = null;
        } else {
            showMsg("uploadMsg", "Upload failed: " + (data.detail || "Unknown error"), "error");
        }

    } catch (err) {
        console.error("uploadReport error:", err);
        showMsg("uploadMsg", "Connection error. Please try again.", "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = "⬆️ Submit Report to Case";
    }
}

// ── Upload History ───────────────────────────────────────
async function loadHistory() {
    const token = getToken();
    if (!token) return;

    const el = document.getElementById("historyContent");
    el.innerHTML = `<div class="empty-state"><span class="empty-icon">⏳</span><p>Loading...</p></div>`;

    try {
        const data = await apiLabMyUploads(token);
        const uploads = data.uploads || [];

        if (uploads.length === 0) {
            el.innerHTML = `<div class="empty-state"><span class="empty-icon">📭</span><p>No reports uploaded yet.</p></div>`;
            return;
        }

        const rows = uploads.map(u => `
            <tr>
                <td>#${u.case_id}</td>
                <td>${u.original_filename || "—"}</td>
                <td>${u.file_type || "—"}</td>
                <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</td>
            </tr>
        `).join("");

        el.innerHTML = `
            <table class="uploads-table">
                <thead><tr><th>Case ID</th><th>File</th><th>Type</th><th>Date Uploaded</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;

    } catch (err) {
        console.error("loadHistory error:", err);
        el.innerHTML = `<div class="empty-state"><span class="empty-icon">⚠️</span><p style="color:var(--danger)">Error loading history.</p></div>`;
    }
}

// ── Boot ─────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    if (!guardAuth()) return;

    const username = localStorage.getItem("username");
    const el = document.getElementById("sidebarUsername");
    if (el && username) el.textContent = username;

    loadOverview();
});
