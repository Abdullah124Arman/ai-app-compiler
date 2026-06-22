import { useState } from 'react'
import PromptInput from './components/PromptInput'
import PipelineVisualizer from './components/PipelineVisualizer'
import OutputViewer from './components/OutputViewer'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [isLoading, setIsLoading] = useState(false)
  const [isDone, setIsDone] = useState(false)
  const [result, setResult] = useState(null)
  const [pipelineLog, setPipelineLog] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  const simulatePipelineProgress = (stages) => {
    // Simulate stage-by-stage progress for UX
    stages.forEach((stage, i) => {
      setTimeout(() => {
        setPipelineLog(prev => {
          const exists = prev.find(s => s.stage === stage.stage)
          if (exists) return prev
          return [...prev, { ...stage, status: 'running' }]
        })
        setTimeout(() => {
          setPipelineLog(prev =>
            prev.map(s => s.stage === stage.stage ? { ...s, status: 'done' } : s)
          )
        }, stage.latency_ms || 1500)
      }, i * 400)
    })
  }

  const handleGenerate = async (prompt) => {
    setIsLoading(true)
    setIsDone(false)
    setResult(null)
    setError(null)
    setPipelineLog([])
    setMetrics(null)

    // Start visual pipeline animation
    const fakeStages = [
      { stage: 'intent_extraction' },
      { stage: 'system_design' },
      { stage: 'schema_generation' },
      { stage: 'refinement' },
      { stage: 'validation_repair' },
    ]
    simulatePipelineProgress(fakeStages)

    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail?.error || 'Failed to generate configuration')
      }

      const data = await res.json()
      setResult(data)
      setMetrics(data.metrics)
      // Override pipeline log with real data
      if (data.metrics?.pipeline_stages) {
        setPipelineLog(data.metrics.pipeline_stages)
      }
      setIsDone(true)
    } catch (err) {
      setError(err.message)
      setIsDone(false)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">⚡</div>
          <span className="logo-text">AI App Compiler</span>
        </div>
        <div className="header-badge">
          <div className="badge-dot"></div>
          Powered by Groq · Llama 3.3 70B
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div className="hero-tag">🤖 Natural Language → Working App Config</div>
        <h1>Turn Ideas Into<br />Structured Apps</h1>
        <p>
          Describe any app in plain English. Our AI compiler generates complete
          UI, API, database, and auth schemas — validated and ready to execute.
        </p>
      </section>

      {/* Main content */}
      <main className="main">
        {/* Prompt Input */}
        <PromptInput onGenerate={handleGenerate} isLoading={isLoading} />

        {/* Error */}
        {error && (
          <div className="error-banner">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* Pipeline Visualizer — show when loading or done */}
        {(isLoading || isDone) && (
          <PipelineVisualizer
            pipelineLog={pipelineLog}
            isLoading={isLoading}
            isDone={isDone}
            metrics={metrics}
          />
        )}

        {/* Metrics */}
        {isDone && metrics && (
          <div className="metrics-bar">
            <div className="metric-card">
              <div className="metric-value">{metrics.total_latency_ms}ms</div>
              <div className="metric-label">Total Latency</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{metrics.retries}</div>
              <div className="metric-label">Auto-Repairs</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {result?.schemas ? Object.keys(result.schemas).length : 0}
              </div>
              <div className="metric-label">Schemas Generated</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {result?.validation_report?.is_valid ? '✓' : '✗'}
              </div>
              <div className="metric-label">Validation Status</div>
            </div>
          </div>
        )}

        {/* Output Viewer */}
        <OutputViewer
          result={result}
          validationReport={result?.validation_report}
        />
      </main>
    </div>
  )
}
