const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function parseResponse(response) {
  if (response.ok) {
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      return response.json();
    }
    return response;
  }

  let message = `HTTP ${response.status}`;
  try {
    const body = await response.json();
    message = body.detail || message;
  } catch {
    // Keep default message.
  }

  throw new ApiError(message, response.status);
}

function createClient(token = "") {
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  return {
    withToken(nextToken) {
      return createClient(nextToken);
    },
    async get(path) {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: authHeaders,
      });
      return parseResponse(response);
    },
    async post(path, payload) {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });
      return parseResponse(response);
    },
    async upload(path, formData) {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: authHeaders,
        body: formData,
      });
      return parseResponse(response);
    },
    async download(path, fileName) {
      const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: authHeaders,
      });
      if (!response.ok) {
        await parseResponse(response);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    },
  };
}

export const api = createClient();
