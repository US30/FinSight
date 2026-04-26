export interface Financials {
  // Income Statement
  revenue: number
  revenue_growth: number
  gross_profit: number
  gross_margin: number
  operating_income: number
  operating_margin: number
  ebitda: number
  ebitda_margin: number
  net_income: number
  net_margin: number
  eps_basic: number
  eps_diluted: number
  // Balance Sheet
  total_assets: number
  total_liabilities: number
  shareholders_equity: number
  current_assets: number
  current_liabilities: number
  current_ratio: number
  long_term_debt: number
  total_debt: number
  debt_to_equity: number
  cash_and_equivalents: number
  // Cash Flow
  operating_cf: number
  capex: number
  free_cash_flow: number
  fcf_margin: number
  // Returns
  roe: number
  roa: number
  roic: number
}

export interface TrendPoint {
  year: string
  value: number
}

export interface ProfitabilityPoint {
  year: string
  net_income: number
  ebitda: number
  gross_profit: number
}

export interface CashFlowPoint {
  year: string
  operating: number
  investing: number
  financing: number
}

export interface SegmentRevenue {
  name: string
  value: number
}

export interface FinancialData {
  company_name: string
  ticker: string
  sector: string
  exchange: string
  fiscal_year_end: string
  filing_period: string
  // enriched on the frontend before rendering
  filing_type?: '10-K' | '10-Q'
  quarter?: string
  summary: string
  financials: Financials
  revenue_trend: TrendPoint[]
  profitability_trend: ProfitabilityPoint[]
  cash_flow_trend: CashFlowPoint[]
  segment_revenue: SegmentRevenue[]
  analysis: string
}

export interface PipelineStep {
  step: number
  name: string
  status: 'idle' | 'running' | 'complete' | 'error'
  message: string
  substep?: 'researcher' | 'calculator' | 'critic' | null
}
