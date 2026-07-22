// The Second Brain HTTP contract, mirrored in TypeScript.
// Must stay in sync with brain/app/models.py.

export type Mode = "note" | "task";
export type Priority = "high" | "medium" | "low";

export interface NoteResult {
  text: string;
}

export interface TaskResult {
  title: string;
  priority: Priority;
}

export interface ProcessResponse {
  transcript: string;
  result: NoteResult | TaskResult;
}

export interface Note {
  id: number;
  text: string;
  created_at: string;
}

export interface Task {
  id: number;
  title: string;
  priority: Priority;
  created_at: string;
}

export function isTaskResult(result: NoteResult | TaskResult): result is TaskResult {
  return "title" in result;
}
