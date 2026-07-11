// =====================================================
// signup.js — Full Signup Integration (Fixed)
// =====================================================

async function signupUser(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const fullName = document.getElementById("full_name").value.trim();
    const roleInput = document.querySelector('input[name="role"]:checked');
    const errEl = document.getElementById("signupError");
    const successEl = document.getElementById("signupSuccess");
    const btn = document.getElementById("signupBtn");

    errEl.style.display = "none";
    successEl.style.display = "none";

    if (!username || !password || !fullName || !roleInput) {
        errEl.textContent = "Please fill in all fields and select a role.";
        errEl.style.display = "block";
        return;
    }

    if (password.length < 6) {
        errEl.textContent = "Password must be at least 6 characters.";
        errEl.style.display = "block";
        return;
    }

    const role = roleInput.value;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Creating account...';

    const payload = {
        username,
        password,
        full_name: fullName,
        role
    };

    try {
        const res = await fetch(`${API_BASE}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        console.log("Signup Response:", data);

        if (res.ok && (data.id || data.username)) {
            successEl.textContent = "✅ Account created! Redirecting to login...";
            successEl.style.display = "block";
            setTimeout(() => { window.location.href = "login.html"; }, 1500);
        } else {
            const msg = data.detail || JSON.stringify(data);
            errEl.textContent = "Registration failed: " + msg;
            errEl.style.display = "block";
            btn.disabled = false;
            btn.innerHTML = "Create My Account";
        }

    } catch (err) {
        console.error(err);
        errEl.textContent = "Signup failed — backend may be offline. Please try again.";
        errEl.style.display = "block";
        btn.disabled = false;
        btn.innerHTML = "Create My Account";
    }
}
