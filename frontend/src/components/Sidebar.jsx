import { NavLink, useNavigate } from 'react-router-dom'

export default function Sidebar({ projects = [] }) {
  const navigate = useNavigate()

  return (
    <aside className="sidebar">
      <div className="sidebar-section">
        <p className="sidebar-title">Navigation</p>
        <NavLink to="/" className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')} end>
          Dashboard
        </NavLink>
      </div>

      {projects.length > 0 && (
        <div className="sidebar-section">
          <p className="sidebar-title">My Projects</p>
          {projects.map((p) => (
            <NavLink
              key={p.id}
              to={`/projects/${p.id}`}
              className={({ isActive }) => 'sidebar-link' + (isActive ? ' active' : '')}
            >
              {p.name}
            </NavLink>
          ))}
        </div>
      )}
    </aside>
  )
}
