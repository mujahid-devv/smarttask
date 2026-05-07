import { useState, useEffect } from 'react'
import { getProjects } from '../api/projects'

export default function useProjects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchProjects = () => {
    setLoading(true)
    getProjects()
      .then((res) => setProjects(res.data))
      .catch((err) => {
        // 404 just means no projects yet — not a real error
        if (err.response?.status === 404) {
          setProjects([])
        } else {
          setError(err.response?.data?.detail || 'Failed to load projects')
        }
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  return { projects, loading, error, setProjects, refetch: fetchProjects }
}
