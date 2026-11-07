//const API_BASE_URL = "http://127.0.0.1:8000/api/v1";
const API_BASE_URL = "/api/v1";
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("access_token");

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        ...(options.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // FastAPI puede devolver detail como string o como array de errores de validación
      let message;
      if (typeof errorData.detail === "string") {
        message = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        // Pydantic validation errors: array de objetos {loc, msg, type}
        message = errorData.detail.map(e => `${e.loc?.join(" → ")}: ${e.msg}`).join(" | ");
      } else {
        message = `Error ${response.status}: ${response.statusText}`;
      }

      throw new Error(message);
    }

    if (response.status === 204) return null;

    return await response.json();

  } catch (error) {
    console.error("API error:", error);
    throw error;
  }
}

async function getData(endpoint) {
  return apiRequest(endpoint);
}

async function postData(endpoint, data) {
  return apiRequest(endpoint, {
    method: "POST",
    body: JSON.stringify(data)
  });
}

async function patchData(endpoint, data) {
  return apiRequest(endpoint, {
    method: "PATCH",
    body: JSON.stringify(data)
  });
}

async function deleteData(endpoint) {
  return apiRequest(endpoint, { method: "DELETE" });
}