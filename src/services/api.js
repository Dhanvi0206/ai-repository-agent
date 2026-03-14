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
    const validationMessage = Array.isArray(detail)
      ? detail.map((item) => item?.msg).filter(Boolean).join(', ')
      : ''
    const message = detail?.message || detail?.error || validationMessage || payload?.message || 'Request failed'
    throw new Error(message)
  }

  return payload
}

export async function analyzeRepository(repoUrl) {
  const result = await request('/analyze-repository', {
    method: 'POST',
    body: JSON.stringify({
      repository_url: repoUrl,
    }),
  })

  if (result.status !== 'success') {
    throw new Error('Analysis failed')
  }

  return result.data
}

export async function getAnalysisStatus(jobId) {
  if (!jobId) {
    return null
  }
  return request(`/analysis-status/${encodeURIComponent(jobId)}`)
}

export async function getAgentStatus(jobId) {
  if (!jobId) {
    return null
  }
  return request(`/agent-status?job_id=${encodeURIComponent(jobId)}`)
}

export async function getDashboardData(repositoryId) {
  return request(`/dashboard-data?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function getRepositoryReport(repositoryId) {
  return request(`/repository-report?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function getRepositoryHealth(repositoryId) {
  return request(`/repo-health/${encodeURIComponent(repositoryId)}`)
}

export async function getRepositorySummary(repositoryId) {
  return request(`/repository-summary?repository_id=${encodeURIComponent(repositoryId)}`)
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

export async function getRiskHeatmap(repositoryId) {
  return request(`/risk-heatmap?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function getPriorityFixes(repositoryId) {
  return request(`/priority-fixes?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function getScoreExplanation(repositoryId) {
  return request(`/score-explanation?repository_id=${encodeURIComponent(repositoryId)}`)
}

export async function getRiskPredictions(repositoryId) {
  return request(`/risk-predictions?repository_id=${encodeURIComponent(repositoryId)}`)
}
