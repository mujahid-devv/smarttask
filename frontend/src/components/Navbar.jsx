import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="navbar-brand">
        Smart<span>Task</span>
      </Link>
      {user && (
        <div className="navbar-user">
          <span className="navbar-username">
            {user.full_name} &mdash; <em>{user.role}</em>
          </span>
          <button className="btn btn-sm btn-outline" onClick={handleLogout}>
            Logout
          </button>
        </div>
      )}
    </nav>
  )
}
