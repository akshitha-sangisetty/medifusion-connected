// =======================================================
// patient.js — Patient Dashboard + Submit Symptoms + Upload
// =======================================================

const API_URL_PROD = "https://medifusion-api-11yd.onrender.com"; const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") ? "http://localhost:8000" : API_URL_PROD; const API_BASE = API;

// ----------------------------------
// 🔑 Get authentication token
// ----------------------------------
function getToken() {
    return localStorage.getItem("token");
}

// ----------------------------------
// 1️⃣ Submit Symptoms (submit_symptoms.html)
// ----------------------------------
async function submitSymptoms() {
    const token = getToken();
    if (!token) {
        alert("Please login again.");
        window.location.href = "login.html";
        return;
    }

    const symptoms = document.getElementById("sym").value.trim();
    const desc = document.getElementById("desc").value.trim();

    if (!symptoms) {
        alert("Please enter symptoms.");
        return;
    }

    const symptomsList = [symptoms];
    if (desc) symptomsList.push(desc);

    try {
        const res = await fetch(`${API}/predict/symptoms`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ symptoms: symptomsList })
        });

        const data = await res.json();
        console.log("Symptom Case Created:", data);

        if (data.case_id) {
            localStorage.setItem("last_case_id", data.case_id);
            alert("Case submitted successfully!");
        } else {
            alert("Error creating case.");
        }

    } catch (err) {
        console.error(err);
        alert("Error submitting symptoms.");
    }
}

// ----------------------------------
// 2️⃣ Upload X-ray Image (patient_dashboard.html)
// ----------------------------------
async function uploadImage() {
    const token = getToken();
    if (!token) {
        alert("Please login again.");
        window.location.href = "login.html";
        return;
    }

    const fileInput = document.getElementById("xrayFile");
    if (!fileInput || fileInput.files.length === 0) {
        alert("Please select an image.");
        return;
    }

    const form = new FormData();
    form.append("file", fileInput.files[0]);

    try {
        const res = await fetch(`${API}/predict/image`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` },
            body: form
        });

        const data = await res.json();
        console.log("Image Case Created:", data);

        if (data.case_id) {
            localStorage.setItem("last_case_id", data.case_id);
            alert("Image uploaded successfully!");
        } else {
            alert("Error uploading image.");
        }

    } catch (err) {
        console.error(err);
        alert("Error uploading image.");
    }
}

// ----------------------------------
// 3️⃣ Load Patient Dashboard Case Details
// ----------------------------------
async function loadPatientCase() {
    const token = getToken();
    const caseId = localStorage.getItem("last_case_id");

    if (!token || !caseId) {
        console.log("No active case.");
        return;
    }

    try {
        const res = await fetch(`${API}/predict/case/${caseId}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        const data = await res.json();
        console.log("Loaded Case:", data);

        // Symptoms
        document.getElementById("symptoms").innerText =
            data.symptom_result ? JSON.stringify(data.symptom_result, null, 2) : "—";

        // AI Result
        document.getElementById("aiResult").innerText =
            data.xray_result ? JSON.stringify(data.xray_result, null, 2) : "—";

        // Doctor Notes
        document.getElementById("docComments").innerText =
            data.doctor_notes || "—";

        // Final Diagnosis
        document.getElementById("diagnosis").innerText =
            data.final_diagnosis || "—";

        // Treatment Plan
        document.getElementById("treatment").innerText =
            data.treatment_plan || "—";

    } catch (err) {
        console.error(err);
        alert("Error loading patient case.");
    }
}

// ----------------------------------
// 4️⃣ Logout
// ----------------------------------
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    alert("Logged out.");
    window.location.href = "login.html";
}
