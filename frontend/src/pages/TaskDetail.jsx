import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getTask, updateTask } from '../api/tasks'
import { getTaskComments } from '../api/comments'
import Navbar from '../components/Navbar'
import CommentBox from '../components/CommentBox'

const STATUS_OPTIONS = ['TODO', 'IN_PROGRESS', 'DONE']
const PRIORITY_OPTIONS = ['LOW', 'MEDIUM', 'HIGH']

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

export default function TaskDetail() {
  const { projectId, taskId } = useParams()

  const [task, setTask] = useState(null)
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [editError, setEditError] = useState(null)

  useEffect(() => {
    Promise.all([
      getTask(projectId, taskId),
      getTaskComments(projectId, taskId),
    ])
      .then(([taskRes, commentsRes]) => {
        setTask(taskRes.data)
        setEditForm({
          title: taskRes.data.title,
          description: taskRes.data.description || '',
          status: taskRes.data.status,
          priority: taskRes.data.priority,
          due_date: taskRes.data.due_date
            ? taskRes.data.due_date.slice(0, 16)
            : '',
        })
        setComments(commentsRes.data)
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to load task')
      })
      .finally(() => setLoading(false))
  }, [projectId, taskId])

  const handleEditChange = (e) =>
    setEditForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setEditError(null)
    try {
      const payload = { ...editForm }
      if (!payload.due_date) delete payload.due_date
      if (!payload.description) delete payload.description
      const res = await updateTask(projectId, taskId, payload)
      setTask(res.data)
      setEditing(false)
    } catch (err) {
      setEditError(err.response?.data?.detail || 'Failed to update task')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <><Navbar /><p className="loading-text">Loading...</p></>
  if (error) return <><Navbar /><div className="error-msg page-error">{error}</div></>

  return (
    <>
      <Navbar />
      <main className="page-content page-content-narrow">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/">Dashboard</Link> /{' '}
          <Link to={`/projects/${projectId}`}>Project</Link> / {task.title}
        </div>

        {/* Task Info */}
        <div className="card task-detail-card">
          {!editing ? (
            <>
              <div className="task-detail-header">
                <h1>{task.title}</h1>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => setEditing(true)}
                >
                  Edit
                </button>
              </div>
              {task.description && <p className="task-full-desc">{task.description}</p>}
              <div className="task-meta">
                <span className={`badge ${STATUS_CLASS[task.status]}`}>
                  {task.status.replace('_', ' ')}
                </span>
                <span className={`badge ${PRIORITY_CLASS[task.priority]}`}>
                  {task.priority}
                </span>
                {task.due_date && (
                  <span className="task-due">
                    Due: {new Date(task.due_date).toLocaleString()}
                  </span>
                )}
              </div>
              <p className="task-meta-small">
                Created: {new Date(task.created_at).toLocaleDateString()}
              </p>
            </>
          ) : (
            <form onSubmit={handleSave}>
              <h3 className="card-title">Edit Task</h3>
              {editError && <div className="error-msg">{editError}</div>}
              <div className="form-group">
                <label htmlFor="edit-title">Title</label>
                <input
                  id="edit-title"
                  type="text"
                  name="title"
                  value={editForm.title}
                  onChange={handleEditChange}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="edit-desc">Description</label>
                <textarea
                  id="edit-desc"
                  name="description"
                  value={editForm.description}
                  onChange={handleEditChange}
                  rows={3}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="edit-status">Status</label>
                  <select
                    id="edit-status"
                    name="status"
                    value={editForm.status}
                    onChange={handleEditChange}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s.replace('_', ' ')}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="edit-priority">Priority</label>
                  <select
                    id="edit-priority"
                    name="priority"
                    value={editForm.priority}
                    onChange={handleEditChange}
                  >
                    {PRIORITY_OPTIONS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="edit-due">Due Date</label>
                  <input
                    id="edit-due"
                    type="datetime-local"
                    name="due_date"
                    value={editForm.due_date}
                    onChange={handleEditChange}
                  />
                </div>
              </div>
              <div className="form-actions">
                <button className="btn btn-primary btn-sm" type="submit" disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  className="btn btn-secondary btn-sm"
                  type="button"
                  onClick={() => setEditing(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Comments */}
        <CommentBox
          comments={comments}
          projectId={projectId}
          taskId={taskId}
          onCommentsChange={setComments}
        />
      </main>
    </>
  )
}
