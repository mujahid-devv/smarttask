import { useState } from 'react'
import { Link } from 'react-router-dom'
import { createProject } from '../api/projects'
import Navbar from '../components/Navbar'
import Sidebar from '../components/Sidebar'
import useProjects from '../hooks/useProjects'

const STATUS_CLASS = {
  ACTIVE: 'badge-active',
  COMPLETED: 'badge-completed',
  ARCHIVED: 'badge-archived',
}

export default function Dashboard() {
  const { projects, loading, error, refetch } = useProjects()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [formError, setFormError] = useState(null)

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    setFormError(null)
    try {
      await createProject(form)
      setForm({ name: '', description: '' })
      setShowForm(false)
      refetch()
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create project')
    } finally {
      setCreating(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="app-layout">
        <Sidebar projects={projects} />
        <main className="page-content">
          <div className="page-header">
            <div className="page-header-row">
              <div>
                <h1>Dashboard</h1>
                <p>Your projects at a glance</p>
              </div>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => setShowForm((v) => !v)}
              >
                {showForm ? 'Cancel' : '+ New Project'}
              </button>
            </div>
          </div>

          {showForm && (
            <div className="card form-card">
              <h3 className="card-title">Create Project</h3>
              {formError && <div className="error-msg">{formError}</div>}
              <form onSubmit={handleCreate}>
                <div className="form-group">
                  <label htmlFor="proj-name">Project Name</label>
                  <input
                    id="proj-name"
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="My new project"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="proj-desc">Description (optional)</label>
                  <textarea
                    id="proj-desc"
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="What is this project about?"
                    rows={3}
                  />
                </div>
                <button className="btn btn-primary" type="submit" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Project'}
                </button>
              </form>
            </div>
          )}

          {loading && <p className="loading-text">Loading projects...</p>}
          {error && <div className="error-msg">{error}</div>}

          {!loading && projects.length === 0 && (
            <div className="empty-card">
              <p>No projects yet. Create your first project above!</p>
            </div>
          )}

          <div className="projects-grid">
            {projects.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className="project-card"
              >
                <div className="project-card-header">
                  <h3>{project.name}</h3>
                  <span className={`badge ${STATUS_CLASS[project.status]}`}>
                    {project.status}
                  </span>
                </div>
                {project.description && (
                  <p className="project-desc">{project.description}</p>
                )}
                {project.tags?.length > 0 && (
                  <div className="tag-list">
                    {project.tags.map((tag, i) => (
                      <span key={i} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
                <p className="project-date">
                  Created: {new Date(project.created_at).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        </main>
      </div>
    </>
  )
}
