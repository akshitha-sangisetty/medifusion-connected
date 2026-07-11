// =======================================
// lab.js  (MediFusion Frontend Integration)
// =======================================

const API_BASE = "http://localhost:8000";

// -----------------------------
// Upload Lab Report
// -----------------------------
async function uploadLabReport() {
    const token = localStorage.getItem("token");
    const caseId = document.getElementById("caseId").value.trim();
    const file = document.getElementById("fileUpload").files[0];
    const comments = document.getElementById("comments").value.trim();

    if (!caseId) {
        alert("Please enter Case ID.");
        return;
    }

    if (!file) {
        alert("Please select a file.");
        return;
    }

    // Prepare form data
    const formData = new FormData();
    formData.append("case_id", caseId);
    formData.append("file", file);
    formData.append("comments", comments);

    try {
        const res = await fetch(`${API_BASE}/lab/upload-report`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`
            },
            body: formData
        });

        const data = await res.json();

        if (res.status === 200) {
            alert(`Report for Case ID ${caseId} uploaded successfully!`);
            document.getElementById("caseId").value = "";
            document.getElementById("fileUpload").value = "";
            document.getElementById("comments").value = "";
        } else {
            alert("Upload failed: " + (data.detail || "Unknown error"));
        }

    } catch (err) {
        alert("Network error: " + err.message);
    }
}

// -----------------------------
// Logout Function
// -----------------------------
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}
