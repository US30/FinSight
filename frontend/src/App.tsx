import { useState, useRef, useCallback } from 'react'
import { FinancialData, PipelineStep } from './types/financial'
import PipelineSteps from './components/PipelineSteps'
import MetricsGrid from './components/MetricsGrid'
import Charts from './components/Charts'
import AnalysisPanel from './components/AnalysisPanel'

// ── Constants ──────────────────────────────────────────────────────────────────
const COMPANIES = [
  { ticker: 'AAPL',  name: 'Apple Inc.' },
  { ticker: 'ABBV',  name: 'AbbVie Inc.' },
  { ticker: 'AMD',   name: 'Advanced Micro Devices, Inc.' },
  { ticker: 'AMZN',  name: 'Amazon.com, Inc.' },
  { ticker: 'AVGO',  name: 'Broadcom Inc.' },
  { ticker: 'BAC',   name: 'Bank of America Corp.' },
  { ticker: 'C',     name: 'Citigroup Inc.' },
  { ticker: 'GOOGL', name: 'Alphabet Inc. (Class A)' },
  { ticker: 'GS',    name: 'Goldman Sachs Group, Inc.' },
  { ticker: 'INTC',  name: 'Intel Corp.' },
  { ticker: 'JNJ',   name: 'Johnson & Johnson' },
  { ticker: 'JPM',   name: 'JPMorgan Chase & Co.' },
  { ticker: 'LLY',   name: 'Eli Lilly and Company' },
  { ticker: 'META',  name: 'Meta Platforms, Inc.' },
  { ticker: 'MRK',   name: 'Merck & Co., Inc.' },
  { ticker: 'MS',    name: 'Morgan Stanley' },
  { ticker: 'MSFT',  name: 'Microsoft Corp.' },
  { ticker: 'NVDA',  name: 'NVIDIA Corp.' },
  { ticker: 'PFE',   name: 'Pfizer Inc.' },
  { ticker: 'QCOM',  name: 'Qualcomm Inc.' },
]

const YEARS         = ['2024', '2023', '2022', '2021', '2020']
const FILING_TYPES  = [
  { value: '10-K', label: '10-K — Annual Report' },
  { value: '10-Q', label: '10-Q — Quarterly Report' },
]
const QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4']

const INITIAL_STEPS: PipelineStep[] = [
  { step: 1, name: 'Ingestion',      status: 'idle', message: '' },
  { step: 2, name: 'Vector Storing', status: 'idle', message: '' },
  { step: 3, name: 'LLM Engineer',   status: 'idle', message: '' },
  { step: 4, name: 'Testing',        status: 'idle', message: '' },
]

// ── Dropdown ───────────────────────────────────────────────────────────────────
interface DropdownProps {
  label: string
  placeholder: string
  value: string
  onChange: (v: string) => void
  disabled?: boolean
  required?: boolean
  children: React.ReactNode
}

function Dropdown({ label, placeholder, value, onChange, disabled, required = true, children }: DropdownProps) {
  const filled = !!value
  return (
    <div style={{ flex: 1, minWidth: 0 }}>
      <label style={{
        display: 'block', fontSize: 10, fontWeight: 600,
        color: filled ? 'var(--cyan)' : 'var(--text-muted)',
        textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6,
        transition: 'color 0.2s',
      }}>
        {label}{required && <span style={{ color: 'var(--red)', marginLeft: 3 }}>*</span>}
      </label>
      <div style={{ position: 'relative' }}>
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          disabled={disabled}
          style={{
            width: '100%',
            background: 'var(--bg-card)',
            border: `1px solid ${filled ? 'var(--cyan)40' : 'var(--border)'}`,
            borderRadius: 9,
            padding: '10px 36px 10px 14px',
            color: filled ? 'var(--text-primary)' : 'var(--text-muted)',
            fontSize: 13,
            fontFamily: 'inherit',
            outline: 'none',
            cursor: disabled ? 'not-allowed' : 'pointer',
            appearance: 'none',
            WebkitAppearance: 'none',
            transition: 'border-color 0.2s',
            opacity: disabled ? 0.5 : 1,
          }}
          onFocus={e => { (e.target as HTMLSelectElement).style.borderColor = 'var(--cyan)' }}
          onBlur={e => { (e.target as HTMLSelectElement).style.borderColor = filled ? 'var(--cyan)40' : 'var(--border)' }}
        >
          <option value="" disabled>{placeholder}</option>
          {children}
        </select>
        <svg
          width="14" height="14" viewBox="0 0 24 24" fill="none"
          stroke={filled ? 'var(--cyan)' : 'var(--text-muted)'} strokeWidth="2.5"
          style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
        >
          <polyline points="6 9 12 15 18 9"/>
        </svg>
      </div>
    </div>
  )
}

// ── App ────────────────────────────────────────────────────────────────────────
export default function App() {
  const [query,           setQuery]           = useState('')
  const [selectedTicker,  setSelectedTicker]  = useState('')
  const [selectedYear,    setSelectedYear]    = useState('')
  const [selectedFiling,  setSelectedFiling]  = useState('')
  const [selectedQuarter, setSelectedQuarter] = useState('')
  const [loading,         setLoading]         = useState(false)
  const [steps,           setSteps]           = useState<PipelineStep[]>(INITIAL_STEPS)
  const [data,            setData]            = useState<FinancialData | null>(null)
  const [error,           setError]           = useState<string | null>(null)
  const [pipelineVisible, setPipelineVisible] = useState(false)
  const [queryTouched,    setQueryTouched]    = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const isQuarterly    = selectedFiling === '10-Q'
  const queryFilled    = query.trim().length > 0
  const quarterNeeded  = isQuarterly && !selectedQuarter

  const canSubmit =
    !loading &&
    queryFilled &&
    !!selectedTicker &&
    !!selectedYear &&
    !!selectedFiling &&
    !quarterNeeded

  const selectedCompany = COMPANIES.find(c => c.ticker === selectedTicker)

  // Reset quarter when switching away from 10-Q
  const handleFilingChange = (v: string) => {
    setSelectedFiling(v)
    if (v !== '10-Q') setSelectedQuarter('')
  }

  const updateStep = useCallback((stepNum: number, patch: Partial<PipelineStep>) => {
    setSteps(prev => prev.map(s => s.step === stepNum ? { ...s, ...patch } : s))
  }, [])

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return

    setLoading(true)
    setError(null)
    setData(null)
    setSteps(INITIAL_STEPS)
    setPipelineVisible(true)

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query:        query.trim(),
          ticker:       selectedTicker,
          company_name: selectedCompany?.name ?? '',
          year:         selectedYear,
          filing_type:  selectedFiling,
          quarter:      selectedFiling === '10-Q' ? selectedQuarter : null,
        }),
      })

      if (!response.ok) throw new Error(`Server error: ${response.status}`)
      if (!response.body) throw new Error('No response body')

      const reader  = response.body.getReader()
      const decoder = new TextDecoder()
      let   buffer  = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue

          let msg: Record<string, unknown>
          try { msg = JSON.parse(raw) } catch { continue }

          if (msg.type === 'step') {
            const { step, status, message, substep } = msg as {
              step: number; status: PipelineStep['status']
              message: string; substep?: PipelineStep['substep']
            }
            updateStep(step, { status, message, ...(substep !== undefined ? { substep } : {}) })
          } else if (msg.type === 'result') {
            // Attach filing context so child components can use it
            const result = msg.data as FinancialData
            result.filing_type = selectedFiling as '10-K' | '10-Q'
            result.quarter     = selectedFiling === '10-Q' ? selectedQuarter : undefined
            setData(result)
          } else if (msg.type === 'error') {
            throw new Error(String(msg.message))
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }, [canSubmit, query, selectedTicker, selectedCompany, selectedYear, selectedFiling, selectedQuarter, updateStep])

  // ── Validation checklist items ─────────────────────────────────────────────
  const checks = [
    { done: queryFilled,        label: 'Query'       },
    { done: !!selectedTicker,   label: 'Company'     },
    { done: !!selectedYear,     label: 'Fiscal Year' },
    { done: !!selectedFiling,   label: 'Filing Type' },
    ...(isQuarterly ? [{ done: !!selectedQuarter, label: 'Quarter' }] : []),
  ]
  const allDone = checks.every(c => c.done)

  // ── Nav badge label ────────────────────────────────────────────────────────
  const periodLabel = isQuarterly && selectedQuarter
    ? `${selectedQuarter} FY${selectedYear}`
    : `FY${selectedYear}`

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>

      {/* ── Nav ───────────────────────────────────────────────────────────── */}
      <nav style={{
        borderBottom: '1px solid var(--border)',
        background: 'var(--bg-secondary)',
        padding: '0 28px',
        height: 56,
        display: 'flex', alignItems: 'center', gap: 12,
        position: 'sticky', top: 0, zIndex: 100,
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, var(--cyan), var(--purple))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 15, fontWeight: 800, color: '#000',
          }}>F</div>
          <span style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            Fin<span style={{ color: 'var(--cyan)' }}>Sight</span>
          </span>
          <span style={{
            fontSize: 9, fontFamily: 'var(--font-mono)', color: 'var(--cyan)',
            background: 'var(--cyan)18', border: '1px solid var(--cyan)30',
            padding: '1px 5px', borderRadius: 3, letterSpacing: '0.12em', textTransform: 'uppercase',
          }}>PRO</span>
        </div>

        <div style={{ flex: 1 }} />

        {/* Context badge — show once all required fields are filled */}
        {allDone && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'var(--cyan)10', border: '1px solid var(--cyan)30',
            borderRadius: 20, padding: '3px 12px',
            animation: 'fade-in 0.3s ease both',
          }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>
              {selectedTicker}
            </span>
            <span style={{ width: 1, height: 12, background: 'var(--border-bright)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{selectedFiling}</span>
            <span style={{ width: 1, height: 12, background: 'var(--border-bright)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{periodLabel}</span>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{
            width: 6, height: 6, borderRadius: '50%',
            background: loading ? 'var(--amber)' : 'var(--green)',
            animation: loading ? 'glow-pulse 1s ease infinite' : 'none',
          }} />
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
            {loading ? 'Processing…' : 'Ready'}
          </span>
        </div>

        <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginLeft: 16 }}>
          <span style={{ color: 'var(--cyan)' }}>SEC 10-K / 10-Q</span> Intelligence
        </div>
      </nav>

      {/* ── Main ──────────────────────────────────────────────────────────── */}
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '28px 28px 60px' }}>

        {/* Hero */}
        {!data && (
          <div style={{ textAlign: 'center', padding: '52px 0 40px', animation: 'fade-in 0.5s ease both' }}>
            <div style={{
              display: 'inline-block',
              fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--cyan)',
              background: 'var(--cyan)12', border: '1px solid var(--cyan)30',
              padding: '4px 12px', borderRadius: 20, letterSpacing: '0.14em',
              textTransform: 'uppercase', marginBottom: 20,
            }}>
              SEC Filing Intelligence Platform
            </div>
            <h1 style={{
              fontSize: 44, fontWeight: 800, letterSpacing: '-0.03em',
              color: 'var(--text-primary)', lineHeight: 1.15, marginBottom: 14,
            }}>
              Institutional-grade insights<br />
              <span style={{ background: 'linear-gradient(90deg, var(--cyan), var(--purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                in seconds
              </span>
            </h1>
            <p style={{ fontSize: 15, color: 'var(--text-secondary)' }}>
              Select a company, year, and filing type to extract structured 10-K / 10-Q data with deep analysis.
            </p>
          </div>
        )}

        {/* ── Query panel ─────────────────────────────────────────────────── */}
        <div style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-bright)',
          borderRadius: 14, padding: '18px 20px',
          marginBottom: data ? 24 : 20,
          boxShadow: '0 0 40px rgba(0,212,255,0.05)',
        }}>

          {/* ── Mandatory query input ──────────────────────────────────────── */}
          <div style={{ marginBottom: 6 }}>
            <label style={{
              display: 'block', fontSize: 10, fontWeight: 600,
              color: queryFilled ? 'var(--cyan)' : 'var(--text-muted)',
              textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6,
              transition: 'color 0.2s',
            }}>
              Query<span style={{ color: 'var(--red)', marginLeft: 3 }}>*</span>
            </label>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10,
              background: 'var(--bg-card)',
              border: `1px solid ${queryTouched && !queryFilled ? 'var(--red)60' : queryFilled ? 'var(--cyan)40' : 'var(--border)'}`,
              borderRadius: 10, padding: '6px 12px',
              transition: 'border-color 0.2s',
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke={queryFilled ? 'var(--cyan)' : 'var(--text-muted)'} strokeWidth="2"
                style={{ flexShrink: 0, transition: 'stroke 0.2s' }}>
                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
              </svg>
              <input
                ref={inputRef}
                value={query}
                onChange={e => setQuery(e.target.value)}
                onBlur={() => setQueryTouched(true)}
                onKeyDown={e => { if (e.key === 'Enter') handleSubmit() }}
                placeholder="Describe what you want to analyse — e.g. 'Break down NVDA revenue and margins for this filing'"
                disabled={loading}
                style={{
                  flex: 1, background: 'transparent', border: 'none', outline: 'none',
                  color: 'var(--text-primary)', fontSize: 13.5, fontFamily: 'inherit',
                  padding: '8px 0',
                }}
              />
              {queryTouched && !queryFilled && (
                <span style={{ fontSize: 10, color: 'var(--red)', flexShrink: 0, fontFamily: 'var(--font-mono)' }}>
                  required
                </span>
              )}
            </div>
          </div>

          {/* ── Dropdowns row ─────────────────────────────────────────────── */}
          <div style={{
            display: 'flex', gap: 12, alignItems: 'flex-end',
            marginTop: 14,
          }}>
            {/* Company */}
            <Dropdown label="Company" placeholder="Select company…"
              value={selectedTicker} onChange={setSelectedTicker} disabled={loading}>
              {COMPANIES.map(c => (
                <option key={c.ticker} value={c.ticker}>{c.ticker} — {c.name}</option>
              ))}
            </Dropdown>

            {/* Year */}
            <Dropdown label="Fiscal Year" placeholder="Select year…"
              value={selectedYear} onChange={setSelectedYear} disabled={loading}>
              {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
            </Dropdown>

            {/* Filing type */}
            <Dropdown label="Filing Type" placeholder="Select filing…"
              value={selectedFiling} onChange={handleFilingChange} disabled={loading}>
              {FILING_TYPES.map(f => (
                <option key={f.value} value={f.value}>{f.label}</option>
              ))}
            </Dropdown>

            {/* Quarter — slides in when 10-Q is selected */}
            {isQuarterly && (
              <div style={{ animation: 'slide-in 0.25s ease both' }}>
                <Dropdown label="Quarter" placeholder="Select quarter…"
                  value={selectedQuarter} onChange={setSelectedQuarter} disabled={loading}>
                  {QUARTERS.map(q => <option key={q} value={q}>{q}</option>)}
                </Dropdown>
              </div>
            )}

            {/* Analyze button */}
            <div style={{ flexShrink: 0 }}>
              {/* invisible spacer to align with dropdown labels */}
              <div style={{ height: 22 }} />
              <button
                onClick={handleSubmit}
                disabled={!canSubmit}
                title={!canSubmit && !loading ? 'Complete all required fields to continue' : ''}
                style={{
                  background: canSubmit
                    ? 'linear-gradient(135deg, var(--cyan), #0095b3)'
                    : 'var(--bg-card)',
                  border: `1px solid ${canSubmit ? 'transparent' : 'var(--border)'}`,
                  borderRadius: 9,
                  padding: '10px 26px',
                  color: canSubmit ? '#000' : 'var(--text-muted)',
                  fontSize: 13, fontWeight: 700,
                  cursor: canSubmit ? 'pointer' : 'not-allowed',
                  display: 'flex', alignItems: 'center', gap: 8,
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                  height: 42,
                }}
              >
                {loading ? (
                  <>
                    <div style={{
                      width: 14, height: 14,
                      border: '2px solid rgba(0,0,0,0.2)', borderTopColor: '#000',
                      borderRadius: '50%', animation: 'spin 0.7s linear infinite',
                    }} />
                    Analyzing…
                  </>
                ) : (
                  <>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                    Analyze
                  </>
                )}
              </button>
            </div>
          </div>

          {/* ── Validation checklist ─────────────────────────────────────── */}
          {!allDone && !loading && (
            <div style={{
              display: 'flex', flexWrap: 'wrap', gap: 14, marginTop: 14,
              paddingTop: 12, borderTop: '1px solid var(--border)',
              alignItems: 'center',
            }}>
              {checks.map(({ done, label }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <div style={{
                    width: 14, height: 14, borderRadius: '50%',
                    background: done ? 'var(--green)' : 'var(--bg-card)',
                    border: `1.5px solid ${done ? 'var(--green)' : 'var(--border)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 8, color: done ? '#000' : 'transparent',
                    fontWeight: 800, flexShrink: 0, transition: 'all 0.25s',
                  }}>✓</div>
                  <span style={{ fontSize: 11, color: done ? 'var(--green)' : 'var(--text-muted)', transition: 'color 0.25s' }}>
                    {label}
                  </span>
                </div>
              ))}
              <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 'auto' }}>
                All fields marked <span style={{ color: 'var(--red)' }}>*</span> are required
              </span>
            </div>
          )}
        </div>

        {/* Pipeline steps */}
        <PipelineSteps steps={steps} visible={pipelineVisible} />

        {/* Error */}
        {error && (
          <div style={{
            background: 'rgba(255,82,82,0.1)', border: '1px solid rgba(255,82,82,0.3)',
            borderRadius: 10, padding: '14px 18px',
            color: 'var(--red)', fontSize: 13, marginBottom: 24, fontFamily: 'var(--font-mono)',
          }}>
            Error: {error}
          </div>
        )}

        {/* Dashboard */}
        {data && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <MetricsGrid data={data} />
            <Charts data={data} />
            <AnalysisPanel data={data} />
          </div>
        )}

        {/* Empty state */}
        {!data && !loading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginTop: 20 }}>
            {[
              { icon: '◈', title: '10-K / 10-Q Data', desc: 'Income statement, balance sheet, cash flow, and return metrics — all from SEC filings' },
              { icon: '⬢', title: 'Historical Trends', desc: 'Revenue, profitability, and cash flow across 5 annual periods — always shown as full-year context' },
              { icon: '◉', title: 'Validated Intelligence', desc: 'Researcher, Calculator, and Critic agents cross-check every figure before delivery' },
            ].map(card => (
              <div key={card.title} style={{
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                borderRadius: 12, padding: '24px 22px', textAlign: 'center',
              }}>
                <div style={{ fontSize: 28, color: 'var(--cyan)', marginBottom: 12 }}>{card.icon}</div>
                <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>{card.title}</div>
                <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{card.desc}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
