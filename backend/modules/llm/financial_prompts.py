"""
Financial Prompts - Domain-specific templates for financial analysis.
"""

from .prompt_builder import PromptTemplate


# ── COMPANY ANALYSIS PROMPTS ─────────────────────────────────────────────────

COMPANY_SUMMARY_TEMPLATE = PromptTemplate(
    template="""Provide a comprehensive summary for {{company_id}} based on the following information:

Company: {{company_id}}
Sector: {{sector}}
Quantitative Profile: {{quant_profile}}

Document Context:
{{document_context}}

Include in your analysis:
1. Business Overview - What does the company do?
2. Financial Health - Key strengths and concerns from the metrics
3. Market Position - Competitive standing in the sector
4. Key Risks - Major risk factors identified
5. Outlook - Summary assessment based on available data

Be specific and reference actual metrics when available.""",
    required_vars=["company_id"],
    optional_vars=["sector", "quant_profile", "document_context"],
)


EARNINGS_ANALYSIS_TEMPLATE = PromptTemplate(
    template="""Analyze the earnings information for {{company_id}}:

Period: {{period}}
Financial Metrics:
{{financial_metrics}}

Earnings Context:
{{earnings_context}}

Provide analysis covering:
1. Revenue Performance - Growth trends and drivers
2. Profitability - Margin analysis and efficiency
3. Key Takeaways - Most important developments
4. Forward Indicators - What metrics suggest about future performance
5. Sentiment Assessment - Overall tone of the earnings information""",
    required_vars=["company_id"],
    optional_vars=["period", "financial_metrics", "earnings_context"],
)


RISK_ASSESSMENT_TEMPLATE = PromptTemplate(
    template="""Assess the risk profile for {{company_id}}:

Quantitative Risk Metrics:
{{risk_profile}}

Volatility Analysis:
{{volatility_profile}}

Document Risk Factors:
{{document_risks}}

Provide a structured risk assessment:
1. Overall Risk Level (Low/Medium/High) with justification
2. Top 3 Risk Factors - Ranked by severity
3. Quantitative Risk Signals - What the metrics indicate
4. Qualitative Risk Factors - From document analysis
5. Mitigating Factors - Any offsetting positive signals
6. Risk Trend - Is risk increasing, stable, or decreasing?""",
    required_vars=["company_id"],
    optional_vars=["risk_profile", "volatility_profile", "document_risks"],
)


SENTIMENT_ANALYSIS_TEMPLATE = PromptTemplate(
    template="""Analyze the sentiment in the following text regarding {{company_id}}:

Text to analyze:
{{text}}

Additional context:
{{context}}

Provide sentiment analysis with:
1. Overall Sentiment (Positive/Neutral/Negative)
2. Sentiment Score (-1.0 to 1.0)
3. Confidence Level (0-100%)
4. Key Positive Phrases
5. Key Negative Phrases
6. Management Tone Assessment
7. Forward-Looking Statement Analysis""",
    required_vars=["text"],
    optional_vars=["company_id", "context"],
)


QUANT_INTERPRETATION_TEMPLATE = PromptTemplate(
    template="""Interpret the following quantitative metrics for {{company_id}}:

Financial Ratios:
{{ratios}}

Price Trends:
{{trends}}

Volatility Metrics:
{{volatility}}

Risk Assessment:
{{risk}}

Provide an interpretation that:
1. Summarizes the overall quantitative picture in plain language
2. Highlights the most significant signals (both positive and concerning)
3. Puts metrics in context of typical ranges for the sector
4. Identifies any conflicting signals between different metrics
5. Suggests what an analyst should focus on when reviewing this company

Avoid simply restating numbers. Focus on what the numbers mean.""",
    required_vars=["company_id"],
    optional_vars=["ratios", "trends", "volatility", "risk"],
)


# ── SECTOR ANALYSIS PROMPTS ───────────────────────────────────────────────────

SECTOR_COMPARISON_TEMPLATE = PromptTemplate(
    template="""Compare {{company_id}} to its sector peers:

Sector: {{sector}}
Company Metrics: {{company_metrics}}
Sector Averages: {{sector_averages}}
Peer Metrics: {{peer_metrics}}

Provide comparison covering:
1. Relative Positioning - How does it compare to sector averages?
2. Competitive Advantages - Where does it outperform?
3. Competitive Weaknesses - Where does it lag?
4. Peer Group Analysis - Comparison to specific peers
5. Sector Outlook - How is the company positioned for sector trends?""",
    required_vars=["company_id", "sector"],
    optional_vars=["company_metrics", "sector_averages", "peer_metrics"],
)


# ── RAG ENHANCEMENT PROMPTS ───────────────────────────────────────────────────

DOCUMENT_QA_TEMPLATE = PromptTemplate(
    template="""Answer the following question based on the provided document context:

Question: {{question}}

Document Context:
{{context}}

Instructions:
- Only use information from the provided context
- If the context doesn't contain the answer, say "The provided documents do not contain this information"
- Cite specific sections or page numbers when available
- Provide direct quotes where relevant""",
    required_vars=["question", "context"],
)


EXTRACT_FINANCIAL_METRICS_TEMPLATE = PromptTemplate(
    template="""Extract financial metrics from the following document text:

Document Text:
{{text}}

Extract the following metrics if present:
- Revenue/Income
- Net Profit/Income
- EBITDA
- Operating Margin
- Net Margin
- EPS (Earnings Per Share)
- P/E Ratio
- Debt to Equity
- ROE (Return on Equity)
- ROA (Return on Assets)
- Free Cash Flow
- Any guidance or forward-looking numbers

Return as JSON with metric names as keys and objects containing:
- "value": the numeric value
- "unit": "millions", "billions", "percentage", etc.
- "period": the time period (e.g., "Q3 2024", "FY 2023")
- "context": brief context about the metric

Only include metrics that are explicitly stated.""",
    required_vars=["text"],
)