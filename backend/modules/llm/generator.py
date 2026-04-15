"""
LLM Generator - Provider-agnostic interface for language models.
Supports OpenAI, Anthropic, and Ollama (local models).
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Iterator
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA    = "ollama"
    BEDROCK   = "bedrock"
    GEMINI    = "gemini"
    GROQ      = "groq"


@dataclass
class GenerationResult:
    """Standardized result from LLM generation."""
    text: str
    provider: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None


class LLMGenerator:
    """
    Provider-agnostic LLM generator.
    Handles OpenAI, Anthropic, and Ollama with a unified interface.
    """
    
    def __init__(self, provider: LLMProvider, api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key or self._get_api_key(provider)
        self._client = None
        self._initialize_client()
    
    def _get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key from environment."""
        key_map = {
            LLMProvider.OPENAI: "OPENAI_API_KEY",
            LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            LLMProvider.OLLAMA: None,  # No API key needed for local
        }
        env_var = key_map.get(provider)
        return os.getenv(env_var) if env_var else None
    
    def _initialize_client(self):
        """Initialize provider-specific client."""
        try:
            if self.provider == LLMProvider.OPENAI:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                self.default_model = "gpt-4"

            elif self.provider == LLMProvider.ANTHROPIC:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
                self.default_model = "claude-3-sonnet-20240229"

            elif self.provider == LLMProvider.OLLAMA:
                import requests
                self._client = requests.Session()
                self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
                self.default_model = "llama2"

            elif self.provider == LLMProvider.BEDROCK:
                import boto3
                region = os.getenv("AWS_REGION", "ap-south-1")
                self._client = boto3.client("bedrock-runtime", region_name=region)
                self.default_model = os.getenv(
                    "BEDROCK_MODEL_ID",
                    "anthropic.claude-3-sonnet-20240229-v1:0",
                )

            elif self.provider == LLMProvider.GEMINI:
                from google import genai as genai_sdk
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not set in environment")
                self._client = genai_sdk.Client(api_key=api_key)
                self.default_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

            elif self.provider == LLMProvider.GROQ:
                from groq import Groq
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    raise ValueError("GROQ_API_KEY not set in environment")
                self._client = Groq(api_key=api_key)
                self.default_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        except ImportError as e:
            logger.error(f"Failed to import {self.provider} client: {e}")
            self._client = None
            raise
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 32768,
        stream: bool = False,
        **kwargs
    ) -> GenerationResult:
        """
        Generate text using the configured provider.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (not supported by all providers)
            model: Model name (uses default if None)
            temperature: Creativity control (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Provider-specific arguments
            
        Returns:
            GenerationResult with text and metadata
        """
        model = model or self.default_model
        history = kwargs.pop("history", [])   # list of (role, content) tuples

        if self.provider == LLMProvider.OPENAI:
            return self._generate_openai(prompt, system_prompt, model, temperature, max_tokens, stream, **kwargs)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, system_prompt, model, temperature, max_tokens, stream, **kwargs)
        elif self.provider == LLMProvider.OLLAMA:
            return self._generate_ollama(prompt, system_prompt, model, temperature, max_tokens, stream, **kwargs)
        elif self.provider == LLMProvider.BEDROCK:
            return self._generate_bedrock(prompt, system_prompt, model, temperature, max_tokens, **kwargs)
        elif self.provider == LLMProvider.GEMINI:
            return self._generate_gemini(prompt, system_prompt, model, temperature, max_tokens, history=history, **kwargs)
        elif self.provider == LLMProvider.GROQ:
            return self._generate_groq(prompt, system_prompt, model, temperature, max_tokens, history=history, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> GenerationResult:
        """Generate using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        
        if stream:
            # Handle streaming response
            text = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    text += chunk.choices[0].delta.content
            usage = {}
            finish_reason = "stop"
        else:
            text = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
            finish_reason = response.choices[0].finish_reason
        
        return GenerationResult(
            text=text,
            provider="openai",
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            raw_response=response if not stream else None,
        )
    
    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> GenerationResult:
        """Generate using Anthropic Claude."""
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return GenerationResult(
            text=response.content[0].text,
            provider="anthropic",
            model=model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
            raw_response=response,
        )
    
    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> GenerationResult:
        """Generate using Ollama (local)."""
        import requests
        
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if stream:
            response = requests.post(url, json=payload, stream=True)
            text = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    text += data.get("response", "")
                    if data.get("done"):
                        break
            usage = {}
        else:
            response = requests.post(url, json=payload)
            data = response.json()
            text = data.get("response", "")
            usage = {
                "prompt_eval_count": data.get("prompt_eval_count", 0),
                "eval_count": data.get("eval_count", 0),
            }
        
        return GenerationResult(
            text=text,
            provider="ollama",
            model=model,
            usage=usage,
            finish_reason="stop",
        )

    def _generate_bedrock(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> GenerationResult:
        """Generate using AWS Bedrock (Anthropic Claude via boto3)."""
        import json as _json

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if system_prompt:
            body["system"] = system_prompt

        response = self._client.invoke_model(
            body=_json.dumps(body),
            modelId=model,
            accept="application/json",
            contentType="application/json",
        )

        result = _json.loads(response["body"].read())
        text = result["content"][0]["text"]
        usage = result.get("usage", {})

        return GenerationResult(
            text=text,
            provider="bedrock",
            model=model,
            usage={
                "input_tokens":  usage.get("input_tokens",  0),
                "output_tokens": usage.get("output_tokens", 0),
            },
            finish_reason=result.get("stop_reason", "end_turn"),
            raw_response=result,
        )

    def _generate_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
        history: list | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate using Google Gemini via new google-genai SDK (v1.x).
        
        Supports multi-turn conversation via the `history` parameter.
        history: list of (role, content) tuples — role is 'user' or 'assistant'.
        """
        from google.genai import types as genai_types

        config_kwargs: dict = {
            "temperature":       temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        config = genai_types.GenerateContentConfig(**config_kwargs)

        # ── Build multi-turn contents ─────────────────────────────────────────
        # Gemini uses role='user' | 'model' (not 'assistant')
        contents: list = []
        for role, content in (history or []):
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(
                genai_types.Content(
                    role=gemini_role,
                    parts=[genai_types.Part(text=content)],
                )
            )
        # Append the current (context-enriched) user turn
        contents.append(
            genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=prompt)],
            )
        )

        response = self._client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        text = response.text
        usage_meta = getattr(response, "usage_metadata", None)
        usage = {}
        if usage_meta:
            usage = {
                "prompt_token_count":     getattr(usage_meta, "prompt_token_count",     0),
                "candidates_token_count": getattr(usage_meta, "candidates_token_count", 0),
                "total_token_count":      getattr(usage_meta, "total_token_count",      0),
            }

        return GenerationResult(
            text=text,
            provider="gemini",
            model=model,
            usage=usage,
            finish_reason="stop",
            raw_response=response,
        )


    def _generate_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        model: str,
        temperature: float,
        max_tokens: int,
        history: list | None = None,
        **kwargs,
    ) -> GenerationResult:
        """Generate using Groq (OpenAI-compatible, blazing fast inference)."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        # Inject multi-turn history
        for role, content in (history or []):
            groq_role = "assistant" if role == "assistant" else "user"
            messages.append({"role": groq_role, "content": content})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        text = response.choices[0].message.content
        usage = {
            "prompt_tokens":     response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens":      response.usage.total_tokens,
        }
        return GenerationResult(
            text=text,
            provider="groq",
            model=model,
            usage=usage,
            finish_reason=response.choices[0].finish_reason,
            raw_response=response,
        )


    def generate_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.
        
        Args:
            prompt: User prompt
            output_schema: JSON schema for expected output
            system_prompt: System prompt
            model: Model name
            
        Returns:
            Parsed JSON response
        """
        # Add schema instructions to prompt
        schema_instruction = f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(output_schema, indent=2)}"
        full_prompt = prompt + schema_instruction
        
        result = self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=0.1,  # Lower temperature for structured output
            **kwargs
        )
        
        # Parse JSON from response
        try:
            # Try to extract JSON from response (handles markdown code blocks)
            text = result.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Failed to parse JSON", "raw_text": result.text}


# ── SINGLETON GENERATORS ─────────────────────────────────────────────────────

_generators: Dict[LLMProvider, Optional[LLMGenerator]] = {}


def get_generator(provider: LLMProvider) -> LLMGenerator:
    """
    Get or create a generator for the specified provider.
    Generators are cached for reuse.
    """
    if provider not in _generators:
        try:
            _generators[provider] = LLMGenerator(provider)
        except Exception as e:
            logger.error(f"Failed to initialize {provider} generator: {e}")
            _generators[provider] = None
            raise
    
    generator = _generators[provider]
    if generator is None:
        raise RuntimeError(f"{provider} generator failed to initialize")
    
    return generator


def generate_text(
    provider: LLMProvider,
    prompt: str,
    system_prompt: Optional[str] = None,
    **kwargs
) -> GenerationResult:
    """Convenience function for one-off text generation."""
    generator = get_generator(provider)
    return generator.generate(prompt=prompt, system_prompt=system_prompt, **kwargs)


def generate_structured(
    provider: LLMProvider,
    prompt: str,
    output_schema: Dict[str, Any],
    system_prompt: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for structured generation."""
    generator = get_generator(provider)
    return generator.generate_structured(
        prompt=prompt,
        output_schema=output_schema,
        system_prompt=system_prompt,
        **kwargs
    )