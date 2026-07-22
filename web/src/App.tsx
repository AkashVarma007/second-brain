import { useCallback, useEffect, useState } from "react";
import { getHealth, getNotes, getTasks, processSample } from "./api";
import { NotesList } from "./components/NotesList";
import { TasksList } from "./components/TasksList";
import type { Mode, Note, Task } from "./protocol";
import "./App.css";

export default function App() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [busy, setBusy] = useState<Mode | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      await getHealth();
      setOnline(true);
      const [nextNotes, nextTasks] = await Promise.all([getNotes(), getTasks()]);
      setNotes(nextNotes);
      setTasks(nextTasks);
      setError(null);
    } catch (err) {
      setOnline(false);
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function sendSample(mode: Mode) {
    setBusy(mode);
    setError(null);
    try {
      await processSample(mode);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <main className="page">
      <header className="page-header">
        <h1>Second Brain</h1>
        <span className={`status status-${online === null ? "unknown" : online ? "up" : "down"}`}>
          {online === null ? "checking…" : online ? "brain online" : "brain offline"}
        </span>
      </header>

      <section className="actions">
        <button onClick={() => void sendSample("note")} disabled={busy !== null}>
          {busy === "note" ? "Processing…" : "Send sample as note"}
        </button>
        <button onClick={() => void sendSample("task")} disabled={busy !== null}>
          {busy === "task" ? "Processing…" : "Send sample as task"}
        </button>
        <button onClick={() => void refresh()} disabled={busy !== null}>
          Refresh
        </button>
      </section>

      {error && <p className="error">{error}</p>}

      <div className="columns">
        <section>
          <h2>Notes ({notes.length})</h2>
          <NotesList notes={notes} />
        </section>
        <section>
          <h2>Tasks ({tasks.length})</h2>
          <TasksList tasks={tasks} />
        </section>
      </div>
    </main>
  );
}
