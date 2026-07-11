// =======================================================
// patient.js — Patient Dashboard Integration & Visualization
// =======================================================

function getToken() {
    return localStorage.getItem("token");
}

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    window.location.href = "login.html";
}

// ----------------------------------
// Submit Symptoms
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
        const res = await fetch(`${API_BASE}/predict/symptoms`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ symptoms: symptomsList })
        });

        const data = await res.json();
        
        if (data.case_id) {
            window.location.href = "patient_dashboard.html";
        } else {
            alert("Error creating case.");
        }
    } catch (err) {
        console.error(err);
        alert("Error submitting symptoms.");
    }
}

// ----------------------------------
// Load Patient Dashboard Data
// ----------------------------------
async function loadPatientCase() {
    const token = getToken();
    if (!token) return;

    try {
        const res = await fetch(`${API_BASE}/patient/latest`, {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();

        if (!data.exists) {
            document.getElementById("caseInfoContainer").innerHTML = `<div class="no-data">No active case found. Submit a new case to begin.</div>`;
            return;
        }

        const c = data.case;

        // Render Case Info
        document.getElementById("caseInfoContainer").innerHTML = `
            <div class="info-item">
                <div class="info-label">Case Status</div>
                <div class="status-badge status-${c.status}">${c.status}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Reported Symptoms</div>
                <div class="info-value">${c.symptoms || 'None'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Uploaded Document</div>
                <div class="info-value">${c.xray_result ? 'X-Ray Image Attached' : 'None'}</div>
            </div>
        `;

        // Render Doctor's Review
        if (c.status === "reviewed") {
            document.getElementById("reviewContainer").innerHTML = `
                <div class="info-item">
                    <div class="info-label">Final Diagnosis</div>
                    <div class="info-value" style="color: var(--accent-glow); font-size: 18px;">${c.final_diagnosis || '—'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Treatment Plan / Tests</div>
                    <div class="info-value">${c.treatment_plan || '—'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Doctor's Notes</div>
                    <div class="info-value">${c.doctor_notes || '—'}</div>
                </div>
            `;
        }

        // Visualize AI Prediction
        const aiData = c.ai_result || c.xray_result;
        if (aiData) {
            renderChart(aiData);
        }

    } catch (err) {
        console.error(err);
        document.getElementById("caseInfoContainer").innerHTML = `<div class="no-data" style="color:var(--danger)">Error loading case data.</div>`;
    }
}

// ----------------------------------
// Render AI Chart
// ----------------------------------
function renderChart(predictionString) {
    let prediction = {};
    try {
        // Handle if prediction is stringified JSON or plain string
        if (typeof predictionString === 'string' && predictionString.startsWith('{')) {
            prediction = JSON.parse(predictionString);
        } else if (typeof predictionString === 'object') {
            prediction = predictionString;
        } else {
            // Fake probabilities if it's just a raw string label
            prediction = { [predictionString]: 0.92, "Other": 0.08 };
        }
    } catch(e) {
        console.error("Chart parsing error", e);
        return;
    }

    const labels = Object.keys(prediction);
    // Convert strings to floats and handle probabilities (e.g., 0.85 -> 85)
    const dataValues = Object.values(prediction).map(v => typeof v === 'number' ? (v <= 1 ? v * 100 : v) : parseFloat(v) * 100);

    document.getElementById("chartFallback").style.display = "none";
    const ctx = document.getElementById("aiChart");
    ctx.style.display = "block";

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: dataValues,
                backgroundColor: [
                    '#38BDF8', // accent blue
                    '#818CF8', // accent purple
                    '#10B981', // green
                    '#F59E0B'  // orange
                ],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#F8FAFC', font: { family: 'Outfit' } }
                }
            }
        }
    });
}
