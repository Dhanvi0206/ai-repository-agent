const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  const payload = await response.json().catch(() => ({}))

  if (!response.ok) {
    const detail = payload?.detail || payload
    const message = detail?.message || detail?.error || payload?.message || 'Request failed'
    throw new Error(message)
  }

  return payload
}

export async function analyzeRepository(repoUrl) {
  return request('/analyze-repository', {
    method: 'POST',
    body: JSON.stringify({
      repo_url: repoUrl,
    }),
  })
}

export async function getAnalysisStatus(jobId) {
  return request(`/analysis-status/${encodeURIComponent(jobId)}`)
}

export async function getAgentStatus(jobId) {
  return request(`/agent-status?job_id=${encodeURIComponent(jobId)}`)
}

export async function getDashboardData(repositoryId) {
  return request(`/dashboard-data?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function getRepositoryHealth(repositoryId) {
  return request(`/repo-health/${encodeURIComponent(repositoryId)}`)
}

export async function getDeveloperScore(repositoryId) {
  return request(`/developer-score/${encodeURIComponent(repositoryId)}`)
}

export async function getDependencyRisk(repositoryId) {
  return request(`/dependency-risk/${encodeURIComponent(repositoryId)}`)
}

export async function getTechnicalDebt(repositoryId) {
  return request(`/technical-debt?repository_id=${encodeURIComponent(repositoryId)}`)
}
