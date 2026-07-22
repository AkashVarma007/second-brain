import type { Mode, Note, ProcessResponse, Task } from "./protocol";

const BASE_URL = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // response had no JSON body; keep the status-code message
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export const getHealth = () => request<{ status: string }>("/health");
export const getNotes = () => request<Note[]>("/notes");
export const getTasks = () => request<Task[]>("/tasks");

export const processSample = (mode: Mode) =>
  request<ProcessResponse>(`/process-sample?mode=${mode}`, { method: "POST" });
