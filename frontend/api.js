// ===========================================
// api.js  —  Global Frontend API Layer
// ===========================================

// Automatically point to localhost during local development, and the Render backend in production.
// NOTE: You will need to replace the PROD_API_URL below with your actual Render deployment URL.
const PROD_API_URL = "https://medifusion-api-11yd.onrender.com";
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") 
    ? "http://localhost:8000" 
    : PROD_API_URL;

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
