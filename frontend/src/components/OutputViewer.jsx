import { useState } from 'react'

const TABS = [
  { key: 'intent',  label: '🧠 Intent',    desc: 'Extracted App Intent' },
  { key: 'ui',      label: '🖥️ UI Schema',  desc: 'Pages & Components' },
  { key: 'api',     label: '🔌 API Schema', desc: 'Endpoints & Methods' },
  { key: 'db',      label: '🗄️ DB Schema',  desc: 'Tables & Relations' },
  { key: 'auth',    label: '🔐 Auth Schema', desc: 'Roles & Permissions' },
  { key: 'refine',  label: '🔧 Refinement', desc: 'Fix Log' },
]

function syntaxHighlight(json) {
  const str = JSON.stringify(json, null, 2)
  return str
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
    .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
    .replace(/: (-?\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
    .replace(/: (true|false)/g, ': <span class="json-bool">$1</span>')
    .replace(/: (null)/g, ': <span class="json-null">$1</span>')
}

function IntentView({ intent }) {
  if (!intent) return null
  return (
    <div className="intent-grid">
      <div className="intent-item">
        <div className="intent-item-label">App Name</div>
        <div className="intent-item-value">{intent.app_name}</div>
      </div>
      <div className="intent-item">
        <div className="intent-item-label">App Type</div>
        <div className="intent-item-value">{intent.app_type}</div>
      </div>
      <div className="intent-item">
        <div className="intent-item-label">Complexity</div>
        <div className="intent-item-value" style={{textTransform:'capitalize'}}>{intent.complexity}</div>
      </div>
      <div className="intent-item" style={{gridColumn:'1/-1'}}>
        <div className="intent-item-label">Description</div>
        <div className="intent-item-value">{intent.description}</div>
      </div>
      <div className="intent-item">
        <div className="intent-item-label">Core Features</div>
        <div className="tag-list">
          {(intent.core_features || []).map((f, i) => <span key={i} className="tag">{f}</span>)}
        </div>
      </div>
      <div className="intent-item">
        <div className="intent-item-label">User Roles</div>
        <div className="tag-list">
          {(intent.user_roles || []).map((r, i) => <span key={i} className="tag">{r}</span>)}
        </div>
      </div>
      <div className="intent-item">
        <div className="intent-item-label">Integrations</div>
        <div className="tag-list">
          {(intent.integrations || []).map((r, i) => <span key={i} className="tag">{r}</span>)}
        </div>
      </div>
      {intent.assumptions?.length > 0 && (
        <div className="intent-item" style={{gridColumn:'1/-1'}}>
          <div className="intent-item-label">Assumptions Made</div>
          <ul style={{paddingLeft:16, marginTop:6}}>
            {intent.assumptions.map((a, i) => (
              <li key={i} style={{fontSize:13, color:'var(--text-secondary)', marginBottom:4}}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function JsonView({ data }) {
  const [copied, setCopied] = useState(false)
  if (!data) return <div style={{padding:24, color:'var(--text-muted)'}}>No data available</div>

  const copy = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <>
      <div className="output-toolbar">
        <span className="output-title">{Object.keys(data).length} top-level keys</span>
        <button id="copy-json-btn" className={`copy-btn ${copied ? 'copied' : ''}`} onClick={copy}>
          {copied ? '✓ Copied!' : '📋 Copy JSON'}
        </button>
      </div>
      <div className="output-body">
        <pre
          className="json-view"
          dangerouslySetInnerHTML={{ __html: syntaxHighlight(data) }}
        />
      </div>
    </>
  )
}

export default function OutputViewer({ result, validationReport }) {
  const [activeTab, setActiveTab] = useState('intent')

  if (!result) {
    return (
      <div className="output-section">
        <div className="empty-state">
          <div className="empty-state-icon">🚀</div>
          <h3>Ready to compile</h3>
          <p>Enter an app description above and click Generate to see the full configuration</p>
        </div>
      </div>
    )
  }

  const getTabData = () => {
    switch (activeTab) {
      case 'intent': return null // rendered specially
      case 'ui':    return result.schemas?.ui_schema
      case 'api':   return result.schemas?.api_schema
      case 'db':    return result.schemas?.db_schema
      case 'auth':  return result.schemas?.auth_schema
      case 'refine':return result.refinement_log
      default:      return null
    }
  }

  return (
    <div className="output-section">
      {/* Validation badge */}
      {validationReport && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
          <span className={`validation-badge ${validationReport.is_valid ? 'valid' : 'invalid'}`}>
            {validationReport.is_valid ? '✓ Schema Valid' : `✗ ${validationReport.error_count} Errors`}
          </span>
          {!validationReport.is_valid && validationReport.errors?.slice(0, 2).map((e, i) => (
            <span key={i} style={{ fontSize: 12, color: 'var(--red)' }}>{e}</span>
          ))}
        </div>
      )}

      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            id={`tab-${tab.key}`}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="output-card">
        {activeTab === 'intent' ? (
          <IntentView intent={result.intent} />
        ) : (
          <JsonView data={getTabData()} />
        )}
      </div>
    </div>
  )
}
