import { useState } from 'react'
import PromptInput from './components/PromptInput'
import ThinkingPanel from './components/ThinkingPanel'
import OutputViewer from './components/OutputViewer'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function App() {
  const [isLoading, setIsLoading]   = useState(false)
  const [isDone, setIsDone]         = useState(false)
  const [result, setResult]         = useState(null)
  const [streamEvents, setStreamEvents] = useState([])
  const [metrics, setMetrics]       = useState(null)
  const [error, setError]           = useState(null)

  const handleGenerate = async (prompt) => {
    setIsLoading(true)
    setIsDone(false)
    setResult(null)
    setError(null)
    setStreamEvents([])
    setMetrics(null)

    try {
      const res = await fetch(`${API_BASE}/generate-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail?.error || 'Failed to generate configuration')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() // keep incomplete line

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))

            if (event.type === 'done') {
              const data = event.result
              setResult(data)
              setMetrics(data.metrics)
              setIsDone(true)
              setIsLoading(false)
            } else if (event.type === 'error') {
              throw new Error(event.error)
            } else {
              // stage_start, stage_done, repair — add to stream
              setStreamEvents(prev => [...prev, event])
            }
          } catch (parseErr) {
            // skip malformed lines
          }
        }
      }
    } catch (err) {
      setError(err.message)
      setIsDone(false)
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
          Powered by Gemini Flash
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

        {/* Thinking Panel — shows live stream while loading and after done */}
        {(isLoading || isDone) && streamEvents.length > 0 && (
          <ThinkingPanel
            events={streamEvents}
            isDone={isDone}
            totalLatency={metrics?.total_latency_ms}
          />
        )}

        {/* Metrics bar */}
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
