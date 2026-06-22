import { useState } from 'react'

const EXAMPLES = [
  "Build a CRM with login, contacts, dashboard, and role-based access",
  "Create an e-commerce store with products, cart, and Stripe payments",
  "Build a project management tool like Trello with boards and teams",
  "Create a hospital system with patients, appointments, and billing",
]

export default function PromptInput({ onGenerate, isLoading }) {
  const [prompt, setPrompt] = useState('')

  const handleSubmit = () => {
    if (prompt.trim().length < 5) return
    onGenerate(prompt.trim())
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit()
  }

  return (
    <div className="prompt-section">
      <div className="prompt-card">
        <div className="prompt-label">
          <span>✏️</span> Describe your app
        </div>
        <textarea
          id="prompt-input"
          className="prompt-textarea"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. Build a CRM with login, contacts, dashboard, role-based access, and premium plan with Stripe payments. Admins can view analytics..."
          rows={4}
          disabled={isLoading}
        />
        <div className="prompt-footer">
          <div className="examples">
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                id={`example-${i}`}
                className="example-chip"
                onClick={() => setPrompt(ex)}
                disabled={isLoading}
              >
                {ex.length > 42 ? ex.slice(0, 42) + '…' : ex}
              </button>
            ))}
          </div>
          <button
            id="generate-btn"
            className="generate-btn"
            onClick={handleSubmit}
            disabled={isLoading || prompt.trim().length < 5}
          >
            {isLoading ? (
              <><span className="spinner">⟳</span> Compiling…</>
            ) : (
              <><span>⚡</span> Generate App Config</>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
