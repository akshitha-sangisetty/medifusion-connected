// =====================================================
// login.js — Full Authentication Logic (Fixed)
// =====================================================

async function loginUser(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const role = document.getElementById("role").value;
    const errEl = document.getElementById("loginError");
    const successEl = document.getElementById("loginSuccess");
    const btn = document.getElementById("loginBtn");

    errEl.style.display = "none";
    successEl.style.display = "none";

    if (!username || !password || !role) {
        errEl.textContent = "Please fill in all fields including your role.";
        errEl.style.display = "block";
        return;
    }

    // Show loading state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Signing in...';

    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    try {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body
        });

        const data = await res.json();
        console.log("Login Response:", data);

        if (data.access_token) {
            // ── Verify the actual role from the backend ──
            let actualRole = null;
            try {
                const meRes = await fetch(`${API_BASE}/auth/me`, {
                    headers: { "Authorization": `Bearer ${data.access_token}` }
                });
                const meData = await meRes.json();
                actualRole = meData.role;
            } catch (e) {
                // If /auth/me fails, trust the role the user selected
                actualRole = role;
            }

            if (actualRole && actualRole !== role) {
                errEl.textContent = `You registered as "${actualRole}" but selected "${role}". Please select the correct role.`;
                errEl.style.display = "block";
                btn.disabled = false;
                btn.innerHTML = "Sign In to Dashboard";
                return;
            }

            // Save credentials
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", actualRole || role);
            localStorage.setItem("username", username);

            successEl.textContent = "✅ Login successful! Redirecting...";
            successEl.style.display = "block";

            // Redirect based on role
            setTimeout(() => {
                if (actualRole === "patient" || role === "patient") {
                    window.location.href = "patient_dashboard.html";
                } else if (actualRole === "doctor" || role === "doctor") {
                    window.location.href = "doctor_dashboard.html";
                } else if (actualRole === "lab" || role === "lab") {
                    window.location.href = "lab_dashboard.html";
                } else {
                    window.location.href = "patient_dashboard.html";
                }
            }, 800);

        } else {
            errEl.textContent = data.detail || "Invalid username or password. Please try again.";
            errEl.style.display = "block";
            btn.disabled = false;
            btn.innerHTML = "Sign In to Dashboard";
        }

    } catch (err) {
        console.error(err);
        errEl.textContent = "Unable to connect to the server. Please check your internet connection.";
        errEl.style.display = "block";
        btn.disabled = false;
        btn.innerHTML = "Sign In to Dashboard";
    }
}
