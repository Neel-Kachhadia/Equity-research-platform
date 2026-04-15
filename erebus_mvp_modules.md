# EREBUS — Minimal MVP Module Breakdown

> **System**: EREBUS — Equity Research & Business Universe System  
> **Source**: `equity_research_platform_architecture.html`, `erebus_model_stack_v2.html`, `erebus_model_stack_v3.html`  
> **Scope**: MVP only. No trading, no portfolio allocation, no price prediction.

---

## What EREBUS Is

An **AI-powered equity research intelligence platform** that:
- Ingests financial documents (annual reports, earnings transcripts, filings)
- Computes quantitative signals (ratios, trends, risk scores, alpha signals)
- Retrieves grounded evidence via RAG
- Synthesises analyst-grade written output via an LLM
- Ranks companies across a universe (e.g. NIFTY 50)

**It is not**: a trading system, price predictor, or portfolio optimizer.

---

## MVP Modules — 7 Total

---

### Module 1 · Data Ingestion & Storage

**Responsibility**  
Ingest raw financial data (structured fundamentals + unstructured documents) and store them in appropriate layers for downstream consumption.

**Inputs**
- Structured: Financial statements (P&L, Balance Sheet, Cash Flow) from vendor APIs or user uploads (Excel/CSV)
- Unstructured: Annual report PDFs, earnings call transcripts, SEBI/regulatory filings

**Outputs**
- Structured financials stored in a relational DB (per company, per period)
- Raw documents archived in object storage (S3 or equivalent)
- Document metadata registry (doc_id, company, type, fiscal period, status)

**Dependencies**
- None. This is the foundation layer. Everything else depends on it.

---

### Module 2 · Document Processing Pipeline (RAG — Embed & Index)

**Responsibility**  
Parse uploaded documents, chunk them semantically, embed into vectors, and index them in a vector store for retrieval.

**Inputs**
- Raw PDF/text documents from Module 1 storage
- Triggered per document on upload or scheduled for batch re-indexing

**Outputs**
- Vector embeddings stored in a vector DB (Qdrant / FAISS)
- Each chunk carries metadata: `doc_id`, `page_number`, `section_title`, `chunk_text`, `company_id`, `fiscal_period`
- Parse status updated in the document registry

**Dependencies**
- Module 1 (documents must exist in storage before processing)

---

### Module 3 · Quantitative Signal Engine

**Responsibility**  
Compute all deterministic financial signals from structured data: ratios, trends, volatility, consistency, and risk scores. This is pure math — no ML, no LLM.

**Sub-components** (all part of this one module for MVP):

| Sub-component | What it computes |
|---|---|
| Financial Ratio Suite | Revenue Growth, Net Profit Margin, ROE, D/E, FCF Conversion, Interest Coverage |
| Trend Model | Linear regression slope + moving average on 5-year metric series |
| Volatility Model | Std deviation of growth metrics; Parkinson estimator |
| Consistency Model | Coefficient of variation (CV) across years; hit rate of positive growth |
| Risk Scorer | Weighted rule-based composite of D/E, margin trend, volatility, ICR, FCF — outputs LOW / MEDIUM / HIGH + score 0–100 |

**Inputs**
- Structured financial data from Module 1 (per company, per period)

**Outputs**
- Per-company feature set: all ratios, trend slopes, volatility scores, risk score + breakdown
- Stored in a feature store (DB table or Redis cache) for fast retrieval

**Dependencies**
- Module 1 (needs structured financials)

---

### Module 4 · Sentiment Analysis (NLP Signal)

**Responsibility**  
Extract tone and sentiment signals from earnings call transcripts and MD&A sections using a financial-domain NLP model (FinBERT).

**Inputs**
- Earnings call transcripts / MD&A text (from Module 1 documents)

**Outputs**
- Per-sentence sentiment classification: Positive / Negative / Neutral
- Aggregated sentiment score per quarter
- Sentiment trajectory signal (improving / stable / deteriorating over time)
- Hedge language ratio (uncertainty/qualifications detected)

**Dependencies**
- Module 1 (documents must be available)
- *(Can run in parallel with Module 3)*

---

### Module 5 · Alpha Signal Aggregator

**Responsibility**  
Convert raw quant outputs and sentiment signals into 8 named, scored, directional alpha signals. Then compute one Composite Alpha Score (CAS) per company.

**The 8 Alpha Signals**

| Alpha | Based On |
|---|---|
| Growth Alpha | Revenue/EBIT CAGR vs sector median |
| Margin Alpha | Change in NPM, EBIT margin, gross margin over 3 years |
| Consistency Alpha | Inverse of CV for revenue/EBIT; hit rate of positive growth |
| Risk Alpha | Weighted inverse of D/E, ICR, margin volatility, FCF conversion |
| Volatility Alpha | Inverse of revenue/margin std deviation + Parkinson vol |
| Credibility Alpha | Guidance accuracy rate + sentiment trend − hedge language ratio |
| Sentiment Alpha | FinBERT pos/neg ratio + trajectory change |
| Relative Strength Alpha | Percentile rank on revenue growth, NPM, ROE within sector |

**Composite Alpha Score (CAS)**
```
CAS = 0.20·α₁ + 0.20·α₂ + 0.15·α₃ + 0.15·α₄ + 0.15·α₅ + 0.10·α₆ + 0.05·α₇ + 0.05·α₈
CAS ∈ [−100, +100]
```

**Inputs**
- All computed ratios, trend slopes, volatility scores from Module 3
- Sentiment scores from Module 4

**Outputs**
- 8 individual alpha scores per company (−100 to +100)
- One CAS per company
- Data Confidence Index (DCI) — penalises thin data/missing fields
- Quant-Sentiment Divergence flag (QSD) — flags when fundamentals and tone disagree

**Dependencies**
- Module 3 (needs quant signals)
- Module 4 (needs sentiment signals)

---

### Module 6 · RAG Query & LLM Synthesis Engine

**Responsibility**  
Answer user queries and generate analyst-grade written outputs by combining retrieved document evidence with pre-computed quantitative signals via an LLM.

**Two modes**:
- **Normal Mode**: Serves pre-computed alpha scores from the feature store. No live inference. Sub-2-second response.
- **Deep Mode**: Retrieves document chunks from the vector store, fuses with quant signals, sends to LLM for full synthesis. Async job, up to 4 minutes.

**Inputs**
- User query / research session context
- Top-5 retrieved document chunks from the vector store (Module 2)
- Pre-computed alpha scores, risk score, financial ratios from Module 5

**Outputs**
- Grounded analyst-style written response (every claim cites a source)
- Structured sections: financial analysis, risk diagnostic, guidance credibility, peer comparison
- Source citations: `doc_id`, `page_number`, `section_title` for each claim

**LLM Constraints** (hard guardrails)
- No price targets
- No buy/sell recommendations
- No portfolio allocation suggestions
- Refuse out-of-scope queries

**Dependencies**
- Module 2 (vector index must be built)
- Module 5 (needs alpha scores and risk data as LLM context)

---

### Module 7 · Universe Ranking & Dashboard API

**Responsibility**  
Rank all companies in the selected universe (e.g. NIFTY 50) by composite alpha score. Serve ranked data to the frontend. Enable filtering by sector, factor threshold, and sort order.

**Inputs**
- CAS and individual alpha scores for all companies from Module 5 (feature store)
- User filter/sort parameters (sector, score threshold, factor weight overrides)

**Outputs**
- Ranked league table: company, composite score, factor breakdown, universe rank
- Company signal card: quick view of scores, trends, risk level
- Exportable scorecard (JSON / CSV)

**Dependencies**
- Module 5 (must have CAS computed for all companies before ranking)

---

## Dependency Order (Build Sequence)

```
[1] Module 1 · Data Ingestion & Storage
        ↓
[2] Module 2 · Document Embedding & Vector Index     ←──┐
[3] Module 3 · Quantitative Signal Engine            ←──┤  (can run in parallel)
[4] Module 4 · Sentiment Analysis (NLP)              ←──┘
        ↓
[5] Module 5 · Alpha Signal Aggregator
        ↓
[6] Module 6 · RAG Query + LLM Synthesis    ← needs Module 2 + Module 5
[7] Module 7 · Universe Ranking + Dashboard API ← needs Module 5
```

**Correct build order:**  
`1 → 2 + 3 + 4 (parallel) → 5 → 6 + 7 (parallel)`

---

## What is Explicitly OUT of MVP Scope

| Excluded | Reason |
|---|---|
| Portfolio Optimisation (Markowitz, Black-Litterman) | Allocation — out of scope |
| Price Prediction (LSTM, ARIMA on stock prices) | Trading — out of scope |
| Trading Strategy Models | Trading — out of scope |
| CAPM / Beta Factor Model | Requires live price data pipeline; optional V1.5 |
| Random Forest / XGBoost classifier | Requires labelled training data; optional V1.5 |
| NLI Entailment Verifier (hallucination checker) | Optional V2.0 |
| Real-time market price streaming | Not needed for fundamental research MVP |
| PDF Report Generator | Polish layer — add after core pipeline works |

---

## Summary Table

| # | Module | Type | Depends On |
|---|---|---|---|
| 1 | Data Ingestion & Storage | Infrastructure | — |
| 2 | Document Embedding & Vector Index | RAG | 1 |
| 3 | Quantitative Signal Engine | Quant | 1 |
| 4 | Sentiment Analysis | NLP | 1 |
| 5 | Alpha Signal Aggregator | Signal Layer | 3, 4 |
| 6 | RAG Query + LLM Synthesis | Intelligence | 2, 5 |
| 7 | Universe Ranking + Dashboard API | Output/UI | 5 |
