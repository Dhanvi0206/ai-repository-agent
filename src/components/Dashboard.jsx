import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  getAgentStatus,
  getAnalysisStatus,
  getDashboardData,
  getDependencyRisk,
  getDeveloperScore,
  getRepositoryHealth,
  getTechnicalDebt,
} from '../services/api'

const POLL_INTERVAL_MS = 2500

function MetricCard({ title, value, subtitle }) {
  return (
    <div
      className="rounded-2xl p-5"
      style={{
        background: 'rgba(15, 23, 42, 0.82)',
        border: '1px solid rgba(148, 163, 184, 0.15)',
      }}
    >
      <p className="text-sm text-slate-400 mb-2">{title}</p>
      <p className="text-3xl font-bold text-white mb-2">{value ?? '—'}</p>
      <p className="text-sm text-slate-500">{subtitle}</p>
    </div>
  )
}

function SectionCard({ title, children }) {
  return (
    <section
      className="rounded-3xl p-6"
      style={{
        background: 'rgba(15, 23, 42, 0.82)',
        border: '1px solid rgba(148, 163, 184, 0.15)',
      }}
    >
      <h2 className="text-xl font-semibold text-white mb-4">{title}</h2>
      {children}
    </section>
  )
}

function LoadingPanel({ repositoryId, agentStatus, analysisStatus }) {
  const agentMessages = agentStatus?.data?.agent_execution_status || []
  const stateLabel = analysisStatus?.data?.status || 'processing'

  return (
    <div
      className="rounded-3xl p-8"
      style={{
        background: 'rgba(15, 23, 42, 0.82)',
        border: '1px solid rgba(148, 163, 184, 0.15)',
      }}
    >
      <h2 className="text-3xl font-bold text-white mb-3">Running AI Agents...</h2>
      <p className="text-slate-300 mb-6">
        Repository <span className="font-mono text-sky-300">{repositoryId}</span> is being analyzed.
        Current state: <span className="text-emerald-300">{stateLabel}</span>
      </p>

      <div className="space-y-3">
        {(agentMessages.length ? agentMessages : [
          { agent: 'security_agent', message: 'Security Agent scanning...' },
          { agent: 'code_quality_agent', message: 'Code Quality Agent analyzing...' },
          { agent: 'dependency_agent', message: 'Dependency Agent checking packages...' },
        ]).map((entry, index) => (
          <div
            key={`${entry.agent}-${index}`}
            className="rounded-2xl px-4 py-3 flex items-center justify-between gap-4"
            style={{
              background: 'rgba(30, 41, 59, 0.65)',
              border: '1px solid rgba(148, 163, 184, 0.12)',
            }}
          >
            <span className="text-slate-200">
              {(entry.agent || 'agent').replaceAll('_', ' ')}
            </span>
            <span className="text-sm text-slate-400">{entry.message || 'Processing...'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { state } = useLocation()
  const navigate = useNavigate()
  const repoUrl = state?.repoUrl || ''
  const [repositoryId, setRepositoryId] = useState(state?.repositoryId || '')
  const [jobId] = useState(state?.jobId || null)
  const [analysisStatus, setAnalysisStatus] = useState(null)
  const [agentStatus, setAgentStatus] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [repoHealth, setRepoHealth] = useState(null)
  const [developerScore, setDeveloperScore] = useState(null)
  const [dependencyRisk, setDependencyRisk] = useState(null)
  const [technicalDebt, setTechnicalDebt] = useState(null)
  const [loading, setLoading] = useState(Boolean(jobId || repositoryId))
  const [error, setError] = useState('')

  useEffect(() => {
    if (!jobId && !repositoryId) {
      setError('No repository analysis found. Start a new analysis from the home page.')
      setLoading(false)
      return
    }

    let cancelled = false
    let timerId = null

    const loadCompletedData = async (targetRepositoryId) => {
      const [dashboard, health, developer, dependency, debt] = await Promise.all([
        getDashboardData(targetRepositoryId),
        getRepositoryHealth(targetRepositoryId),
        getDeveloperScore(targetRepositoryId),
        getDependencyRisk(targetRepositoryId),
        getTechnicalDebt(targetRepositoryId),
      ])

      if (cancelled) {
        return
      }

      setDashboardData(dashboard)
      setRepoHealth(health)
      setDeveloperScore(developer)
      setDependencyRisk(dependency)
      setTechnicalDebt(debt)
      setLoading(false)
    }

    const poll = async () => {
      try {
        if (jobId) {
          const [job, agents] = await Promise.all([
            getAnalysisStatus(jobId),
            getAgentStatus(jobId).catch(() => null),
          ])

          if (cancelled) {
            return
          }

          setAnalysisStatus(job)
          setAgentStatus(agents)

          const currentRepositoryId = job?.data?.repository || repositoryId
          if (currentRepositoryId && currentRepositoryId !== repositoryId) {
            setRepositoryId(currentRepositoryId)
          }

          if (job?.data?.status === 'completed' || job?.data?.status === 'cached') {
            await loadCompletedData(currentRepositoryId)
            return
          }

          if (job?.data?.status === 'failed') {
            throw new Error(job?.data?.error || 'Repository analysis failed.')
          }
        } else if (repositoryId) {
          await loadCompletedData(repositoryId)
          return
        }

        timerId = window.setTimeout(poll, POLL_INTERVAL_MS)
      } catch (requestError) {
        if (cancelled) {
          return
        }
        setError(requestError.message || 'Unable to load dashboard data.')
        setLoading(false)
      }
    }

    poll()

    return () => {
      cancelled = true
      if (timerId) {
        window.clearTimeout(timerId)
      }
    }
  }, [jobId, repositoryId])

  const dashboard = dashboardData?.data
  const health = repoHealth?.data
  const developer = developerScore?.data
  const dependency = dependencyRisk?.data
  const debt = technicalDebt?.data

  const topContributors = useMemo(
    () => dashboard?.developer_insights?.top_contributors || [],
    [dashboard],
  )

  const alerts = dashboard?.alerts || []

  if (loading) {
    return (
      <div className="min-h-screen px-6 py-10" style={{ background: '#0d1117' }}>
        <div className="max-w-6xl mx-auto">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-slate-400 hover:text-white mb-6"
          >
            ← Back to analysis form
          </button>
          <LoadingPanel repositoryId={repositoryId || 'pending'} agentStatus={agentStatus} analysisStatus={analysisStatus} />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen px-6 py-10" style={{ background: '#0d1117' }}>
        <div className="max-w-4xl mx-auto">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-slate-400 hover:text-white mb-6"
          >
            ← Back to analysis form
          </button>
          <div
            className="rounded-3xl p-8"
            style={{
              background: 'rgba(15, 23, 42, 0.82)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
            }}
          >
            <h2 className="text-2xl font-bold text-white mb-3">Unable to load dashboard</h2>
            <p className="text-rose-300">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen px-6 py-10" style={{ background: '#0d1117' }}>
      <div className="max-w-7xl mx-auto space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-3"
        >
          <button
            type="button"
            onClick={() => navigate('/')}
            className="text-slate-400 hover:text-white w-fit"
          >
            ← Analyze another repository
          </button>
          <p className="text-sm uppercase tracking-[0.28em] text-sky-300">Live Dashboard</p>
          <h1 className="text-4xl md:text-5xl font-black text-white">{repositoryId}</h1>
          <p className="text-slate-400 max-w-3xl">
            Repository URL: <span className="font-mono">{repoUrl || repositoryId}</span>
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-4">
          <MetricCard title="Repository Health Score" value={health?.health_score} subtitle="Overall repository health from the scoring engine." />
          <MetricCard title="Security Score" value={health?.security_score} subtitle="Driven by detected vulnerabilities and confirmed risk." />
          <MetricCard title="Code Quality Score" value={health?.quality_score} subtitle="Maintainability and code smell impact." />
          <MetricCard title="Technical Debt Score" value={debt?.technical_debt_score} subtitle="Current maintainability risk across the codebase." />
        </div>

        <div className="grid xl:grid-cols-3 gap-6">
          <SectionCard title="Repository Overview">
            <div className="space-y-3 text-slate-300">
              <p><span className="text-slate-500">Primary language:</span> {dashboard?.repository_overview?.primary_language || 'Unknown'}</p>
              <p><span className="text-slate-500">Repository type:</span> {dashboard?.repository_overview?.repository_type || 'Unknown'}</p>
              <p><span className="text-slate-500">Tracked issues:</span> {dashboard?.repository_overview?.total_files ?? '—'}</p>
              <p><span className="text-slate-500">Analysis status:</span> Completed</p>
            </div>
          </SectionCard>

          <SectionCard title="Security Analysis">
            <div className="space-y-3 text-slate-300">
              <p>Score: <span className="text-white font-semibold">{health?.security_score ?? '—'}</span></p>
              <p>Critical vulnerabilities: <span className="text-white font-semibold">{dashboard?.security_analysis?.critical_vulnerabilities ?? 0}</span></p>
              <div>
                <p className="text-slate-500 mb-2">High risk files</p>
                <ul className="space-y-2">
                  {(dashboard?.security_analysis?.high_risk_files || []).map((file) => (
                    <li key={file} className="text-sm text-slate-300 font-mono">{file}</li>
                  ))}
                </ul>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Dependency Risk">
            <div className="space-y-3 text-slate-300">
              <p>Score: <span className="text-white font-semibold">{health?.dependency_score ?? '—'}</span></p>
              <p>Dependencies scanned: <span className="text-white font-semibold">{dependency?.dependencies_scanned ?? 0}</span></p>
              <p>Vulnerable dependencies: <span className="text-white font-semibold">{dependency?.vulnerable_dependencies ?? 0}</span></p>
              <p>Critical dependency risks: <span className="text-white font-semibold">{dependency?.critical_risks ?? 0}</span></p>
            </div>
          </SectionCard>
        </div>

        <div className="grid xl:grid-cols-2 gap-6">
          <SectionCard title="Code Quality and Technical Debt">
            <div className="space-y-3 text-slate-300">
              <p>Code quality score: <span className="text-white font-semibold">{health?.quality_score ?? '—'}</span></p>
              <p>Documentation score: <span className="text-white font-semibold">{health?.documentation_score ?? '—'}</span></p>
              <p>Code smells: <span className="text-white font-semibold">{dashboard?.code_quality?.code_smells ?? 0}</span></p>
              <p>High complexity functions: <span className="text-white font-semibold">{dashboard?.code_quality?.high_complexity_functions ?? 0}</span></p>
              <p>Top debt reason: <span className="text-slate-200">{debt?.debt_reasons?.[0] || 'No major debt reason reported.'}</span></p>
            </div>
          </SectionCard>

          <SectionCard title="Developer Reputation">
            <div className="space-y-4">
              <p className="text-slate-300">
                Developer report status: <span className="text-white font-semibold">{developer?.repository || repositoryId}</span>
              </p>
              <div className="space-y-3">
                {topContributors.length ? topContributors.map((contributor) => (
                  <div
                    key={contributor.developer}
                    className="rounded-2xl px-4 py-3 flex items-center justify-between"
                    style={{
                      background: 'rgba(30, 41, 59, 0.65)',
                      border: '1px solid rgba(148, 163, 184, 0.12)',
                    }}
                  >
                    <span className="text-slate-200">{contributor.developer}</span>
                    <span className="text-sky-300">{contributor.reputation_score}</span>
                  </div>
                )) : (
                  <p className="text-slate-400">No contributor data available yet.</p>
                )}
              </div>
            </div>
          </SectionCard>
        </div>

        <div className="grid xl:grid-cols-2 gap-6">
          <SectionCard title="Agent Activity">
            <div className="space-y-3">
              {(dashboard?.agent_activity || []).length ? (
                dashboard.agent_activity.map((item, index) => (
                  <div
                    key={`${item}-${index}`}
                    className="rounded-2xl px-4 py-3 text-slate-300"
                    style={{
                      background: 'rgba(30, 41, 59, 0.65)',
                      border: '1px solid rgba(148, 163, 184, 0.12)',
                    }}
                  >
                    {item}
                  </div>
                ))
              ) : (
                <p className="text-slate-400">Agent activity will appear here once the execution monitor emits updates.</p>
              )}
            </div>
          </SectionCard>

          <SectionCard title="Alerts and Priority Areas">
            <div className="space-y-3">
              {alerts.length ? alerts.map((alert, index) => (
                <div
                  key={`${alert}-${index}`}
                  className="rounded-2xl px-4 py-3 text-slate-200"
                  style={{
                    background: 'rgba(127, 29, 29, 0.3)',
                    border: '1px solid rgba(248, 113, 113, 0.2)',
                  }}
                >
                  {alert}
                </div>
              )) : (
                <p className="text-slate-400">No high-priority alerts reported.</p>
              )}
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
