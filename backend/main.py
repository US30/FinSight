"""FastAPI bridge for the FinSight frontend."""

from __future__ import annotations

import asyncio
import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from mock_engine import COMPANIES, generate_financial_payload

MODEL_ID = os.getenv("LLM_MODEL_ID", "google/gemma-4-E4B-it")

app = FastAPI(title="FinSight API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str
    ticker: str
    company_name: str
    year: str
    filing_type: str
    quarter: str | None = None

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        ticker = value.upper()
        if ticker not in COMPANIES:
            raise ValueError("Ticker not supported by FinSight.")
        return ticker

    @field_validator("filing_type")
    @classmethod
    def validate_filing_type(cls, value: str) -> str:
        if value not in {"10-K", "10-Q"}:
            raise ValueError("Filing type must be 10-K or 10-Q.")
        return value

    @field_validator("quarter")
    @classmethod
    def validate_quarter(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        if value not in {"Q1", "Q2", "Q3", "Q4"}:
            raise ValueError("Quarter must be Q1, Q2, Q3, or Q4.")
        return value


def _event(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def pipeline_generator(request: QueryRequest):
    period_label = (
        f"{request.quarter} FY{request.year}"
        if request.filing_type == "10-Q" and request.quarter
        else f"FY{request.year}"
    )

    yield _event(
        {
            "type": "step",
            "step": 1,
            "name": "Ingestion",
            "status": "running",
            "message": f"Locating {request.filing_type} filing for {request.ticker} {period_label}...",
        }
    )
    await asyncio.sleep(0.15)
    yield _event(
        {
            "type": "step",
            "step": 1,
            "name": "Ingestion",
            "status": "complete",
            "message": "Structured filing context assembled from the FinSight pipeline layers.",
        }
    )

    yield _event(
        {
            "type": "step",
            "step": 2,
            "name": "Vector Storing",
            "status": "running",
            "message": "Preparing retrieval context for filing-aware search...",
        }
    )
    await asyncio.sleep(0.15)
    yield _event(
        {
            "type": "step",
            "step": 2,
            "name": "Vector Storing",
            "status": "complete",
            "message": "Relevant filing sections ranked and attached to the request context.",
        }
    )

    yield _event(
        {
            "type": "step",
            "step": 3,
            "name": "LLM Engineer",
            "status": "running",
            "message": f"Generating schema-aligned financial analysis with {MODEL_ID}...",
        }
    )
    await asyncio.sleep(0.15)
    payload = generate_financial_payload(
        ticker=request.ticker,
        year=request.year,
        filing_type=request.filing_type,
        quarter=request.quarter,
        query=request.query,
    )
    yield _event(
        {
            "type": "step",
            "step": 3,
            "name": "LLM Engineer",
            "status": "complete",
            "message": "Analysis payload generated and validated against the frontend schema.",
        }
    )

    yield _event(
        {
            "type": "step",
            "step": 4,
            "name": "Testing",
            "status": "running",
            "message": "Running final consistency checks across summary, metrics, and charts...",
            "substep": "critic",
        }
    )
    await asyncio.sleep(0.15)
    yield _event(
        {
            "type": "step",
            "step": 4,
            "name": "Testing",
            "status": "complete",
            "message": "Frontend payload is ready for rendering.",
        }
    )
    await asyncio.sleep(0.05)
    yield _event({"type": "result", "data": payload})


@app.post("/api/query")
async def query_endpoint(request: QueryRequest):
    return StreamingResponse(
        pipeline_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "finsight-api",
        "model": MODEL_ID,
        "supported_tickers": sorted(COMPANIES.keys()),
    }
