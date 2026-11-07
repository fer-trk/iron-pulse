/**
 * Authentication management for Iron Pulse
 * Based on backend endpoints in auth.py
 */

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", handleLogin);
    }
});

/**
 * Handles the login process using OAuth2PasswordRequestForm format
 */
async function handleLogin(event) {
    event.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const errorDiv = document.getElementById("login-error");

    if (!username || !password) {
        showLoginError("Please enter both username and password.");
        return;
    }

    // The backend uses OAuth2PasswordRequestForm, which requires form-data
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
            },
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Invalid credentials");
        }

        const data = await response.json();
        
        // Store the access token and type
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type);
        localStorage.setItem("username", username);

        // Redirect to dashboard on success
        window.location.href = "index.html";
    } catch (error) {
        console.error("Login error:", error);
        showLoginError(error.message);
    }
}

/**
 * Logs out the user by clearing local storage
 */
function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token_type");
    localStorage.removeItem("username");
    window.location.href = "login.html";
}

/**
 * Utility to display errors on the login page
 */
function showLoginError(message) {
    const errorDiv = document.getElementById("login-error");
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove("d-none");
    } else {
        alert(message);
    }
}