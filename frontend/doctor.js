// =======================================================
// doctor.js  —  Handles all Doctor Dashboard + Review Page
// =======================================================

const API_URL_PROD = "https://medifusion-api-11yd.onrender.com"; const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") ? "http://localhost:8000" : API_URL_PROD; const API_BASE = API;

// ------------------------------
// 1️⃣ Get Token
// ------------------------------
function getToken() {
    return localStorage.getItem("token");
}

// ------------------------------
// 2️⃣ Load Assigned Cases (doctor_dashboard.html)
// ------------------------------
async function loadAssignedCases() {
    const token = getToken();
    if (!token) {
        alert("Unauthorized. Please login again.");
        window.location.href = "login.html";
        return;
    }

    try {
        const res = await fetch(`${API}/doctor/assigned`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        const cases = await res.json();
        console.log("Assigned cases:", cases);

        const container = document.getElementById("assignedCases");
        container.innerHTML = "";

        if (!cases.length) {
            container.innerHTML = `<p>No assigned cases.</p>`;
            return;
        }

        cases.forEach(c => {
            const card = document.createElement("div");
            card.className = "case-card";

            card.innerHTML = `
                <h3>Case #${c.id}</h3>
                <p><b>Patient:</b> ${c.patient_name}</p>
                <p><b>Status:</b> ${c.status}</p>
                <button class="review-btn" onclick="openCase(${c.id})">Review Case</button>
            `;

            container.appendChild(card);
        });

    } catch (err) {
        console.error(err);
        alert("Error loading assigned cases.");
    }
}

// ------------------------------
// 3️⃣ Navigation — Open Case Review Page
// ------------------------------
function openCase(caseId) {
    localStorage.setItem("selected_case_id", caseId);
    window.location.href = "doctor_review.html";
}

// ------------------------------
// 4️⃣ Load Case Details in Review Page (doctor_review.html)
// ------------------------------
async function loadCaseForReview() {
    const token = getToken();
    const caseId = localStorage.getItem("selected_case_id");

    if (!token || !caseId) {
        alert("No case selected.");
        window.location.href = "doctor_dashboard.html";
        return;
    }

    try {
        const res = await fetch(`${API}/predict/case/${caseId}`, {
            headers: { "Authorization": `Bearer ${token}` }
        });

        const data = await res.json();
        console.log("Case data:", data);

        document.getElementById("symptomsBox").innerText =
            data.symptom_result ? JSON.stringify(data.symptom_result, null, 2) : "No symptoms found.";

        document.getElementById("aiBox").innerText =
            data.xray_result ? JSON.stringify(data.xray_result, null, 2) : "No X-ray result found.";

    } catch (err) {
        console.error(err);
        alert("Error loading case details.");
    }
}

// ------------------------------
// 5️⃣ Submit Doctor Review
// ------------------------------
async function submitReview() {
    const token = getToken();
    const caseId = localStorage.getItem("selected_case_id");

    const notes = document.getElementById("docNotes").value.trim();

    if (!notes) {
        alert("Please enter your notes before submitting.");
        return;
    }

    try {
        const res = await fetch(`${API}/doctor/review/${caseId}`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ notes })
        });

        const result = await res.json();
        console.log(result);

        alert("Review submitted successfully!");
        window.location.href = "doctor_dashboard.html";

    } catch (err) {
        console.error(err);
        alert("Error submitting review.");
    }
}
