import { useEffect, useRef } from 'react'

const STAGE_META = {
  intent_extraction:  { label: 'Intent Extraction',  icon: '🧠', color: '#818cf8' },
  system_design:      { label: 'System Design',       icon: '🏗️', color: '#34d399' },
  schema_generation:  { label: 'Schema Generation',   icon: '📐', color: '#f59e0b' },
  refinement:         { label: 'Refinement',          icon: '🔧', color: '#fb923c' },
  validation_repair:  { label: 'Validation & Repair', icon: '🛡️', color: '#a78bfa' },
  runtime_generation: { label: 'Runtime Generation',  icon: '🚀', color: '#22d3ee' },
}

function TypewriterText({ text, speed = 18 }) {
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current || !text) return
    ref.current.textContent = ''
    let i = 0
    const interval = setInterval(() => {
      if (!ref.current) { clearInterval(interval); return }
      ref.current.textContent += text[i]
      i++
      if (i >= text.length) clearInterval(interval)
    }, speed)
    return () => clearInterval(interval)
  }, [text, speed])
  return <span ref={ref} />
}

function StageCard({ event, isActive }) {
  const meta = STAGE_META[event.stage] || { label: event.stage, icon: '⚙️', color: '#6366f1' }
  const isDone = event.status === 'done'

  return (
    <div className={`thinking-stage-card ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}
      style={{ '--stage-color': meta.color }}>

      {/* Header row */}
      <div className="thinking-stage-header">
        <div className="thinking-stage-icon" style={{ color: meta.color }}>
          {meta.icon}
        </div>
        <div className="thinking-stage-info">
          <div className="thinking-stage-name">{meta.label}</div>
          {isActive && !isDone && (
            <div className="thinking-stage-detail">
              <TypewriterText text={event.detail} speed={12} />
            </div>
          )}
        </div>
        <div className="thinking-stage-right">
          {isDone ? (
            <div className="thinking-stage-latency">{event.latency_ms}ms</div>
          ) : (
            <div className="thinking-dots">
              <span /><span /><span />
            </div>
          )}
          <div className={`thinking-stage-status ${isDone ? 'done' : 'running'}`}>
            {isDone ? '✓' : '…'}
          </div>
        </div>
      </div>

      {/* Thought bubble (shown while running) */}
      {isActive && !isDone && event.thought && (
        <div className="thinking-thought">
          <span className="thinking-quote">"</span>
          <TypewriterText text={event.thought} speed={20} />
          <span className="thinking-quote">"</span>
        </div>
      )}

      {/* Summary (shown when done) */}
      {isDone && event.summary && (
        <div className="thinking-summary">
          <span className="thinking-check" style={{ color: meta.color }}>→</span>
          {event.summary}
        </div>
      )}

      {/* Assumptions list */}
      {isDone && event.assumptions && event.assumptions.length > 0 && (
        <div className="thinking-assumptions">
          <div className="thinking-assumptions-title">Assumptions made:</div>
          {event.assumptions.map((a, i) => (
            <div key={i} className="thinking-assumption-item">💡 {a}</div>
          ))}
        </div>
      )}
    </div>
  )
}

function RepairCard({ event }) {
  return (
    <div className="thinking-repair-card">
      <span className="thinking-repair-icon">⚠️</span>
      <span className="thinking-repair-text">
        Auto-repair #{event.attempt}: {event.thought}
      </span>
    </div>
  )
}

export default function ThinkingPanel({ events, isDone, totalLatency }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  // Build display state: merge start + done events per stage
  const stageMap = {}
  const repairEvents = []
  const displayOrder = []

  for (const ev of events) {
    if (ev.type === 'stage_start') {
      stageMap[ev.stage] = { ...ev, status: 'running' }
      if (!displayOrder.includes(ev.stage)) displayOrder.push(ev.stage)
    } else if (ev.type === 'stage_done') {
      stageMap[ev.stage] = { ...stageMap[ev.stage], ...ev, status: 'done' }
    } else if (ev.type === 'repair') {
      repairEvents.push(ev)
    }
  }

  const activeStage = displayOrder.find(s => stageMap[s]?.status === 'running')

  return (
    <div className="thinking-panel">
      <div className="thinking-panel-header">
        <div className="thinking-panel-title">
          <div className={`thinking-pulse ${isDone ? 'done' : 'active'}`} />
          {isDone ? '✅ Generation Complete' : '🤖 AI is thinking…'}
        </div>
        {isDone && totalLatency && (
          <div className="thinking-total-time">{(totalLatency / 1000).toFixed(1)}s total</div>
        )}
      </div>

      <div className="thinking-stages-list">
        {displayOrder.map(stageKey => {
          const ev = stageMap[stageKey]
          const isActive = stageKey === activeStage
          return (
            <div key={stageKey}>
              <StageCard event={ev} isActive={isActive} />
              {/* Show repairs after validation stage */}
              {stageKey === 'validation_repair' && repairEvents.map((r, i) => (
                <RepairCard key={i} event={r} />
              ))}
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {!isDone && (
        <div className="thinking-footer">
          <div className="thinking-progress-bar">
            <div
              className="thinking-progress-fill"
              style={{ width: `${(displayOrder.filter(s => stageMap[s]?.status === 'done').length / 6) * 100}%` }}
            />
          </div>
          <div className="thinking-footer-text">
            {displayOrder.filter(s => stageMap[s]?.status === 'done').length} / 6 stages complete
          </div>
        </div>
      )}
    </div>
  )
}
