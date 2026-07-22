import type { Task } from "../protocol";

export function TasksList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return <p className="empty">No tasks yet. Send a sample to create one.</p>;
  }
  return (
    <ul className="card-list">
      {tasks.map((task) => (
        <li key={task.id} className="card">
          <span className={`badge badge-${task.priority}`}>{task.priority}</span>
          <p className="card-body">{task.title}</p>
          <time className="card-meta">{new Date(task.created_at).toLocaleString()}</time>
        </li>
      ))}
    </ul>
  );
}
