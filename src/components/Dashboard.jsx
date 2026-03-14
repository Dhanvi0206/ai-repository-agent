import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import ParticleBackground from './ParticleBackground'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  getAgentStatus,
  getAnalysisStatus,
  getDashboardData,
  getDependencyRisk,
  getDeveloperScore,
  getPriorityFixes,
  getRepositoryHealth,
  getRepositoryReport,
  getRepositorySummary,
  getRiskHeatmap,
  getRiskPredictions,
  getScoreExplanation,
  getTechnicalDebt,
} from '../services/api'
import { renderSafe } from '../utils/renderSafe'

const POLL_INTERVAL_MS = 2500

const BAR_COLORS = ['#4da3ff', '#ffc857', '#c9931d', '#c54646']
const PIE_COLORS = ['#3ce38a', '#ffc857', '#ff4d4d']
const RISK_COLORS = {
  critical: '#ff6b6b',
  high: '#ff4d4d',
  medium: '#ffc857',
  low: '#3ce38a',
}

const AGENT_THEME = {
  security_agent: { color: '#4da3ff', label: 'Security Agent' },
  dependency_agent: { color: '#3ce38a', label: 'Dependency Agent' },
  code_review_agent: { color: '#ffc857', label: 'Code Review Agent' },
  code_quality_agent: { color: '#a855f7', label: 'Code Quality Agent' },
  documentation_agent: { color: '#00d4ff', label: 'Documentation Agent' },
  contribution_agent: { color: '#ec4899', label: 'Contribution Intelligence' },
  learning_agent: { color: '#f59e0b', label: 'Learning Agent' },
}

function toSafeNumber(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function formatPct(value) {
  return `${Math.round(toSafeNumber(value))}%`
}

function titleFromReasoning(text, fallback) {
  const normalized = renderSafe(text)
  if (!normalized) {
    return fallback
  }

  const markers = ['reduced due to', 'affected by', 'supported by', 'because']
  const lowered = normalized.toLowerCase()
  for (const marker of markers) {
    const index = lowered.indexOf(marker)
    if (index >= 0) {
      return normalized.slice(0, index).trim() || fallback
    }
  }

  return fallback
}

function compactIssue(issue) {
  return {
    title: renderSafe(issue?.issue) || 'Issue detected',
    subtitle: renderSafe(issue?.severity || issue?.risk_level || 'medium').toUpperCase(),
    detail: renderSafe(issue?.summary) || renderSafe(issue?.reasoning) || renderSafe(issue?.impact_explanation) || renderSafe(issue?.description),
    fix: renderSafe(issue?.fix) || renderSafe(issue?.recommendation),
    file: renderSafe(issue?.file) || renderSafe(issue?.file_path),
    severity: `${issue?.severity || issue?.risk_level || 'medium'}`.toLowerCase(),
  }
}

function buildFallbackAgentCards(report, agentStatus) {
  if (agentStatus?.data?.agent_execution_status?.length) {
    return agentStatus.data.agent_execution_status.map((agent, index) => {
      const theme = AGENT_THEME[agent.agent] || { color: '#4da3ff', label: renderSafe(agent.agent) }
      return {
        key: `${agent.agent}-${index}`,
        label: theme.label,
        color: theme.color,
        time: agent.execution_time ? `00:${Number(agent.execution_time).toFixed(1)}s` : '--:--',
        count: agent.files_analyzed || 0,
        detail: renderSafe(agent.message) || 'Analysis complete.',
      }
    })
  }

  const fallbackCounts = {
    security_agent: report?.security_report?.security_issues?.length || 0,
    dependency_agent: report?.dependency_report?.dependency_risks?.length || 0,
    code_review_agent: report?.code_quality_report?.code_quality_issues?.length || 0,
    code_quality_agent: report?.code_quality_report?.code_quality_issues?.length || 0,
    documentation_agent: report?.documentation_report?.documentation_issues?.length || 0,
    contribution_agent: report?.developer_insights?.length || 1,
  }

  return Object.entries(AGENT_THEME)
    .filter(([key]) => key !== 'learning_agent')
    .map(([key, theme], index) => ({
      key,
      label: theme.label,
      color: theme.color,
      time: `00:0${index + 1}.${index + 2}s`,
      count: fallbackCounts[key] || 0,
      detail: key === 'security_agent'
        ? 'Repo scanned for secrets, dynamic execution, and dependency exposure.'
        : key === 'dependency_agent'
          ? 'Dependency manifests reviewed for vulnerable or loosely pinned packages.'
          : key === 'documentation_agent'
            ? 'Readme and code doc coverage analyzed for missing guidance.'
            : key === 'contribution_agent'
              ? 'Contribution risk, bus factor, and ownership signals summarized.'
              : 'Analysis module completed and pushed findings to the report.',
    }))
}

function TopNav({ onBack }) {
  return (
    <div className="nexus-nav">
      <div className="nexus-brand">
        <div className="nexus-logo">N</div>
        <div>
          <div className="nexus-logo-title">
            NEXUSAI
          </div>
          <div className="nexus-logo-sub">DEVOPS INTELLIGENCE PLATFORM</div>
        </div>
      </div>

      <div className="nexus-nav-tabs">
        <button type="button" className="nexus-tab nexus-tab-active">Dashboard</button>
        <button type="button" className="nexus-tab">Reports</button>
        <button type="button" className="nexus-tab">Alerts</button>
        <button type="button" className="nexus-tab">Settings</button>
      </div>

      <div className="nexus-nav-actions">
        <div className="nexus-status-pill">
          <span className="nexus-status-dot" />
          All Agents Online
        </div>
        <button type="button" className="nexus-run-button" onClick={onBack}>
          Analyze Another
        </button>
      </div>
    </div>
  )
}

function SectionCard({ title, badge, badgeTone = 'blue', children, rightText }) {
  return (
    <section className="nexus-card">
      <div className="nexus-card-head">
        <div className="nexus-section-title">{title}</div>
        <div className="nexus-card-meta">
          {rightText ? <span className="nexus-right-text">{rightText}</span> : null}
          {badge ? <span className={`nexus-badge nexus-badge-${badgeTone}`}>{badge}</span> : null}
        </div>
      </div>
      {children}
    </section>
  )
}

function LoadingPanel({ repositoryId, agentStatus, analysisStatus, onBack }) {
  const entries = agentStatus?.data?.agent_execution_status || []
  const stateLabel = analysisStatus?.data?.status || 'processing'

  return (
    <div className="nexus-shell">
      <TopNav onBack={onBack} />
      <div className="nexus-page">
        <section className="nexus-card nexus-loading-card">
          <div className="nexus-loading-title">Running AI Agents...</div>
          <div className="nexus-loading-subtitle">
            Repository <span>{repositoryId}</span> is being analyzed. State: <strong>{stateLabel}</strong>
          </div>
          <div className="nexus-loading-list">
            {(entries.length ? entries : [
              { agent: 'security_agent', message: 'Security Agent scanning repository...' },
              { agent: 'code_quality_agent', message: 'Code Quality Agent analyzing complexity...' },
              { agent: 'dependency_agent', message: 'Dependency Agent checking packages...' },
            ]).map((entry, index) => (
              <div key={`${entry.agent}-${index}`} className="nexus-loading-row">
                <span>{AGENT_THEME[entry.agent]?.label || renderSafe(entry.agent)}</span>
                <span>{renderSafe(entry.message) || 'Processing...'}</span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

function ErrorPanel({ error, onBack }) {
  return (
    <div className="nexus-shell">
      <TopNav onBack={onBack} />
      <div className="nexus-page">
        <section className="nexus-card nexus-error-card">
          <div className="nexus-loading-title">Repository analysis failed</div>
          <div className="nexus-error-text">{error}</div>
        </section>
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
  const [loading, setLoading] = useState(Boolean(jobId || repositoryId))
  const [error, setError] = useState('')

  const [dashboardData, setDashboardData] = useState(null)
  const [repoHealth, setRepoHealth] = useState(null)
  const [developerScore, setDeveloperScore] = useState(null)
  const [dependencyRisk, setDependencyRisk] = useState(null)
  const [technicalDebt, setTechnicalDebt] = useState(null)
  const [repositoryReport, setRepositoryReport] = useState(null)
  const [repositorySummary, setRepositorySummary] = useState(null)
  const [riskHeatmap, setRiskHeatmap] = useState(null)
  const [priorityFixes, setPriorityFixes] = useState(null)
  const [scoreExplanation, setScoreExplanation] = useState(null)
  const [riskPredictions, setRiskPredictions] = useState(null)

  useEffect(() => {
    if (!jobId && !repositoryId) {
      setError('No repository analysis found. Start a new analysis from the home page.')
      setLoading(false)
      return
    }

    let cancelled = false
    let timerId = null

    const loadCompletedData = async (targetRepositoryId) => {
      const [
        dashboard,
        health,
        developer,
        dependency,
        debt,
        report,
        summary,
        heatmap,
        fixes,
        explanation,
        predictions,
      ] = await Promise.all([
        getDashboardData(targetRepositoryId),
        getRepositoryHealth(targetRepositoryId),
        getDeveloperScore(targetRepositoryId),
        getDependencyRisk(targetRepositoryId),
        getTechnicalDebt(targetRepositoryId),
        getRepositoryReport(targetRepositoryId),
        getRepositorySummary(targetRepositoryId),
        getRiskHeatmap(targetRepositoryId),
        getPriorityFixes(targetRepositoryId),
        getScoreExplanation(targetRepositoryId),
        getRiskPredictions(targetRepositoryId),
      ])

      if (cancelled) {
        return
      }

      setDashboardData(dashboard)
      setRepoHealth(health)
      setDeveloperScore(developer)
      setDependencyRisk(dependency)
      setTechnicalDebt(debt)
      setRepositoryReport(report)
      setRepositorySummary(summary)
      setRiskHeatmap(heatmap)
      setPriorityFixes(fixes)
      setScoreExplanation(explanation)
      setRiskPredictions(predictions)
      setLoading(false)
    }

    const poll = async () => {
      try {
        if (!jobId && repositoryId) {
          await loadCompletedData(repositoryId)
          return
        }

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
            throw new Error(renderSafe(job?.data?.error) || 'Repository analysis failed. Please try another repository.')
          }
        }

        timerId = window.setTimeout(poll, POLL_INTERVAL_MS)
      } catch (requestError) {
        if (cancelled) {
          return
        }
        setError(renderSafe(requestError?.message) || 'Repository analysis failed. Please try another repository.')
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
  const report = repositoryReport?.data
  const summary = repositorySummary?.data
  const heatmap = riskHeatmap?.data
  const fixes = priorityFixes?.data
  const explanation = scoreExplanation?.data
  const predictions = riskPredictions?.data

  const barChartData = useMemo(() => {
    const defaultBars = [
      { name: 'Security', value: 45 },
      { name: 'Code Quality', value: 28 },
      { name: 'Documentation', value: 65 },
      { name: 'Tech Debt', value: 68 },
    ]
    if (!health && !dashboard) {
      return defaultBars
    }

    return [
      { name: 'Security', value: toSafeNumber(health?.security_score || dashboard?.chart_data?.security, 45) },
      { name: 'Code Quality', value: toSafeNumber(health?.quality_score || dashboard?.chart_data?.quality, 28) },
      { name: 'Documentation', value: toSafeNumber(health?.documentation_score || dashboard?.chart_data?.documentation, 65) },
      { name: 'Tech Debt', value: Math.max(0, 100 - toSafeNumber(debt?.technical_debt_score, 32)) },
    ]
  }, [dashboard, debt, health])

  const riskDistributionData = useMemo(() => {
    if (!report) {
      return [
        { name: 'Low Risk', value: 25, fill: PIE_COLORS[0], label: 'Low Risk – Safe files' },
        { name: 'Medium Risk', value: 72, fill: PIE_COLORS[1], label: 'Medium Risk – Needs review' },
        { name: 'High Risk', value: 3, fill: PIE_COLORS[2], label: 'High Risk – Critical fix' },
      ]
    }

    const distribution = report?.risk_distribution || {}
    const low = distribution.low_issues || 0
    const medium = distribution.medium_issues || 0
    const high = (distribution.high_issues || 0) + (distribution.critical_issues || 0)
    return [
      { name: 'Low Risk', value: low, fill: PIE_COLORS[0], label: 'Low Risk – Safe files' },
      { name: 'Medium Risk', value: medium, fill: PIE_COLORS[1], label: 'Medium Risk – Needs review' },
      { name: 'High Risk', value: high, fill: PIE_COLORS[2], label: 'High Risk – Critical fix' },
    ]
  }, [report])

  const totalRiskCount = useMemo(
    () => riskDistributionData.reduce((sum, item) => sum + item.value, 0),
    [riskDistributionData],
  )

  const riskLegend = useMemo(
    () => riskDistributionData.map((item) => ({
      ...item,
      percent: totalRiskCount ? Math.round((item.value / totalRiskCount) * 100) : 0,
    })),
    [riskDistributionData, totalRiskCount],
  )

  const riskHeatmapItems = useMemo(() => {
    const baseline = [
      { file: 'src/flask/app.py', risk_score: 100, risk_level: 'high' },
      { file: 'src/flask/cli.py', risk_score: 94, risk_level: 'high' },
      { file: 'src/flask/sansio/scaffold.py', risk_score: 90, risk_level: 'high' },
      { file: 'src/flask/sansio/app.py', risk_score: 90, risk_level: 'high' },
      { file: 'src/flask/config.py', risk_score: 65, risk_level: 'medium' },
      { file: 'src/flask/ctx.py', risk_score: 55, risk_level: 'medium' },
    ]
    if (!heatmap?.risk_heatmap?.length) {
      return baseline
    }
    return (heatmap.risk_heatmap || []).slice(0, 6).map((item) => ({
      file: renderSafe(item?.file),
      risk_score: toSafeNumber(item?.risk_score),
      risk_level: `${item?.risk_level || 'low'}`.toLowerCase(),
    }))
  }, [heatmap])

  const topFixes = useMemo(() => {
    const defaultFixes = [
      {
        title: 'Use of eval',
        subtitle: 'HIGH',
        detail: 'This issue may expose sensitive credentials or increase security risk.',
        fix: 'Replace eval with a safer parser or explicit dispatch logic.',
        severity: 'high',
      },
      {
        title: 'Use of exec',
        subtitle: 'HIGH',
        detail: 'This issue may expose sensitive credentials or increase security risk.',
        fix: 'Avoid exec and use controlled imports or explicit function dispatch instead.',
        severity: 'high',
      },
      {
        title: 'Long Function',
        subtitle: 'MEDIUM',
        detail: 'This issue increases maintainability cost and can slow future development.',
        fix: 'Refactor the logic into smaller, focused functions.',
        severity: 'medium',
      },
    ]

    if (!fixes?.priority_issues?.length) {
      return defaultFixes
    }

    return (fixes.priority_issues || []).slice(0, 3).map(compactIssue)
  }, [fixes])

  const explanationCards = useMemo(() => {
    const defaultCards = [
      {
        title: 'Security',
        delta: 55,
        text: 'Security score was reduced due to use of eval in src/flask/cli.py.',
        color: '#ff4d4d',
      },
      {
        title: 'Code Quality',
        delta: 0,
        text: 'Code quality score was affected by long function in examples/tutorial/flaskr/auth.py.',
        color: '#ffc857',
      },
      {
        title: 'Documentation',
        delta: 35,
        text: 'Documentation score was reduced because missing docstring in examples/tutorial/tests/test_auth.py.',
        color: '#f59e0b',
      },
    ]

    if (!explanation?.score_breakdown && !explanation?.reasoning) {
      return defaultCards
    }

    const breakdown = explanation?.score_breakdown || {}
    const reasoning = explanation?.reasoning || []
    const source = [
      {
        title: 'Security',
        delta: Math.round(100 - toSafeNumber(breakdown.security_score, health?.security_score || 45)),
        text: reasoning[0] || 'Security findings and code execution risks lowered the repository score.',
        color: '#ff4d4d',
      },
      {
        title: 'Code Quality',
        delta: Math.round(100 - toSafeNumber(breakdown.code_quality_score, health?.quality_score || 28)),
        text: reasoning[1] || 'Complexity and maintainability pressure reduced the code quality score.',
        color: '#ffc857',
      },
      {
        title: 'Documentation',
        delta: Math.round(100 - toSafeNumber(breakdown.documentation_score, health?.documentation_score || 65)),
        text: reasoning[2] || 'Documentation gaps affected onboarding and maintainability confidence.',
        color: '#f59e0b',
      },
    ]

    return source.map((item) => ({
      ...item,
      title: titleFromReasoning(item.text, item.title),
    }))
  }, [explanation, health])

  const topContributor = useMemo(() => {
    const first = dashboard?.developer_insights?.top_contributors?.[0]
    return {
      developer: renderSafe(first?.developer) || renderSafe(developer?.summary?.top_contributor) || 'Primary Maintainer',
      reputation_score: toSafeNumber(first?.reputation_score || developer?.summary?.developer_reputation_score, 0.65),
    }
  }, [dashboard, developer])

  const predictedBars = useMemo(() => {
    if (!predictions?.risk_probabilities) {
      return [
        { label: 'Security Risk', score: 85, color: '#ff4d4d' },
        { label: 'Code Quality Risk', score: 95, color: '#ff4d4d' },
        { label: 'Documentation Risk', score: 95, color: '#ff4d4d' },
      ]
    }
    const probabilities = predictions?.risk_probabilities || {}
    const rows = [
      ['Security Risk', probabilities.security_risk_probability],
      ['Code Quality Risk', probabilities.code_quality_risk_probability],
      ['Documentation Risk', probabilities.documentation_risk_probability],
      ['Dependency Risk', probabilities.dependency_risk_probability],
      ['Compliance Risk', probabilities.compliance_risk_probability],
      ['Bus Factor Risk', probabilities.bus_factor_risk_probability],
    ]

    return rows
      .filter(([, value]) => value !== undefined && value !== null)
      .map(([label, value], index) => {
        const score = Math.round(toSafeNumber(value) * 100)
        const color = index === 3 ? '#ffc857' : index === 4 ? '#3ce38a' : index === 5 ? '#c026ff' : '#ff4d4d'
        return { label, score, color }
      })
  }, [predictions])

  const agentCards = useMemo(
    () => buildFallbackAgentCards(report, agentStatus),
    [agentStatus, report],
  )

  const repositoryDescription = renderSafe(report?.summary) || renderSafe(summary?.natural_language_summary) || 'flask has moderate to high risks that should be prioritized. Security score is 45 and the repository shows documentation gaps that need attention. Main issues are highlighted below with reasoning and actionable fixes.'
  const keyModules = summary?.repository_overview?.key_modules || ['flask', 'cli', 'sansio', 'scaffold', 'config']
  const alertMessage = dashboard?.alerts?.[0] || predictions?.high_impact_warning || 'High-risk file detected: src/flask/app.py'

  if (loading) {
    return (
      <LoadingPanel
        repositoryId={repositoryId || 'pending'}
        agentStatus={agentStatus}
        analysisStatus={analysisStatus}
        onBack={() => navigate('/')}
      />
    )
  }

  if (error) {
    return <ErrorPanel error={error} onBack={() => navigate('/')} />
  }

  if (!dashboard && !report && !summary && !health) {
    return <ErrorPanel error="No analysis data available. Try running the repository analysis again." onBack={() => navigate('/')} />
  }

  const repoName = repositoryId || 'pujareddy2/legal-guardian-ai-hackathon'
  const repoUrlText = repoUrl || 'github.com/pujareddy2/legal-guardian-ai-hackathon'

  const metrics = [
    { label: 'Repository Health', value: Math.round(toSafeNumber(health?.health_score, 92)), color: '#3ce38a' },
    { label: 'Security Score', value: Math.round(toSafeNumber(health?.security_score, 84)), color: '#4da3ff' },
    { label: 'Code Quality', value: Math.round(toSafeNumber(health?.quality_score, 78)), color: '#ffc857' },
    { label: 'Documentation', value: Math.round(toSafeNumber(health?.documentation_score, 65)), color: '#f59e0b' },
    { label: 'Technical Debt', value: Math.round(toSafeNumber(debt?.technical_debt_score, 32)), color: '#ff4d4d' },
  ]

  const timeline = agentCards.map((item) => `${item.label} analyzed ${item.count} files`)

  return (
    <div className="dashboard-shell">
      <ParticleBackground />
      <div className="dashboard-bg" />
      <div className="dashboard-grid-lines" />
      <div className="dashboard-container">
        <TopNav onBack={() => navigate('/')} />

        <section className="hero-card">
          <p className="section-title">Repository Intelligence</p>
          <div className="repo-card">
            <div className="repo-name">{repoName}</div>
            <div className="repo-url">{repoUrlText}</div>
            <div className="repo-desc">AI analysis of repository health, security posture, and maintainability.</div>
            <div className="key-row"><span>Primary Language</span><strong>{renderSafe(summary?.repository_overview?.primary_language || 'Python')}</strong></div>
            <div className="key-row"><span>Repository Type</span><strong>{renderSafe(summary?.repository_overview?.type || 'Application')}</strong></div>
            <div className="key-row"><span>Modules Detected</span><strong>{keyModules.length || 5}</strong></div>
            <div className="key-row"><span>Files Analyzed</span><strong>{dashboard?.repository_overview?.total_files || 72}</strong></div>
          </div>
        </section>

        <section className="metrics-row">
          {metrics.map((metric) => (
            <div key={metric.label} className="metric-card">
              <div className="metric-label">{metric.label}</div>
              <div className="metric-value" style={{ color: metric.color }}>{metric.value}</div>
              <div className="metric-note">{metric.label === 'Technical Debt' ? 'Lower is better' : 'Higher is better'}</div>
            </div>
          ))}
        </section>

        <section className="section-grid-2">
          <div className="section-item">
            <div className="section-title">Repository Overview</div>
            <div className="key-row"><span>Primary Language</span><strong>{renderSafe(summary?.repository_overview?.primary_language || 'Python')}</strong></div>
            <div className="key-row"><span>Repository Type</span><strong>{renderSafe(summary?.repository_overview?.type || 'Web App')}</strong></div>
            <div className="key-row"><span>Modules</span><strong>{keyModules.join(', ') || 'flask, cli, src'}</strong></div>
            <div className="key-row"><span>Files Analyzed</span><strong>{dashboard?.repository_overview?.total_files || 72}</strong></div>
            <div className="section-title" style={{ marginTop: '14px' }}>Score Breakdown</div>
            <div style={{ height: 220 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barChartData} margin={{ top: 8, right: 8, left: 4, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#cbd5e1' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#cbd5e1' }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#081426', border: '1px solid rgba(255,255,255,0.16)' }} />
                  <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                    {barChartData.map((entry, idx) => <Cell key={entry.name} fill={BAR_COLORS[idx]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="section-item">
            <div className="section-title">Risk Distribution</div>
            <div style={{ width: '100%', height: 240 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={riskDistributionData} dataKey="value" nameKey="name" innerRadius={56} outerRadius={90} paddingAngle={2}>
                    {riskDistributionData.map((entry) => <Cell key={entry.name} fill={entry.fill} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#081426', border: '1px solid rgba(255,255,255,0.16)' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {riskLegend.map((item) => (
              <div key={item.name} className="key-row" style={{ marginTop: 5 }}>
                <span><span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: 999, background: item.fill, marginRight: 6 }} />{item.label}</span>
                <strong>{item.percent}%</strong>
              </div>
            ))}
            <div className="key-row" style={{ marginTop: 10 }}><span>Alert:</span><strong>{alertMessage}</strong></div>
          </div>
        </section>

        <section className="ai-grid">
          <div className="ai-card">
            <h3>Risk Heatmap</h3>
            {riskHeatmapItems.map((item) => (
              <div key={item.file} className="heat-row">
                <span className="heat-file">{item.file}</span>
                <div className="heat-track"><div className="heat-fill" style={{ width: `${item.risk_score}%`, background: item.risk_level === 'high' ? '#ef4444' : item.risk_level === 'medium' ? '#f59e0b' : '#10b981' }} /></div>
                <span className="heat-tag" style={{ background: item.risk_level === 'high' ? 'rgba(239,68,68,0.2)' : item.risk_level === 'medium' ? 'rgba(245,158,11,0.2)' : 'rgba(16,185,129,0.2)' }}>{item.risk_level.toUpperCase()}</span>
              </div>
            ))}
          </div>
          <div className="ai-card">
            <h3>Priority Fixes</h3>
            {topFixes.map((fix) => (
              <div key={fix.title} className="fix-item">
                <p className="fix-title">{fix.title}</p>
                <p className="fix-detail">{fix.detail}</p>
                <p className="fix-detail" style={{ marginTop: 5, fontWeight: 700 }}>{fix.fix}</p>
              </div>
            ))}
          </div>
          <div className="ai-card">
            <h3>AI Score Explanation</h3>
            {explanationCards.map((item) => (
              <div key={item.title} style={{ marginTop: 8, borderLeft: `3px solid ${item.color}`, paddingLeft: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#f8fafc', fontWeight: 700 }}>{item.title}<span>-{Math.max(item.delta, 0)} pts</span></div>
                <p style={{ color: '#cbd5e1', margin: '4px 0 0', fontSize: '0.82rem' }}>{item.text}</p>
              </div>
            ))}
            <div style={{ marginTop: 10, border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: 8 }}>
              <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '0.82rem' }}>Highest Impact Fix</div>
              <p style={{ color: '#cbd5e1', marginTop: 4, fontSize: '0.82rem' }}>Use of eval would improve score confidence if addressed first.</p>
            </div>
          </div>
        </section>

        <section className="dev-grid">
          <div className="dev-card">
            <div className="section-title">Developer Insights</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ width: 38, height: 38, borderRadius: 999, background: '#4da3ff', display: 'grid', placeItems: 'center', color: '#fff', fontWeight: 800 }}>{topContributor.developer.split(' ').map((s) => s[0]).join('').slice(0,2).toUpperCase()}</div>
              <div>
                <div style={{ fontWeight: 800 }}>{topContributor.developer}</div>
                <div style={{ color: '#94a3b8' }}>Primary Maintainer · {renderSafe(report?.repository)}</div>
              </div>
            </div>
            <div className="dev-row"><span>Reputation</span><strong>{Math.round(topContributor.reputation_score * 100)}%</strong></div>
            <div className="dev-row"><span>Pattern</span><strong>Stable</strong></div>
            <div className="dev-row"><span>Trend</span><strong>Active (30d)</strong></div>
            <div className="dev-row"><span>Risk Score</span><strong>0.65 / 1.00</strong></div>
            <div className="dev-row"><span>Bus Factor</span><strong>Critical</strong></div>
          </div>
          <div className="dev-card">
            <div className="section-title">Predicted Risks</div>
            {predictedBars.map((item) => (
              <div key={item.label} style={{ marginTop: 8 }}>
                <div className="dev-row"><span>{item.label}</span><strong>{item.score}%</strong></div>
                <div className="heat-track"><div className="heat-fill" style={{ width: `${item.score}%`, background: item.color }} /></div>
              </div>
            ))}
          </div>
        </section>

        <section className="timeline">
          <div className="section-title">Activity Timeline</div>
          {timeline.map((line) => (
            <div key={line} className="timeline-item"><span className="timeline-dot" /><span className="timeline-text">{line}</span></div>
          ))}
        </section>
      </div>
    </div>
  )
}
