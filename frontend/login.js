// =====================================================
// login.js — Full Authentication Logic
// =====================================================

async function loginUser(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const role = document.getElementById("role").value;
    const errEl = document.getElementById("loginError");
    const errText = document.getElementById("loginErrorText");
    const successEl = document.getElementById("loginSuccess");
    const successText = document.getElementById("loginSuccessText");
    const btn = document.getElementById("loginBtn");

    errEl.style.display = "none";
    successEl.style.display = "none";

    if (!username || !password) {
        if (errText) errText.textContent = "Please enter your username and password.";
        else errEl.textContent = "Please enter your username and password.";
        errEl.style.display = "flex";
        return;
    }
    if (!role) {
        if (errText) errText.textContent = "Please select your role above.";
        else errEl.textContent = "Please select your role above.";
        errEl.style.display = "flex";
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Signing in...';

    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    function onWaiting(attempt, total) {
        btn.innerHTML = `<span class="spinner"></span> Server waking up... (${attempt}/${total})`;
        if (successText) successText.textContent = "Server is starting up, please wait a moment...";
        else successEl.textContent = "Server is starting up, please wait a moment...";
        successEl.style.display = "flex";
        errEl.style.display = "none";
    }

    try {
        const res = await fetchWithRetry(
            `${API_BASE}/auth/login`,
            { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body },
            3, 8000, onWaiting
        );

        successEl.style.display = "none";
        const data = await res.json();

        if (data.access_token) {
            let actualRole = null;
            try {
                const meRes = await fetch(`${API_BASE}/auth/me`, {
                    headers: { "Authorization": `Bearer ${data.access_token}` }
                });
                const meData = await meRes.json();
                actualRole = meData.role;
            } catch (e) {
                actualRole = role;
            }

            if (actualRole && actualRole !== role) {
                const msg = `You registered as "${actualRole}" but selected "${role}". Please select the correct role tab.`;
                if (errText) errText.textContent = msg; else errEl.textContent = msg;
                errEl.style.display = "flex";
                btn.disabled = false;
                btn.innerHTML = "Sign In to Dashboard →";
                return;
            }

            localStorage.setItem("token", data.access_token);
            localStorage.setItem("role", actualRole || role);
            localStorage.setItem("username", username);

            const msg = "Login successful! Redirecting to your dashboard...";
            if (successText) successText.textContent = msg; else successEl.textContent = msg;
            successEl.style.display = "flex";

            setTimeout(() => {
                const r = actualRole || role;
                if (r === "doctor") window.location.href = "doctor_dashboard.html";
                else if (r === "lab") window.location.href = "lab_dashboard.html";
                else window.location.href = "patient_dashboard.html";
            }, 800);

        } else {
            const msg = data.detail || "Invalid username or password.";
            if (errText) errText.textContent = msg; else errEl.textContent = msg;
            errEl.style.display = "flex";
            btn.disabled = false;
            btn.innerHTML = "Sign In to Dashboard →";
        }

    } catch (err) {
        console.error(err);
        const msg = "Unable to connect to the server. Please try again in a moment.";
        if (errText) errText.textContent = msg; else errEl.textContent = msg;
        errEl.style.display = "flex";
        successEl.style.display = "none";
        btn.disabled = false;
        btn.innerHTML = "Sign In to Dashboard →";
    }
}
