// ===========================================
// api.js  —  Global Frontend API Layer
// ===========================================

const PROD_API_URL = "https://medifusion-api-11yd.onrender.com";
// "" covers file:// protocol (opening HTML directly), localhost covers local dev
const API_BASE = (["localhost", "127.0.0.1", ""].includes(window.location.hostname))
    ? "http://localhost:8000"
    : PROD_API_URL;

// -------------------------------------------
//  FETCH WITH RETRY (handles Render cold start)
//  Render free tier sleeps after inactivity —
//  first request can take 30-60s to respond.
//  This retries up to `retries` times with a
//  delay, and calls onWaiting() so the UI can
//  show a "waking up" message.
// -------------------------------------------
async function fetchWithRetry(url, options = {}, retries = 3, delayMs = 5000, onWaiting = null) {
    for (let attempt = 1; attempt <= retries; attempt++) {
        try {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), 60000); // 60s timeout per attempt
            const res = await fetch(url, { ...options, signal: controller.signal });
            clearTimeout(timeout);
            return res;
        } catch (err) {
            if (attempt < retries) {
                if (onWaiting) onWaiting(attempt, retries);
                await new Promise(r => setTimeout(r, delayMs));
            } else {
                throw err;
            }
        }
    }
}

// -------------------------------------------
//  AUTH MODULE
// -------------------------------------------

// Login (POST /auth/login)
async function apiLogin(username, password) {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body
    });

    return res.json();
}

// Signup (POST /auth/register)
async function apiSignup(data) {
    const res = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });

    return res.json();
}


// -------------------------------------------
//  PATIENT MODULE
// -------------------------------------------

// Submit symptoms (POST /predict/symptoms)
async function apiSubmitSymptoms(token, symptomsList) {
    const res = await fetch(`${API_BASE}/predict/symptoms`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ symptoms: symptomsList })
    });

    return res.json();
}

// Upload X-ray image (POST /predict/image)
async function apiUploadImage(token, formData) {
    const res = await fetch(`${API_BASE}/predict/image`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
    });

    return res.json();
}

// Get case details (GET /predict/case/{id})
async function apiGetCase(token, caseId) {
    const res = await fetch(`${API_BASE}/predict/case/${caseId}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    return res.json();
}


// -------------------------------------------
//  DOCTOR MODULE
// -------------------------------------------

// Get assigned cases (GET /doctor/assigned)
async function apiDoctorAssignedCases(token) {
    const res = await fetch(`${API_BASE}/doctor/assigned`, {
        headers: { "Authorization": `Bearer ${token}` }
    });

    return res.json();
}

// Submit doctor review (POST /doctor/review/{caseId})
async function apiDoctorSubmitReview(token, caseId, notes) {
    const res = await fetch(`${API_BASE}/doctor/review/${caseId}`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ notes })
    });

    return res.json();
}


// -------------------------------------------
//  LAB MODULE (backend route coming in Phase 3)
// -------------------------------------------

// Upload report
async function apiLabUploadReport(token, formData) {
    const res = await fetch(`${API_BASE}/lab/upload-report`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${token}`
        },
        body: formData
    });

    return res.json();
}
