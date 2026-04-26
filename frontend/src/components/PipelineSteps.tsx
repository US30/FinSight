import { PipelineStep } from '../types/financial'

const STEP_ICONS = ['⬡', '◈', '⬢', '◉']
const STEP_COLORS = ['#00d4ff', '#7c3aed', '#00e676', '#ffab40']

const SUBSTEP_ICONS: Record<string, string> = {
  researcher: '🔍',
  calculator: '🧮',
  critic: '⚖️',
}

interface Props {
  steps: PipelineStep[]
  visible: boolean
}

export default function PipelineSteps({ steps, visible }: Props) {
  if (!visible) return null

  return (
    <div style={{
      background: 'var(--bg-secondary)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding: '20px 24px',
      marginBottom: 24,
      animation: 'slide-in 0.35s ease both',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: 'var(--cyan)',
          animation: 'pulse-cyan 1.5s ease infinite',
        }} />
        <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--cyan)', letterSpacing: '0.12em', textTransform: 'uppercase' }}>
          Processing Pipeline
        </span>
      </div>

      {/* Steps */}
      <div style={{ display: 'flex', gap: 8, position: 'relative' }}>
        {steps.map((step, i) => {
          const color = STEP_COLORS[i]
          const isActive = step.status === 'running'
          const isDone  = step.status === 'complete'
          const isIdle  = step.status === 'idle'

          return (
            <div key={step.step} style={{ flex: 1 }}>
              {/* Step card */}
              <div style={{
                background: isActive ? `${color}12` : isDone ? `${color}08` : 'var(--bg-card)',
                border: `1px solid ${isActive || isDone ? color + '40' : 'var(--border)'}`,
                borderRadius: 10,
                padding: '14px 16px',
                transition: 'all 0.3s ease',
                opacity: isIdle ? 0.4 : 1,
              }}>
                {/* Step number + icon */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <div style={{
                    width: 28, height: 28,
                    borderRadius: '50%',
                    background: isDone ? color : isActive ? `${color}30` : 'var(--bg-secondary)',
                    border: `1.5px solid ${isActive || isDone ? color : 'var(--border)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    color: isDone ? '#000' : color,
                    fontWeight: 700,
                  }}>
                    {isDone ? '✓' : step.step}
                  </div>
                  <span style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: isActive || isDone ? color : 'var(--text-secondary)',
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}>
                    {step.name}
                  </span>
                  {isActive && (
                    <div style={{
                      marginLeft: 'auto',
                      width: 14, height: 14,
                      border: `2px solid ${color}40`,
                      borderTopColor: color,
                      borderRadius: '50%',
                      animation: 'spin 0.7s linear infinite',
                    }} />
                  )}
                </div>

                {/* Message */}
                <div style={{
                  fontSize: 11,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-mono)',
                  lineHeight: 1.5,
                  minHeight: 32,
                }}>
                  {step.message || '—'}
                </div>

                {/* Substeps for step 4 */}
                {step.step === 4 && step.status !== 'idle' && (
                  <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                    {(['researcher', 'calculator', 'critic'] as const).map(sub => {
                      const active = step.substep === sub
                      const done = step.status === 'complete' ||
                        (step.substep === 'calculator' && sub === 'researcher') ||
                        (step.substep === 'critic' && sub !== 'critic')
                      return (
                        <div key={sub} style={{
                          flex: 1,
                          background: done ? `${color}20` : active ? `${color}15` : 'transparent',
                          border: `1px solid ${done || active ? color + '50' : 'var(--border)'}`,
                          borderRadius: 6,
                          padding: '5px 8px',
                          textAlign: 'center',
                          fontSize: 10,
                          color: done || active ? color : 'var(--text-muted)',
                          fontWeight: 500,
                          textTransform: 'capitalize',
                          transition: 'all 0.25s ease',
                        }}>
                          {SUBSTEP_ICONS[sub]} {sub}
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* Progress bar for running steps */}
                {isActive && (
                  <div style={{
                    marginTop: 10,
                    height: 2,
                    background: `${color}20`,
                    borderRadius: 1,
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: '40%',
                      background: color,
                      borderRadius: 1,
                      animation: 'scanner 1.4s ease-in-out infinite',
                    }} />
                  </div>
                )}
              </div>

              {/* Connector */}
              {i < steps.length - 1 && (
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: `calc(${(i + 1) * 25}% - 4px)`,
                  transform: 'translateY(-50%)',
                }} />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
