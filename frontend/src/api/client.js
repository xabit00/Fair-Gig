const STORAGE_KEY = "fairgig.session";
const SESSION_EVENT = "fairgig:session";

export const serviceUrls = {
  auth: import.meta.env.VITE_AUTH_API_URL || "http://localhost:8001",
  earnings: import.meta.env.VITE_EARNINGS_API_URL || "http://localhost:8002",
  anomaly: import.meta.env.VITE_ANOMALY_API_URL || "http://localhost:8003",
  grievance: import.meta.env.VITE_GRIEVANCE_API_URL || "http://localhost:8004",
  analytics: import.meta.env.VITE_ANALYTICS_API_URL || "http://localhost:8005",
  certificate: import.meta.env.VITE_CERTIFICATE_API_URL || "http://localhost:8006",
};

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export function getStoredSession() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || null;
  } catch (_error) {
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function storeSession(session) {
  if (session) localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  else localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new CustomEvent(SESSION_EVENT, { detail: session }));
}

export function subscribeToSession(callback) {
  const listener = (event) => callback(event.detail);
  window.addEventListener(SESSION_EVENT, listener);
  return () => window.removeEventListener(SESSION_EVENT, listener);
}

async function parseBody(response) {
  if (response.status === 204) return null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json().catch(() => null);
  }
  return response.text().catch(() => "");
}

function errorMessage(response, data, path) {
  if (response.status === 401 && path === "/login") return "Incorrect email or password.";
  if (response.status === 401) return "Your session has expired. Please log in again.";
  if (response.status === 403) return "You do not have permission to do that.";
  if (response.status === 422) return typeof data?.detail === "string" ? data.detail : "Please check the highlighted information.";
  if (response.status === 409) return data?.detail || "This record already exists.";
  return data?.detail || "Something went wrong. Please try again.";
}

async function send(service, path, options, accessToken) {
  const headers = new Headers(options.headers);
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  if (options.body != null && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let response;
  try {
    response = await fetch(`${serviceUrls[service]}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body == null || options.body instanceof FormData
        ? options.body
        : JSON.stringify(options.body),
      signal: options.signal,
    });
  } catch (_error) {
    throw new ApiError("Could not reach the server. Please try again.");
  }
  const data = options.responseType === "blob" ? await response.blob() : await parseBody(response);
  return { response, data };
}

let refreshPromise = null;

export async function refreshSession() {
  if (refreshPromise) return refreshPromise;
  const session = getStoredSession();
  if (!session?.refresh_token) {
    storeSession(null);
    throw new ApiError("Your session has expired. Please log in again.", 401);
  }

  refreshPromise = send("auth", "/refresh", {
    method: "POST",
    body: { refresh_token: session.refresh_token },
  }).then(({ response, data }) => {
    if (!response.ok) {
      storeSession(null);
      throw new ApiError("Your session has expired. Please log in again.", 401, data);
    }
    storeSession(data);
    return data;
  }).finally(() => {
    refreshPromise = null;
  });

  return refreshPromise;
}

export async function apiRequest(service, path, options = {}) {
  const { auth = true, retry = true, ...requestOptions } = options;
  const session = getStoredSession();
  const { response, data } = await send(
    service,
    path,
    requestOptions,
    auth ? session?.access_token : null,
  );

  if (response.status === 401 && auth && retry) {
    const renewed = await refreshSession();
    const repeated = await send(service, path, requestOptions, renewed.access_token);
    if (repeated.response.ok) return repeated.data;
    if (repeated.response.status === 401) storeSession(null);
    throw new ApiError(
      errorMessage(repeated.response, repeated.data, path),
      repeated.response.status,
      repeated.data,
    );
  }

  if (!response.ok) {
    throw new ApiError(errorMessage(response, data, path), response.status, data);
  }
  return data;
}

export const api = {
  get: (service, path, options) => apiRequest(service, path, { ...options, method: "GET" }),
  post: (service, path, body, options) => apiRequest(service, path, { ...options, method: "POST", body }),
  patch: (service, path, body, options) => apiRequest(service, path, { ...options, method: "PATCH", body }),
  put: (service, path, body, options) => apiRequest(service, path, { ...options, method: "PUT", body }),
  delete: (service, path, options) => apiRequest(service, path, { ...options, method: "DELETE" }),
  download: (service, path, options) => apiRequest(service, path, { ...options, method: "GET", responseType: "blob" }),
};
