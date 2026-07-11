// =====================================================
// signup.js — Full Signup Integration
// =====================================================

const API = "http://localhost:8000";

// -------------------------------
// 🔹 Signup Function
// -------------------------------
async function signupUser(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const fullName = document.getElementById("full_name").value.trim();
    const role = document.getElementById("role").value;

    if (!username || !password || !fullName || !role) {
        alert("Please fill all fields.");
        return;
    }

    const payload = {
        username: username,
        password: password,
        full_name: fullName,
        role: role
    };

    try {
        const res = await fetch(`${API}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        console.log("Signup Response:", data);

        if (data.id || data.username || data.message) {
            alert("Account created successfully! Please log in.");
            window.location.href = "login.html";
        } else {
            alert("Unable to create account: " + JSON.stringify(data));
        }

    } catch (err) {
        console.error(err);
        alert("Signup failed — backend may be offline.");
    }
}
