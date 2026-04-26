"""Schema-aligned data generator for the FinSight web API."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from random import Random


@dataclass(frozen=True)
class CompanyProfile:
    ticker: str
    company_name: str
    sector: str
    exchange: str
    fiscal_year_end: str


COMPANIES: dict[str, CompanyProfile] = {
    "AAPL": CompanyProfile("AAPL", "Apple Inc.", "Technology", "NASDAQ", "September 28, 2024"),
    "ABBV": CompanyProfile("ABBV", "AbbVie Inc.", "Healthcare", "NYSE", "December 31, 2024"),
    "AMD": CompanyProfile("AMD", "Advanced Micro Devices, Inc.", "Semiconductors", "NASDAQ", "December 28, 2024"),
    "AMZN": CompanyProfile("AMZN", "Amazon.com, Inc.", "Consumer Technology", "NASDAQ", "December 31, 2024"),
    "AVGO": CompanyProfile("AVGO", "Broadcom Inc.", "Semiconductors", "NASDAQ", "November 3, 2024"),
    "BAC": CompanyProfile("BAC", "Bank of America Corporation", "Financial Services", "NYSE", "December 31, 2024"),
    "C": CompanyProfile("C", "Citigroup Inc.", "Financial Services", "NYSE", "December 31, 2024"),
    "GOOGL": CompanyProfile("GOOGL", "Alphabet Inc.", "Technology", "NASDAQ", "December 31, 2024"),
    "GS": CompanyProfile("GS", "The Goldman Sachs Group, Inc.", "Financial Services", "NYSE", "December 31, 2024"),
    "INTC": CompanyProfile("INTC", "Intel Corporation", "Semiconductors", "NASDAQ", "December 28, 2024"),
    "JNJ": CompanyProfile("JNJ", "Johnson & Johnson", "Healthcare", "NYSE", "December 29, 2024"),
    "JPM": CompanyProfile("JPM", "JPMorgan Chase & Co.", "Financial Services", "NYSE", "December 31, 2024"),
    "LLY": CompanyProfile("LLY", "Eli Lilly and Company", "Healthcare", "NYSE", "December 31, 2024"),
    "META": CompanyProfile("META", "Meta Platforms, Inc.", "Technology", "NASDAQ", "December 31, 2024"),
    "MRK": CompanyProfile("MRK", "Merck & Co., Inc.", "Healthcare", "NYSE", "December 31, 2024"),
    "MS": CompanyProfile("MS", "Morgan Stanley", "Financial Services", "NYSE", "December 31, 2024"),
    "MSFT": CompanyProfile("MSFT", "Microsoft Corporation", "Technology", "NASDAQ", "June 30, 2024"),
    "NVDA": CompanyProfile("NVDA", "NVIDIA Corporation", "Semiconductors", "NASDAQ", "January 26, 2025"),
    "PFE": CompanyProfile("PFE", "Pfizer Inc.", "Healthcare", "NYSE", "December 31, 2024"),
    "QCOM": CompanyProfile("QCOM", "Qualcomm Incorporated", "Semiconductors", "NASDAQ", "September 29, 2024"),
}


def _rng(*parts: str) -> Random:
    seed = sha256("|".join(parts).encode("utf-8")).hexdigest()
    return Random(int(seed[:16], 16))


def _rounded(value: float) -> float:
    return round(value, 2)


def _trend_series(base: float, growth_floor: float, growth_ceiling: float, years: list[str], rng: Random) -> list[float]:
    values: list[float] = []
    current = base
    for _year in years:
        values.append(_rounded(current))
        current = current * (1 + rng.uniform(growth_floor, growth_ceiling))
    return values


def generate_financial_payload(
    *,
    ticker: str,
    year: str,
    filing_type: str,
    quarter: str | None,
    query: str,
) -> dict:
    profile = COMPANIES[ticker]
    rng = _rng(ticker, year, filing_type, quarter or "FY")

    years = [str(int(year) - 4 + i) for i in range(5)]
    revenue_base = rng.uniform(48.0, 420.0)
    revenue_values = _trend_series(revenue_base, 0.04, 0.18, years, rng)
    revenue = revenue_values[-1]

    gross_margin = rng.uniform(38.0, 78.0)
    operating_margin = max(8.0, gross_margin - rng.uniform(10.0, 24.0))
    ebitda_margin = operating_margin + rng.uniform(2.0, 9.0)
    net_margin = max(5.0, operating_margin - rng.uniform(2.0, 9.0))
    revenue_growth = rng.uniform(-3.5, 24.0)

    quarter_scale = 0.23 if filing_type == "10-Q" else 1.0
    current_revenue = revenue * quarter_scale
    gross_profit = current_revenue * gross_margin / 100
    operating_income = current_revenue * operating_margin / 100
    ebitda = current_revenue * ebitda_margin / 100
    net_income = current_revenue * net_margin / 100

    total_assets = current_revenue * rng.uniform(2.1, 4.8)
    total_liabilities = total_assets * rng.uniform(0.35, 0.72)
    shareholders_equity = total_assets - total_liabilities
    current_assets = total_assets * rng.uniform(0.24, 0.42)
    current_liabilities = total_liabilities * rng.uniform(0.22, 0.41)
    cash_and_equivalents = total_assets * rng.uniform(0.07, 0.22)
    long_term_debt = total_liabilities * rng.uniform(0.28, 0.58)
    total_debt = long_term_debt + total_liabilities * rng.uniform(0.04, 0.16)

    operating_cf = current_revenue * rng.uniform(0.14, 0.34)
    capex = current_revenue * rng.uniform(0.03, 0.11)
    free_cash_flow = operating_cf - capex

    quarterly_label = f"{quarter} FY{year}" if filing_type == "10-Q" and quarter else f"FY{year}"
    filing_period = quarterly_label

    segments = ["Platform", "Services", "Enterprise", "Consumer"]
    raw_shares = [rng.uniform(0.12, 0.38) for _ in segments]
    total_share = sum(raw_shares)
    segment_revenue = [
        {"name": name, "value": _rounded(current_revenue * share / total_share)}
        for name, share in zip(segments, raw_shares, strict=False)
    ]

    profitability_trend = []
    cash_flow_trend = []
    for idx, period_year in enumerate(years):
        period_revenue = revenue_values[idx]
        profitability_trend.append(
            {
                "year": period_year,
                "net_income": _rounded(period_revenue * rng.uniform(0.09, 0.24)),
                "ebitda": _rounded(period_revenue * rng.uniform(0.16, 0.31)),
                "gross_profit": _rounded(period_revenue * rng.uniform(0.34, 0.7)),
            }
        )
        operating = period_revenue * rng.uniform(0.13, 0.32)
        investing = -period_revenue * rng.uniform(0.04, 0.14)
        financing = period_revenue * rng.uniform(-0.1, 0.07)
        cash_flow_trend.append(
            {
                "year": period_year,
                "operating": _rounded(operating),
                "investing": _rounded(investing),
                "financing": _rounded(financing),
            }
        )

    period_text = "quarterly filing" if filing_type == "10-Q" else "annual filing"
    summary = (
        f"{profile.company_name} shows a {period_text} profile centered on {query.strip() or 'operating performance'}. "
        f"Revenue for {filing_period} is modeled at ${_rounded(current_revenue)}B with gross margin at {_rounded(gross_margin)}%. "
        f"Cash generation remains positive, while the balance sheet maintains a moderate leverage posture."
    )
    analysis = (
        f"For {filing_period}, {profile.ticker} combines top-line momentum with operating discipline, producing "
        f"${_rounded(ebitda)}B of EBITDA and ${_rounded(free_cash_flow)}B of free cash flow. "
        f"Margin structure suggests the company is sustaining pricing power while funding ongoing investment programs. "
        f"Leverage stays manageable relative to equity, and liquidity coverage remains adequate for near-term obligations. "
        f"Overall, the filing points to a business with durable cash conversion and room for strategic reinvestment."
    )

    return {
        "company_name": profile.company_name,
        "ticker": profile.ticker,
        "sector": profile.sector,
        "exchange": profile.exchange,
        "fiscal_year_end": profile.fiscal_year_end,
        "filing_period": filing_period,
        "summary": summary,
        "financials": {
            "revenue": _rounded(current_revenue),
            "revenue_growth": _rounded(revenue_growth),
            "gross_profit": _rounded(gross_profit),
            "gross_margin": _rounded(gross_margin),
            "operating_income": _rounded(operating_income),
            "operating_margin": _rounded(operating_margin),
            "ebitda": _rounded(ebitda),
            "ebitda_margin": _rounded(ebitda_margin),
            "net_income": _rounded(net_income),
            "net_margin": _rounded(net_margin),
            "eps_basic": _rounded(rng.uniform(1.2, 9.4)),
            "eps_diluted": _rounded(rng.uniform(1.1, 8.9)),
            "total_assets": _rounded(total_assets),
            "total_liabilities": _rounded(total_liabilities),
            "shareholders_equity": _rounded(shareholders_equity),
            "current_assets": _rounded(current_assets),
            "current_liabilities": _rounded(current_liabilities),
            "current_ratio": _rounded(current_assets / current_liabilities if current_liabilities else 0.0),
            "long_term_debt": _rounded(long_term_debt),
            "total_debt": _rounded(total_debt),
            "debt_to_equity": _rounded(total_debt / shareholders_equity if shareholders_equity else 0.0),
            "cash_and_equivalents": _rounded(cash_and_equivalents),
            "operating_cf": _rounded(operating_cf),
            "capex": _rounded(capex),
            "free_cash_flow": _rounded(free_cash_flow),
            "fcf_margin": _rounded((free_cash_flow / current_revenue) * 100 if current_revenue else 0.0),
            "roe": _rounded((net_income / shareholders_equity) * 100 if shareholders_equity else 0.0),
            "roa": _rounded((net_income / total_assets) * 100 if total_assets else 0.0),
            "roic": _rounded((operating_income / (shareholders_equity + total_debt)) * 100 if shareholders_equity + total_debt else 0.0),
        },
        "revenue_trend": [
            {"year": period_year, "value": revenue_values[idx]}
            for idx, period_year in enumerate(years)
        ],
        "profitability_trend": profitability_trend,
        "cash_flow_trend": cash_flow_trend,
        "segment_revenue": segment_revenue,
        "analysis": analysis,
    }
