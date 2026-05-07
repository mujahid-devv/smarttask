import { Link } from 'react-router-dom'

const STATUS_CLASS = {
  TODO: 'badge-todo',
  IN_PROGRESS: 'badge-in-progress',
  DONE: 'badge-done',
}

const PRIORITY_CLASS = {
  LOW: 'badge-low',
  MEDIUM: 'badge-medium',
  HIGH: 'badge-high',
}

export default function TaskCard({ task, projectId }) {
  return (
    <div className="task-card">
      <div className="task-card-header">
        <Link to={`/projects/${projectId}/tasks/${task.id}`} className="task-title">
          {task.title}
        </Link>
        {task.due_date && (
          <span className="task-due">
            Due: {new Date(task.due_date).toLocaleDateString()}
          </span>
        )}
      </div>
      {task.description && (
        <p className="task-description">{task.description}</p>
      )}
      <div className="task-meta">
        <span className={`badge ${STATUS_CLASS[task.status]}`}>{task.status.replace('_', ' ')}</span>
        <span className={`badge ${PRIORITY_CLASS[task.priority]}`}>{task.priority}</span>
      </div>
    </div>
  )
}
