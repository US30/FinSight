import { FinancialData } from '../types/financial'

interface Props { data: FinancialData }

export default function AnalysisPanel({ data }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14, animation: 'fade-in 0.7s ease both' }}>

      {/* Executive Summary */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 10,
        padding: '18px 22px',
      }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10 }}>
          Executive Summary
        </div>
        <p style={{ fontSize: 13.5, color: 'var(--text-primary)', lineHeight: 1.75 }}>
          {data.summary}
        </p>
      </div>

      {/* Deep Analysis */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--cyan)30',
        borderRadius: 10,
        padding: '18px 22px',
      }}>
        <div style={{
          fontSize: 11, fontWeight: 600, color: 'var(--cyan)',
          textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 10,
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ opacity: 0.7 }}>◈</span> Filing Analysis
        </div>
        <p style={{ fontSize: 13.5, color: 'var(--text-primary)', lineHeight: 1.8 }}>
          {data.analysis}
        </p>
      </div>
    </div>
  )
}
