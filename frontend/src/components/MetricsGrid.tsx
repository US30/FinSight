import { FinancialData } from '../types/financial'

const fmt = {
  bn:  (v: number) => v == null ? '—' : `$${v.toFixed(2)}B`,
  pct: (v: number) => v == null ? '—' : `${v.toFixed(1)}%`,
  x:   (v: number) => v == null ? '—' : `${v.toFixed(2)}x`,
  usd: (v: number) => v == null ? '—' : `$${v.toFixed(2)}`,
}

function growthColor(v: number) {
  if (v > 0)  return 'var(--green)'
  if (v < 0)  return 'var(--red)'
  return 'var(--text-secondary)'
}

interface MetricCardProps {
  label: string
  value: string
  sub?: string
  subColor?: string
  accent?: string
}

function MetricCard({ label, value, sub, subColor, accent = 'var(--cyan)' }: MetricCardProps) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: '16px 18px',
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color 0.2s, background 0.2s',
    }}
    onMouseEnter={e => {
      (e.currentTarget as HTMLDivElement).style.borderColor = accent + '60'
      ;(e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card-hover)'
    }}
    onMouseLeave={e => {
      (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)'
      ;(e.currentTarget as HTMLDivElement).style.background = 'var(--bg-card)'
    }}>
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${accent}, transparent)` }} />
      <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', letterSpacing: '-0.01em' }}>
        {value}
      </div>
      {sub && (
        <div style={{ fontSize: 11, color: subColor || 'var(--text-secondary)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
          {sub}
        </div>
      )}
    </div>
  )
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{
      fontSize: 10, fontWeight: 600, color: 'var(--text-muted)',
      textTransform: 'uppercase', letterSpacing: '0.14em',
      marginBottom: 8, marginTop: 4,
      display: 'flex', alignItems: 'center', gap: 8,
    }}>
      <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
      {children}
      <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
    </div>
  )
}

interface Props { data: FinancialData }

export default function MetricsGrid({ data }: Props) {
  const f = data.financials

  return (
    <div style={{ animation: 'slide-in 0.35s ease both' }}>

      {/* Company header strip */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '16px 22px',
        marginBottom: 16,
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        flexWrap: 'wrap',
      }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            {data.company_name}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 4, alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{
              background: 'var(--cyan)22', border: '1px solid var(--cyan)44',
              color: 'var(--cyan)', fontSize: 11, fontWeight: 700,
              padding: '2px 8px', borderRadius: 4, fontFamily: 'var(--font-mono)', letterSpacing: '0.08em',
            }}>
              {data.ticker}
            </span>
            <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>{data.exchange}</span>
            <span style={{ color: 'var(--border-bright)', fontSize: 12 }}>•</span>
            <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>{data.sector}</span>
          </div>
        </div>

        <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'flex-end', marginBottom: 4 }}>
            {/* Annual / Quarterly badge */}
            {data.filing_type === '10-Q' ? (
              <span style={{
                background: 'var(--amber)20', border: '1px solid var(--amber)50',
                color: 'var(--amber)', fontSize: 10, fontWeight: 700,
                padding: '2px 8px', borderRadius: 4, fontFamily: 'var(--font-mono)', letterSpacing: '0.08em',
              }}>
                {data.quarter} — QUARTERLY
              </span>
            ) : (
              <span style={{
                background: 'var(--cyan)15', border: '1px solid var(--cyan)40',
                color: 'var(--cyan)', fontSize: 10, fontWeight: 700,
                padding: '2px 8px', borderRadius: 4, fontFamily: 'var(--font-mono)', letterSpacing: '0.08em',
              }}>
                ANNUAL
              </span>
            )}
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--cyan)', fontFamily: 'var(--font-mono)' }}>
            {data.filing_period}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
            Fiscal year ending {data.fiscal_year_end}
          </div>
        </div>
      </div>

      {/* ── Income Statement ──────────────────────────────────────────────── */}
      <SectionLabel>Income Statement</SectionLabel>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))', gap: 10, marginBottom: 16 }}>
        <MetricCard label="Revenue"          value={fmt.bn(f.revenue)}
          sub={`YoY Growth: ${f.revenue_growth > 0 ? '+' : ''}${f.revenue_growth.toFixed(1)}%`}
          subColor={growthColor(f.revenue_growth)} accent="var(--cyan)" />
        <MetricCard label="Gross Profit"     value={fmt.bn(f.gross_profit)}
          sub={`Margin: ${fmt.pct(f.gross_margin)}`} accent="var(--cyan)" />
        <MetricCard label="Operating Income" value={fmt.bn(f.operating_income)}
          sub={`Margin: ${fmt.pct(f.operating_margin)}`} accent="var(--blue)" />
        <MetricCard label="EBITDA"           value={fmt.bn(f.ebitda)}
          sub={`Margin: ${fmt.pct(f.ebitda_margin)}`} accent="var(--purple)" />
        <MetricCard label="Net Income"       value={fmt.bn(f.net_income)}
          sub={`Margin: ${fmt.pct(f.net_margin)}`} accent="var(--green)" />
        <MetricCard label="EPS (Basic)"      value={fmt.usd(f.eps_basic)}   accent="var(--green)" />
        <MetricCard label="EPS (Diluted)"    value={fmt.usd(f.eps_diluted)} accent="var(--green)" />
      </div>

      {/* ── Balance Sheet ─────────────────────────────────────────────────── */}
      <SectionLabel>Balance Sheet</SectionLabel>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))', gap: 10, marginBottom: 16 }}>
        <MetricCard label="Total Assets"       value={fmt.bn(f.total_assets)}       accent="var(--cyan)" />
        <MetricCard label="Total Liabilities"  value={fmt.bn(f.total_liabilities)}  accent="var(--red)" />
        <MetricCard label="Shareholders Equity"value={fmt.bn(f.shareholders_equity)}accent="var(--green)" />
        <MetricCard label="Cash & Equivalents" value={fmt.bn(f.cash_and_equivalents)}accent="var(--cyan)" />
        <MetricCard label="Current Assets"     value={fmt.bn(f.current_assets)}     accent="var(--blue)" />
        <MetricCard label="Current Liabilities"value={fmt.bn(f.current_liabilities)}accent="var(--amber)" />
        <MetricCard label="Current Ratio"      value={fmt.x(f.current_ratio)}       accent="var(--blue)" />
        <MetricCard label="Long-term Debt"     value={fmt.bn(f.long_term_debt)}     accent="var(--red)" />
        <MetricCard label="Total Debt"         value={fmt.bn(f.total_debt)}         accent="var(--red)" />
        <MetricCard label="Debt / Equity"      value={f.debt_to_equity.toFixed(2)}  accent="var(--amber)" />
      </div>

      {/* ── Cash Flow & Returns ───────────────────────────────────────────── */}
      <SectionLabel>Cash Flow &amp; Returns</SectionLabel>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(155px, 1fr))', gap: 10 }}>
        <MetricCard label="Operating Cash Flow" value={fmt.bn(f.operating_cf)}   accent="var(--cyan)" />
        <MetricCard label="CapEx"               value={fmt.bn(f.capex)}          accent="var(--amber)" />
        <MetricCard label="Free Cash Flow"      value={fmt.bn(f.free_cash_flow)}
          sub={`FCF Margin: ${fmt.pct(f.fcf_margin)}`} accent="var(--green)" />
        <MetricCard label="Return on Equity"    value={fmt.pct(f.roe)}   accent="var(--purple)" />
        <MetricCard label="Return on Assets"    value={fmt.pct(f.roa)}   accent="var(--purple)" />
        <MetricCard label="ROIC"                value={fmt.pct(f.roic)}  accent="var(--purple)" />
      </div>
    </div>
  )
}
