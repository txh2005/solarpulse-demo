import axios from "axios";

const resolveApiBaseUrl = () => {
  const envBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

  if (envBaseUrl) {
    return envBaseUrl.replace(/\/+$/, "");
  }

  return import.meta.env.DEV ? "http://127.0.0.1:8000/api" : "/api";
};

const client = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 8000,
  headers: { "Content-Type": "application/json" },
});

export const fetchMetrics = () => client.get("/metrics/").then((response) => response.data);
export const fetchPowerCurve = () => client.get("/power-curve/").then((response) => response.data);
export const fetchAnomalies = () => client.get("/anomalies/").then((response) => response.data);
export const fetchAiAdvice = () => client.get("/ai-advice/").then((response) => response.data);
export const fetchSubArrays = () => client.get("/sub-arrays/").then((response) => response.data);
export const sendAssistantMessage = (message, history = []) =>
  client.post("/assistant/", { message, history }, { timeout: 60000 }).then((response) => response.data);
