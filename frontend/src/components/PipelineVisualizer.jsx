const STAGES = [
  { key: 'intent_extraction',  label: 'Intent Extraction',  icon: '🧠', desc: 'Parsing user intent' },
  { key: 'system_design',      label: 'System Design',      icon: '🏗️', desc: 'Designing architecture' },
  { key: 'schema_generation',  label: 'Schema Generation',  icon: '📐', desc: 'Generating all schemas' },
  { key: 'refinement',         label: 'Refinement',         icon: '🔧', desc: 'Cross-layer consistency' },
  { key: 'validation_repair',  label: 'Validation & Repair',icon: '🛡️', desc: 'Validating & auto-fixing' },
]

function getStageStatus(stageKey, pipelineLog, isLoading, isDone) {
  if (!pipelineLog || pipelineLog.length === 0) return 'idle'
  const found = pipelineLog.find(s => s.stage === stageKey)
  if (!found) {
    // Check if a later stage is running → this one must be done conceptually
    const stageIndex = STAGES.findIndex(s => s.key === stageKey)
    const currentIndex = pipelineLog.length - 1
    if (stageIndex < currentIndex) return 'done'
    if (stageIndex === currentIndex && isLoading) return 'running'
    return 'idle'
  }
  return found.status || 'idle'
}

export default function PipelineVisualizer({ pipelineLog, isLoading, isDone, metrics }) {
  return (
    <div className="pipeline-section">
      <div className="section-title">
        <span>⚙️</span> Pipeline Stages
        {isDone && metrics && (
          <span style={{ marginLeft: 'auto', fontFamily: 'JetBrains Mono', fontSize: 12, color: 'var(--accent-light)' }}>
            Total: {metrics.total_latency_ms}ms · Retries: {metrics.retries}
          </span>
        )}
      </div>
      <div className="pipeline-stages">
        {STAGES.map((stage, idx) => {
          const log = pipelineLog?.find(s => s.stage === stage.key)
          let status = 'idle'
          if (pipelineLog && pipelineLog.length > 0) {
            const loggedIdx = pipelineLog.findIndex(s => s.stage === stage.key)
            if (loggedIdx !== -1) {
              status = pipelineLog[loggedIdx].status
            } else if (isDone) {
              status = 'done'
            } else if (isLoading && idx < pipelineLog.length) {
              status = 'done'
            } else if (isLoading && idx === pipelineLog.length) {
              status = 'running'
            }
          }

          return (
            <div key={stage.key} id={`stage-${stage.key}`} className={`stage-card ${status}`}>
              <div className="stage-icon">{stage.icon}</div>
              <div className="stage-name">{stage.label}</div>
              <div className="stage-status">
                {status === 'idle' && <><span>○</span> Waiting</>}
                {status === 'running' && <><span className="spinner">⟳</span> Running…</>}
                {status === 'done' && <><span>✓</span> Done</>}
                {status === 'error' && <><span>✗</span> Error</>}
              </div>
              {log?.latency_ms && (
                <div className="stage-latency">{log.latency_ms}ms</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
