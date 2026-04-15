"""
Prompt Builder - Template system for LLM prompts.
Pure functions for building consistent, type-safe prompts.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class PromptRole(str, Enum):
    """Prompt message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class PromptTemplate:
    """Template for building prompts with variable substitution."""
    template: str
    required_vars: List[str] = None
    optional_vars: List[str] = None
    
    def __post_init__(self):
        self.required_vars = self.required_vars or []
        self.optional_vars = self.optional_vars or []
    
    def render(self, variables: Dict[str, Any]) -> str:
        """
        Render template with variables.
        Uses {{variable}} syntax.
        """
        # Validate required variables
        missing = [v for v in self.required_vars if v not in variables]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        
        # Render template
        result = self.template
        all_vars = self.required_vars + self.optional_vars
        
        for var in all_vars:
            if var in variables:
                placeholder = f"{{{{{var}}}}}"
                value = variables[var]
                
                # Format lists nicely
                if isinstance(value, list):
                    value = "\n".join(f"- {item}" for item in value)
                # Format dicts as JSON-like
                elif isinstance(value, dict):
                    import json
                    value = json.dumps(value, indent=2)
                
                result = result.replace(placeholder, str(value))
        
        return result


# ── SYSTEM PROMPTS ───────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "financial_analyst": """You are an expert financial analyst with deep knowledge of equity research, quantitative analysis, and financial statement interpretation.

Guidelines:
- Provide factual, data-driven analysis
- Use clear, professional language
- Cite specific metrics when available
- Highlight both strengths and risks
- Avoid speculative statements
- Maintain objectivity and balance

When analyzing companies:
1. Start with key takeaways
2. Support with quantitative evidence
3. Discuss risks and uncertainties
4. Provide actionable insights

Do not provide investment advice. Present information for educational purposes only.""",

    "sentiment_analyzer": """You are a financial sentiment analysis specialist. Analyze text for market sentiment, management tone, and forward-looking statements.

Focus on:
- Positive/negative/neutral sentiment classification
- Confidence level in assessments
- Key phrases indicating sentiment
- Management's forward guidance tone
- Risk language and hedging statements

Provide structured analysis with sentiment scores from -1.0 (very negative) to 1.0 (very positive).""",

    "quant_interpreter": """You are a quantitative finance specialist who translates complex metrics into clear, actionable insights.

Expertise:
- Interpreting financial ratios
- Analyzing price trends and momentum
- Assessing volatility and risk metrics
- Connecting quantitative signals to business fundamentals

Provide interpretations that are:
1. Data-driven and precise
2. Contextualized within industry norms
3. Balanced between positive and cautionary signals
4. Accessible to non-quantitative audiences""",
}


def build_system_prompt(role: str, custom_instructions: Optional[str] = None) -> str:
    """
    Build a system prompt for a specific role.
    
    Args:
        role: Predefined role key
        custom_instructions: Additional instructions to append
        
    Returns:
        System prompt string
    """
    base_prompt = SYSTEM_PROMPTS.get(role, "")
    if custom_instructions:
        base_prompt = f"{base_prompt}\n\n{custom_instructions}"
    return base_prompt


def build_prompt(
    template: PromptTemplate,
    variables: Dict[str, Any],
    system_prompt: Optional[str] = None,
) -> Dict[str, str]:
    """
    Build a complete prompt with optional system prompt.
    
    Returns:
        Dict with 'system' and 'user' keys (system may be None)
    """
    return {
        "system": system_prompt,
        "user": template.render(variables),
    }


def build_financial_prompt(
    template: PromptTemplate,
    context: Dict[str, Any],
    include_system: bool = True,
) -> str:
    """
    Build a financial analysis prompt with context.
    
    Args:
        template: Prompt template
        context: Variables for template
        include_system: Whether to include system prompt
        
    Returns:
        Rendered prompt string
    """
    return template.render(context)


# ── COMMON PROMPT TEMPLATES ───────────────────────────────────────────────────

BASIC_ANALYSIS_TEMPLATE = PromptTemplate(
    template="""Analyze the following information about {{company_name}}:

Company: {{company_name}}
Sector: {{sector}}
Period: {{period}}

{{context}}

Provide a concise analysis covering:
1. Key observations
2. Notable trends
3. Potential implications""",
    required_vars=["company_name"],
    optional_vars=["sector", "period", "context"],
)

COMPARISON_TEMPLATE = PromptTemplate(
    template="""Compare the following companies based on the provided metrics:

{{companies}}

Key Metrics:
{{metrics}}

Provide a comparative analysis including:
1. Relative strengths and weaknesses
2. Notable differences in metrics
3. Sector positioning""",
    required_vars=["companies", "metrics"],
)