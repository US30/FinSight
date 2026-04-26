import {
  AreaChart, Area, BarChart, Bar, ComposedChart, Line,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts'
import { FinancialData } from '../types/financial'

const GRID  = '#1a2744'
const TEXT  = '#8899bb'
const CYAN  = '#00d4ff'
const GREEN = '#00e676'
const AMBER = '#ffab40'
const RED   = '#ff5252'
const PURPLE= '#7c3aed'
const BLUE  = '#448aff'

const PIE_COLORS = [CYAN, PURPLE, GREEN, AMBER, BLUE, RED, '#ff80ab', '#b388ff']

const tooltipStyle = {
  contentStyle: { background: '#0f1629', border: '1px solid #1a2744', borderRadius: 8, color: '#e8edf5', fontSize: 12 },
  cursor: { fill: 'rgba(0,212,255,0.05)' },
}

interface ChartCardProps {
  title: string
  badge?: string
  badgeColor?: string
  children: React.ReactNode
}

function ChartCard({ title, badge, badgeColor = TEXT, children }: ChartCardProps) {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 10,
      padding: '18px 20px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {title}
        </div>
        {badge && (
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase',
            color: badgeColor, background: badgeColor + '20',
            border: `1px solid ${badgeColor}40`,
            padding: '1px 6px', borderRadius: 3, fontFamily: 'var(--font-mono)',
          }}>
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

interface Props { data: FinancialData }

export default function Charts({ data }: Props) {
  const { revenue_trend, profitability_trend, cash_flow_trend, segment_revenue } = data

  const isQuarterly  = data.filing_type === '10-Q'
  const quarterLabel = isQuarterly && data.quarter ? data.quarter : null
  const segmentTitle = quarterLabel
    ? `Revenue by Segment — ${quarterLabel}`
    : 'Revenue by Segment'

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 14,
      animation: 'fade-in 0.6s ease both',
    }}>

      {/* ── Revenue Trend — always annual ─────────────────────────────────── */}
      <ChartCard title="Revenue Trend (USD Billions)" badge="Annual" badgeColor={CYAN}>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={revenue_trend} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="gradRev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={CYAN} stopOpacity={0.25} />
                <stop offset="95%" stopColor={CYAN} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="year" tick={{ fill: TEXT, fontSize: 11 }} axisLine={{ stroke: GRID }} tickLine={false} />
            <YAxis tick={{ fill: TEXT, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}B`} />
            <Tooltip {...tooltipStyle} formatter={(v: number) => [`$${v.toFixed(2)}B`, 'Revenue']} />
            <Area type="monotone" dataKey="value" stroke={CYAN} strokeWidth={2} fill="url(#gradRev)"
              dot={{ fill: CYAN, r: 3, strokeWidth: 0 }} activeDot={{ r: 5, fill: CYAN }} />
          </AreaChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* ── Profitability Trend — always annual ───────────────────────────── */}
      <ChartCard title="Profitability Trend (USD Billions)" badge="Annual" badgeColor={PURPLE}>
        <ResponsiveContainer width="100%" height={220}>
          <ComposedChart data={profitability_trend} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="gradEbit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={PURPLE} stopOpacity={0.25} />
                <stop offset="95%" stopColor={PURPLE} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="year" tick={{ fill: TEXT, fontSize: 11 }} axisLine={{ stroke: GRID }} tickLine={false} />
            <YAxis tick={{ fill: TEXT, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}B`} />
            <Tooltip {...tooltipStyle} formatter={(v: number, n: string) => [`$${v.toFixed(2)}B`, n]} />
            <Legend wrapperStyle={{ fontSize: 11, color: TEXT }} />
            <Area type="monotone" dataKey="ebitda"       name="EBITDA"       stroke={PURPLE} strokeWidth={2} fill="url(#gradEbit)" dot={false} />
            <Line  type="monotone" dataKey="gross_profit" name="Gross Profit" stroke={GREEN}  strokeWidth={2} dot={{ fill: GREEN,  r: 3, strokeWidth: 0 }} />
            <Line  type="monotone" dataKey="net_income"   name="Net Income"   stroke={AMBER}  strokeWidth={2} dot={{ fill: AMBER,  r: 3, strokeWidth: 0 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* ── Cash Flow — always annual ─────────────────────────────────────── */}
      <ChartCard title="Cash Flow Analysis (USD Billions)" badge="Annual" badgeColor={GREEN}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={cash_flow_trend} margin={{ top: 4, right: 4, bottom: 0, left: 0 }} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke={GRID} />
            <XAxis dataKey="year" tick={{ fill: TEXT, fontSize: 11 }} axisLine={{ stroke: GRID }} tickLine={false} />
            <YAxis tick={{ fill: TEXT, fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}B`} />
            <Tooltip {...tooltipStyle} formatter={(v: number, n: string) => [`$${v.toFixed(2)}B`, n]} />
            <Legend wrapperStyle={{ fontSize: 11, color: TEXT }} />
            <Bar dataKey="operating" name="Operating" fill={GREEN}  radius={[3,3,0,0]} maxBarSize={28} />
            <Bar dataKey="investing" name="Investing" fill={RED}    radius={[3,3,0,0]} maxBarSize={28} />
            <Bar dataKey="financing" name="Financing" fill={BLUE}   radius={[3,3,0,0]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      {/* ── Segment Revenue — quarterly when 10-Q ────────────────────────── */}
      <ChartCard
        title={segmentTitle}
        badge={quarterLabel ? `${quarterLabel} Data` : 'Annual'}
        badgeColor={quarterLabel ? AMBER : CYAN}
      >
        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={segment_revenue}
              cx="50%" cy="50%"
              innerRadius={55} outerRadius={85}
              paddingAngle={3}
              dataKey="value"
              labelLine={false}
              label={({ name, percent }: { name: string; percent: number }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
            >
              {segment_revenue.map((_, i) => (
                <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="transparent" />
              ))}
            </Pie>
            <Tooltip
              contentStyle={tooltipStyle.contentStyle}
              formatter={(v: number) => [`$${v.toFixed(2)}B`, 'Revenue']}
            />
          </PieChart>
        </ResponsiveContainer>
        {/* Quarter note */}
        {quarterLabel && (
          <div style={{
            marginTop: 8, textAlign: 'center',
            fontSize: 10, color: AMBER, fontFamily: 'var(--font-mono)',
            opacity: 0.8,
          }}>
            Showing {quarterLabel} segment revenue only
          </div>
        )}
      </ChartCard>
    </div>
  )
}
