import type { Note } from "../protocol";

export function NotesList({ notes }: { notes: Note[] }) {
  if (notes.length === 0) {
    return <p className="empty">No notes yet. Send a sample to create one.</p>;
  }
  return (
    <ul className="card-list">
      {notes.map((note) => (
        <li key={note.id} className="card">
          <p className="card-body">{note.text}</p>
          <time className="card-meta">{new Date(note.created_at).toLocaleString()}</time>
        </li>
      ))}
    </ul>
  );
}
