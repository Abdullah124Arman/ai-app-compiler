import { useState } from 'react'
import GitHubPushModal from './GitHubPushModal'

const TABS = [
  { key: 'intent',  label: '🧠 Intent',    desc: 'Extracted App Intent' },
  { key: 'ui',      label: '🖥️ UI Schema',  desc: 'Pages & Components' },
  { key: 'api',     label: '🔌 API Schema', desc: 'Endpoints & Methods' },
  { key: 'db',      label: '🗄️ DB Schema',  desc: 'Tables & Relations' },
  { key: 'auth',    label: '🔐 Auth Schema', desc: 'Roles & Permissions' },
  { key: 'refine',  label: '🔧 Refinement', desc: 'Fix Log' },
  { key: 'live',    label: '🚀 Live App', desc: 'Generated Working App' },
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

function LiveAppView({ runtime, appName, schemas, intent }) {
  const [copied,     setCopied]     = useState(false)
  const [showDeploy, setShowDeploy] = useState(false)
  const [showGH,     setShowGH]     = useState(false)

  if (!runtime || !runtime.html) return <div style={{padding:24, color:'var(--text-muted)'}}>No runtime generated yet. Ensure the prompt is detailed.</div>;

  const safeName = (appName || 'my-app').toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')

  // ── Download as self-contained HTML file ──────────────────
  const downloadHTML = () => {
    const blob = new Blob([runtime.html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${safeName}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ── Copy raw HTML to clipboard ─────────────────────────────
  const copyHTML = () => {
    navigator.clipboard.writeText(runtime.html)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '600px' }}>

      {/* Toolbar */}
      <div className="output-toolbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <span className="output-title">Generated React Runtime</span>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <span className="tag" style={{ background: 'rgba(99,102,241,0.2)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.4)' }}>{runtime.app_type}</span>
          <span className="tag" style={{ background: 'rgba(16,185,129,0.2)', color: '#34d399', border: '1px solid rgba(16,185,129,0.4)' }}>Fully Executable</span>
        </div>
      </div>

      {/* ── Download / Export Bar ───────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: '10px 16px',
        background: 'linear-gradient(90deg,rgba(99,102,241,0.06),rgba(167,139,250,0.04))',
        borderBottom: '1px solid var(--border)', flexWrap: 'wrap'
      }}>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginRight: 4 }}>📦 Export your app:</span>

        {/* Download HTML */}
        <button id="download-html-btn" onClick={downloadHTML} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 14px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
          background: 'linear-gradient(135deg,#6366f1,#7c3aed)', color: '#fff',
          boxShadow: '0 2px 12px rgba(99,102,241,0.3)', transition: 'opacity 0.15s'
        }}>
          ⬇️ Download HTML
        </button>

        {/* Copy HTML */}
        <button id="copy-html-btn" onClick={copyHTML} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 14px', borderRadius: 8, border: '1px solid var(--border)', cursor: 'pointer', fontSize: 12, fontWeight: 600,
          background: 'var(--bg-card2)', color: 'var(--text-secondary)', transition: 'all 0.15s'
        }}>
          {copied ? '✓ Copied!' : '📋 Copy HTML'}
        </button>

        {/* Deploy instructions toggle */}
        <button id="deploy-info-btn" onClick={() => setShowDeploy(v => !v)} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(16,185,129,0.4)', cursor: 'pointer', fontSize: 12, fontWeight: 600,
          background: 'rgba(16,185,129,0.08)', color: '#34d399', transition: 'all 0.15s'
        }}>
          🚀 {showDeploy ? 'Hide' : 'How to Deploy'}
        </button>

        {/* GitHub Push */}
        <button id="github-push-btn" onClick={() => setShowGH(true)} style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '6px 14px', borderRadius: 8, border: '1px solid rgba(139,92,246,0.4)', cursor: 'pointer', fontSize: 12, fontWeight: 600,
          background: 'rgba(139,92,246,0.1)', color: '#a78bfa', transition: 'all 0.15s'
        }}>
          🐙 Push to GitHub
        </button>
      </div>

      {/* GitHub Push Modal */}
      {showGH && (
        <GitHubPushModal
          onClose={() => setShowGH(false)}
          html={runtime.html}
          appName={appName}
          description={intent?.description || ''}
          schemas={schemas}
          intent={intent}
        />
      )}

      {/* ── Deploy Instructions Panel ───────────────────────── */}
      {showDeploy && (
        <div style={{
          padding: '16px 20px', background: 'var(--bg-card2)',
          borderBottom: '1px solid var(--border)', fontSize: 13
        }}>
          <div style={{ fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12, fontSize: 14 }}>
            🌐 Deploy Your Generated App in 2 Minutes
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: 12 }}>

            {/* Option 1 */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
              <div style={{ fontWeight: 700, color: '#818cf8', marginBottom: 8 }}>⚡ Option 1 — Netlify Drop</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, lineHeight: 1.6 }}>
                1. Click <strong style={{color:'var(--text-primary)'}}>⬇️ Download HTML</strong> above<br />
                2. Go to <a href="https://app.netlify.com/drop" target="_blank" style={{color:'#818cf8'}}>app.netlify.com/drop</a><br />
                3. Drag & drop the HTML file<br />
                4. ✅ Live in 10 seconds — free!
              </div>
            </div>

            {/* Option 2 */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
              <div style={{ fontWeight: 700, color: '#34d399', marginBottom: 8 }}>📁 Option 2 — GitHub Pages</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, lineHeight: 1.6 }}>
                1. Download the HTML file<br />
                2. Create a new GitHub repo<br />
                3. Upload as <code style={{color:'#f59e0b',background:'rgba(245,158,11,0.1)',padding:'1px 5px',borderRadius:4}}>index.html</code><br />
                4. Settings → Pages → Deploy<br />
                5. ✅ Free hosting at github.io
              </div>
            </div>

            {/* Option 3 */}
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 10, padding: 14 }}>
              <div style={{ fontWeight: 700, color: '#f59e0b', marginBottom: 8 }}>🖥️ Option 3 — Run Locally</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: 12, lineHeight: 1.6 }}>
                1. Download the HTML file<br />
                2. Double-click to open in browser<br />
                3. ✅ Works offline with no setup!<br />
                <span style={{color:'var(--text-muted)'}}>Data saved in browser localStorage</span>
              </div>
            </div>
          </div>

          <div style={{
            marginTop: 12, padding: '10px 14px', borderRadius: 8,
            background: 'rgba(99,102,241,0.06)', border: '1px solid rgba(99,102,241,0.2)',
            fontSize: 12, color: 'var(--text-secondary)'
          }}>
            💡 <strong style={{color:'var(--text-primary)'}}>No build step required.</strong> The downloaded HTML is fully self-contained —
            it includes React, all styles, and your app logic in a single file.
            Just open it in any browser or upload to any static host.
          </div>
        </div>
      )}

      {/* ── Live Preview iframe ─────────────────────────────── */}
      <div style={{ flex: 1, position: 'relative', backgroundColor: '#fff', borderRadius: showDeploy ? 0 : '0 0 12px 12px', overflow: 'hidden', minHeight: 500 }}>
        <iframe
          srcDoc={runtime.html}
          style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', border: 'none' }}
          title="Generated App"
          sandbox="allow-scripts allow-same-origin allow-forms"
        />
      </div>
    </div>
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

      <div className="output-card" style={activeTab === 'live' ? { padding: 0 } : {}}>
        {activeTab === 'intent' ? (
          <IntentView intent={result.intent} />
        ) : activeTab === 'live' ? (
          <LiveAppView runtime={result.runtime} appName={result.intent?.app_name} schemas={result.schemas} intent={result.intent} />
        ) : (
          <JsonView data={getTabData()} />
        )}
      </div>
    </div>
  )
}
