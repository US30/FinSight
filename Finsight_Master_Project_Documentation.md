# Finsight: Master Project Documentation & Architecture Blueprint
## Multi-Agent RAG for Automated Financial Due Diligence (M.Tech NLP Project)

**Version:** 3.0 (Complete Master Document)
**Target Environment:** Local Workstation / Cloud Instance
**Hardware Specifications:** NVIDIA H100 (40GB VRAM slice), 256 GB System RAM

---

## 1. Resume / ATS Summary (The "Elevator Pitch")
*Add this 4-5 line paragraph directly to your resume:*

**Project: Finsight (Multi-Agent RAG for Automated Financial Due Diligence)**
> Engineered **"Finsight,"** a Multi-Agent RAG pipeline for automated fundamental analysis, leveraging 256GB system RAM for high-throughput, in-memory sanitization of 9.5GB of complex SEC XBRL/XML filings. Orchestrated an autonomous reasoning engine using LangGraph, Qdrant, and a local `gemma-4-E4B-it` LLM, optimizing inference via bfloat16 and Flash Attention 2 on an NVIDIA H100 40GB VRAM slice. The agent reliably extracts 25+ structured financial KPIs (e.g., EBITDA, ROE), aggregates 5-year trends, and synthesizes deep qualitative filing analyses into a strict JSON schema to power a real-time Fintech dashboard.

---

## 2. Infrastructure & Tech Stack (Local Execution Only)

### 2.1. Hardware Utilization Strategy
* **GPU:** NVIDIA H100 (40GB VRAM slice) allocated for rapid LLM inference and embedding generation.
* **System Memory:** 256GB RAM utilized for in-memory batch processing of 9.5GB raw HTML/XML files without disk swapping bottlenecks.
* **LLM Model:** `google/gemma-4-E4B-it` loaded via Hugging Face `transformers` in `bfloat16` precision with Flash Attention 2. (No paid APIs).
* **Embedding Model:** `BAAI/bge-large-en-v1.5` loaded on the GPU alongside the LLM for high-speed vectorization.

### 2.2. Core Libraries & Frameworks
* **Data Acquisition:** `sec-edgar-downloader` (Targeting Finance, IT, Pharma, Semiconductor sectors, years 2020-2025).
* **Data Sanitization:** `BeautifulSoup4`, `lxml`, `unstructured`
* **Orchestration:** `langchain`, `langgraph`
* **Vector Database:** `qdrant-client` (Local instance)
* **Application Interfaces:** `FastAPI` backend service with a `React`/`Vite` analytics dashboard

---

## 3. Data Ingestion & Sanitization Pipeline (`ingestion.py`)

Raw SEC EDGAR 10-K and 10-Q filings are highly unstructured and packed with markup that will poison vector embeddings if not handled. 

### 3.1. Parsing Workflow
1.  **Data Source:** Read the 9.5GB of downloaded data from `/content/drive/MyDrive/SEC_Filings_Data`.
2.  **Markup Sanitization (CRITICAL):**
    * Parse the raw files using `BeautifulSoup` and `lxml`.
    * **Strictly strip all HTML, XML, and XBRL tags.** The vector store will only accept clean, human-readable text and structured data.
3.  **Table vs. Text Separation:** * Use `unstructured` to detect financial tables and convert them to Markdown tables to preserve row/column relationships. 
    * Extract narrative text separately.
4.  **Semantic Chunking:** Use `RecursiveCharacterTextSplitter` to chunk the sanitized text logically by SEC sections (e.g., "Item 1A. Risk Factors", "Item 7. MD&A").
5.  **Vectorization:** Embed the clean chunks using `BAAI/bge-large-en-v1.5` and push them into the local **Qdrant** database (`vector_store.py`).

---

## 4. Multi-Agent Orchestration (`agent.py`)

The core intelligence is driven by a **LangGraph** state machine, enabling the agent to reason, calculate, and self-correct.

### 4.1. Agent Nodes
* **Researcher Node:** Translates user queries into optimal vector search queries. Retrieves the most relevant SEC chunks from Qdrant.
* **Analyst Node:** Reads the retrieved context to extract specific numerical values and qualitative insights.
* **Calculator Tool:** A secure Python-based mathematical tool that computes derived ratios (e.g., Current Ratio, Margins) based on the Analyst's extracted numbers to prevent LLM hallucination.
* **Critic Node (Self-Correction):** Cross-checks the calculated numbers and extracted text against the raw retrieved chunks. If data is contradictory or hallucinated, it forces the Researcher to fetch new context.

---

## 5. Output Data Schema (Frontend Integration)

The LLM is prompted via `Pydantic` to output its final analysis matching this **strict JSON schema**. All monetary values (except EPS) must be generated in **Billions of USD**.

### 5.1. Core Metadata
* `company_name` (string): Full name of the company (e.g., "Apple Inc.")
* `ticker` (string): Stock symbol (e.g., "AAPL")
* `sector` (string): Industrial sector
* `exchange` (string): Stock exchange (e.g., "NASDAQ")
* `fiscal_year_end` (string): Date of fiscal year end
* `filing_period` (string): Period covered (e.g., "Annual Report 2023")
* `summary` (string): **Executive Summary.** Rendered in a standard card. A concise 3-5 sentence paragraph summarizing company performance, major events, or overall financial health for the period.
* `analysis` (string): **Filing Analysis.** Rendered in a highlighted cyan card. A deep, technical interpretation of the numbers explaining *why* margins dropped or *what* is driving revenue growth, risks, and opportunities.

### 5.2. Financial Metrics (`financials` object)
**Income Statement**
* `revenue`: Total Revenue ($B)
* `revenue_growth`: Year-over-Year Growth (%)
* `gross_profit`: Gross Profit ($B)
* `gross_margin`: Gross Margin (%)
* `operating_income`: Operating Income ($B)
* `operating_margin`: Operating Margin (%)
* `ebitda`: EBITDA ($B)
* `ebitda_margin`: EBITDA Margin (%)
* `net_income`: Net Income ($B)
* `net_margin`: Net Margin (%)
* `eps_basic`: Basic Earnings Per Share ($)
* `eps_diluted`: Diluted Earnings Per Share ($)

**Balance Sheet**
* `total_assets`: Total Assets ($B)
* `total_liabilities`: Total Liabilities ($B)
* `shareholders_equity`: Shareholders' Equity ($B)
* `current_assets`: Current Assets ($B)
* `current_liabilities`: Current Liabilities ($B)
* `current_ratio`: Current Ratio (x)
* `long_term_debt`: Long-term Debt ($B)
* `total_debt`: Total Debt ($B)
* `debt_to_equity`: Debt-to-Equity Ratio

**Cash Flow & Returns**
* `operating_cf`: Operating Cash Flow ($B)
* `capex`: Capital Expenditures ($B)
* `free_cash_flow`: Free Cash Flow ($B)
* `fcf_margin`: FCF Margin (%)
* `roe`: Return on Equity (%)
* `roa`: Return on Assets (%)
* `roic`: Return on Invested Capital (%)

### 5.3. Trends & Charts Arrays (Last 5 Years)
* `revenue_trend`: Array of `{ year: string, value: number }`
* `profitability_trend`: Array of `{ year: string, net_income: number, ebitda: number, gross_profit: number }`
* `cash_flow_trend`: Array of `{ year: string, operating: number, investing: number, financing: number }`
* `segment_revenue`: Array of `{ name: string, value: number }` (Used for UI Pie Chart)

---

## 6. Execution Guidelines for Code Generation
When feeding this document to an AI coding assistant to generate the project files:
1.  **Memory Management:** Ensure the XML/XBRL stripping step (`ingestion.py`) uses batched processing to leverage the 256GB RAM without crashing.
2.  **Schema Enforcement:** The LangGraph agent MUST use `langchain-core.pydantic_v1` or `instructor` to guarantee the output strictly adheres to the JSON schema in Section 5.
3.  **Local Execution Constraint:** Do not generate any code containing OpenAI, Anthropic, or paid API keys. Rely exclusively on Hugging Face local pipelines for `gemma-4-E4B-it`.
