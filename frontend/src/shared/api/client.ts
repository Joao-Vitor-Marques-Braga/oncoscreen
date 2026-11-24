import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  timeout: 185000,
});

apiClient.interceptors.request.use((config) => {
  const raw = localStorage.getItem("oncoscreen_auth");
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as { access_token?: string };
      if (parsed.access_token) {
        config.headers.Authorization = `Bearer ${parsed.access_token}`;
      }
    } catch {
      // Ignore malformed storage
    }
  }
  return config;
});

