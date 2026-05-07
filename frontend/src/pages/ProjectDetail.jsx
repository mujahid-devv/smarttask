import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProject, getMembers, archiveProject, unarchiveProject } from '../api/projects'
import { getTasks, createTask } from '../api/tasks'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import TaskCard from '../components/TaskCard'
import useProjects from '../hooks/useProjects'

const MEMBER_ROLE_CLASS = {
  OWNER: 'badge-high',
  EDITOR: 'badge-medium',
  VIEWER: 'badge-low',
}

export default function ProjectDetail() {
  const { projectId } = useParams()
  const { projects } = useProjects()

  const [project, setProject] = useState(null)
  const [members, setMembers] = useState([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [showTaskForm, setShowTaskForm] = useState(false)
  const [taskForm, setTaskForm] = useState({
    title: '',
    description: '',
    status: 'TODO',
    priority: 'MEDIUM',
    due_date: '',
  })
  const [creating, setCreating] = useState(false)
  const [taskError, setTaskError] = useState(null)
  const [archiving, setArchiving] = useState(false)

  useEffect(() => {
    Promise.all([
      getProject(projectId),
      getMembers(projectId),
      getTasks(projectId),
    ])
      .then(([projRes, membersRes, tasksRes]) => {
        setProject(projRes.data)
        setMembers(membersRes.data)
        setTasks(tasksRes.data)
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to load project')
      })
      .finally(() => setLoading(false))
  }, [projectId])

  const handleTaskChange = (e) =>
    setTaskForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleCreateTask = async (e) => {
    e.preventDefault()
    setCreating(true)
    setTaskError(null)
    try {
      const payload = { ...taskForm }
      if (!payload.due_date) delete payload.due_date
      const res = await createTask(projectId, payload)
      setTasks((prev) => [res.data, ...prev])
      setTaskForm({ title: '', description: '', status: 'TODO', priority: 'MEDIUM', due_date: '' })
      setShowTaskForm(false)
    } catch (err) {
      setTaskError(err.response?.data?.detail || 'Failed to create task')
    } finally {
      setCreating(false)
    }
  }

  const handleArchiveToggle = async () => {
    setArchiving(true)
    try {
      const fn = project.status === 'ARCHIVED' ? unarchiveProject : archiveProject
      const res = await fn(projectId)
      setProject(res.data)
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed')
    } finally {
      setArchiving(false)
    }
  }

  if (loading) return <><Navbar /><p className="loading-text">Loading...</p></>
  if (error) return <><Navbar /><div className="error-msg page-error">{error}</div></>

  return (
    <>
      <Navbar />
      <div className="app-layout">
        <Sidebar projects={projects} />
        <main className="page-content">
          {/* Project Header */}
          <div className="page-header">
            <div className="breadcrumb">
              <Link to="/">Dashboard</Link> / {project.name}
            </div>
            <div className="page-header-row">
              <div>
                <h1>{project.name}</h1>
                {project.description && <p>{project.description}</p>}
              </div>
              <div className="header-actions">
                {project.tags?.map((tag, i) => (
                  <span key={i} className="tag">{tag}</span>
                ))}
                <span className={`badge badge-${project.status.toLowerCase()}`}>
                  {project.status}
                </span>
                <button
                  className="btn btn-sm btn-secondary"
                  onClick={handleArchiveToggle}
                  disabled={archiving}
                >
                  {project.status === 'ARCHIVED' ? 'Unarchive' : 'Archive'}
                </button>
              </div>
            </div>
          </div>

          <div className="detail-layout">
            {/* Members Panel */}
            <section className="card members-panel">
              <h2 className="card-title">Members ({members.length})</h2>
              {members.map((m) => (
                <div key={m.user_id} className="member-item">
                  <div className="member-avatar">
                    {m.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div className="member-info">
                    <p className="member-name">{m.full_name}</p>
                    <p className="member-email">{m.email}</p>
                  </div>
                  <span className={`badge ${MEMBER_ROLE_CLASS[m.role]}`}>
                    {m.role}
                  </span>
                </div>
              ))}
            </section>

            {/* Tasks Panel */}
            <section className="tasks-panel">
              <div className="section-header">
                <h2 className="section-title">Tasks ({tasks.length})</h2>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => setShowTaskForm((v) => !v)}
                >
                  {showTaskForm ? 'Cancel' : '+ Add Task'}
                </button>
              </div>

              {showTaskForm && (
                <div className="card form-card">
                  <h3 className="card-title">New Task</h3>
                  {taskError && <div className="error-msg">{taskError}</div>}
                  <form onSubmit={handleCreateTask}>
                    <div className="form-group">
                      <label htmlFor="task-title">Title</label>
                      <input
                        id="task-title"
                        type="text"
                        name="title"
                        value={taskForm.title}
                        onChange={handleTaskChange}
                        placeholder="Task title"
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="task-desc">Description (optional)</label>
                      <textarea
                        id="task-desc"
                        name="description"
                        value={taskForm.description}
                        onChange={handleTaskChange}
                        rows={2}
                        placeholder="Task description"
                      />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label htmlFor="task-status">Status</label>
                        <select
                          id="task-status"
                          name="status"
                          value={taskForm.status}
                          onChange={handleTaskChange}
                        >
                          <option value="TODO">TODO</option>
                          <option value="IN_PROGRESS">IN PROGRESS</option>
                          <option value="DONE">DONE</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label htmlFor="task-priority">Priority</label>
                        <select
                          id="task-priority"
                          name="priority"
                          value={taskForm.priority}
                          onChange={handleTaskChange}
                        >
                          <option value="LOW">LOW</option>
                          <option value="MEDIUM">MEDIUM</option>
                          <option value="HIGH">HIGH</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label htmlFor="task-due">Due Date (optional)</label>
                        <input
                          id="task-due"
                          type="datetime-local"
                          name="due_date"
                          value={taskForm.due_date}
                          onChange={handleTaskChange}
                        />
                      </div>
                    </div>
                    <button className="btn btn-primary" type="submit" disabled={creating}>
                      {creating ? 'Creating...' : 'Create Task'}
                    </button>
                  </form>
                </div>
              )}

              {tasks.length === 0 && (
                <div className="empty-card">
                  <p>No tasks yet. Add the first task above!</p>
                </div>
              )}

              {tasks.map((task) => (
                <TaskCard key={task.id} task={task} projectId={projectId} />
              ))}
            </section>
          </div>
        </main>
      </div>
    </>
  )
}
