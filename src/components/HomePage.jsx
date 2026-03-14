import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import ParticleBackground from './ParticleBackground'
import { analyzeRepository } from '../services/api'

const SAMPLE_REPO = 'https://github.com/pallets/flask'

export default function HomePage() {
  const [repoUrl, setRepoUrl] = useState(SAMPLE_REPO)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleAnalyze = async (event) => {
    event.preventDefault()

    const trimmedUrl = repoUrl.trim()
    if (!trimmedUrl) {
      setError('Please enter a GitHub repository URL.')
      return
    }

    if (!trimmedUrl.startsWith('https://github.com/')) {
      setError('Please enter a valid GitHub repository URL.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const job = await analyzeRepository(trimmedUrl)

      navigate('/dashboard', {
        state: {
          repoUrl: trimmedUrl,
          repositoryId: job.repository,
          jobId: job.job_id,
          initialStatus: job.status,
        },
      })
    } catch (requestError) {
      console.error('API error:', requestError)
      setError(requestError.message || 'Repository analysis failed')
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden px-6" style={{ background: '#0d1117' }}>
      <ParticleBackground />

      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(circle at top left, rgba(59,130,246,0.16), transparent 32%), radial-gradient(circle at bottom right, rgba(16,185,129,0.12), transparent 28%)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="relative z-10 w-full max-w-3xl rounded-3xl p-8 md:p-12"
        style={{
          background: 'rgba(15, 23, 42, 0.78)',
          border: '1px solid rgba(148, 163, 184, 0.18)',
          boxShadow: '0 30px 80px rgba(2, 6, 23, 0.55)',
          backdropFilter: 'blur(18px)',
        }}
      >
        <p className="text-sm uppercase tracking-[0.28em] text-sky-300 mb-4">AI Repository Agent</p>
        <h1 className="text-4xl md:text-6xl font-black text-white leading-tight mb-4">
          Connect the dashboard to live repository intelligence.
        </h1>
        <p className="text-slate-300 text-lg mb-10 max-w-2xl">
          Submit any public GitHub repository and the backend will fetch it, run the agent pipeline,
          score the codebase, and return the dashboard data in one flow.
        </p>

        <form onSubmit={handleAnalyze} className="space-y-4">
          <label className="block text-sm text-slate-300" htmlFor="repo-url">
            GitHub repository URL
          </label>
          <div
            className="flex flex-col md:flex-row gap-3 rounded-2xl p-3"
            style={{
              background: 'rgba(15, 23, 42, 0.72)',
              border: '1px solid rgba(148, 163, 184, 0.16)',
            }}
          >
            <input
              id="repo-url"
              type="url"
              value={repoUrl}
              onChange={(event) => setRepoUrl(event.target.value)}
              placeholder={SAMPLE_REPO}
              disabled={loading}
              className="flex-1 bg-transparent outline-none text-white px-3 py-3 font-mono"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 rounded-xl font-semibold text-slate-950 disabled:opacity-60"
              style={{
                background: 'linear-gradient(135deg, #38bdf8, #34d399)',
              }}
            >
              {loading ? 'Starting Analysis...' : 'Analyze Repository'}
            </button>
          </div>
          {error && <p className="text-sm text-rose-400">{error}</p>}
        </form>

        <div className="grid md:grid-cols-3 gap-4 mt-10">
          {[
            ['Backend API', 'FastAPI endpoints for orchestration, scoring, reporting, and monitoring.'],
            ['Live Agent Flow', 'Job status, agent progress, and dashboard metrics come from the real backend pipeline.'],
            ['Frontend Dashboard', 'Health, risk, developer insights, dependency reports, and technical debt.'],
          ].map(([title, body]) => (
            <div
              key={title}
              className="rounded-2xl p-5"
              style={{
                background: 'rgba(30, 41, 59, 0.55)',
                border: '1px solid rgba(148, 163, 184, 0.12)',
              }}
            >
              <h2 className="text-white font-semibold mb-2">{title}</h2>
              <p className="text-sm text-slate-400 leading-6">{body}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  )
}
