// =====================================================
// login.js — Full Authentication Logic
// =====================================================

const API = "http://localhost:8000";

// -------------------------------
// 🔹 Login function
// -------------------------------
async function loginUser(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const role = document.getElementById("role").value;

    if (!username || !password || !role) {
        alert("Please fill all fields including role.");
        return;
    }

    // Create x-www-form-urlencoded body as backend expects
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    try {
        const res = await fetch(`${API}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded"
            },
            body
        });

        const data = await res.json();
        console.log("Login Response:", data);

        if (data.access_token) {
            // Save JWT token
            localStorage.setItem("token", data.access_token);

            // Save role for routing
            localStorage.setItem("role", role);

            // Redirect based on role
            if (role === "patient") {
                window.location.href = "patient_dashboard.html";
            } else if (role === "doctor") {
                window.location.href = "doctor_dashboard.html";
            } else if (role === "lab") {
                window.location.href = "lab_dashboard.html";
            }

        } else {
            alert("Invalid login credentials.");
        }

    } catch (err) {
        console.error(err);
        alert("Unable to login. Backend may be offline.");
    }
}
