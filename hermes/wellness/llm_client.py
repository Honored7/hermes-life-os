"""
Multi-provider LLM client for the Hermes Wellness Wizard.

Supports:
- Ollama (local, free, private) — DEFAULT
- OpenAI (cloud, requires API key)
- Anthropic (cloud, requires API key)

Auto-detects available providers. Falls back to None (template mode)
if no LLM is available.

Usage:
    client = LLMClient()                    # Auto-detect
    client = LLMClient(provider="ollama")   # Force Ollama
    client = LLMClient(provider="openai")   # Force OpenAI

    response = client.generate(
        system="You are a wise wizard...",
        prompt="The user is stressed...",
    )
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from typing import Optional


class LLMClient:
    """Unified LLM client with multi-provider support."""

    def __init__(
        self,
        provider: str = "auto",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 512,
        timeout: int = 60,
    ):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        if provider == "auto":
            provider, model, api_key, base_url = self._auto_detect(model, api_key, base_url)

        self.provider = provider
        self.model = model or self._default_model(provider)
        self.api_key = api_key
        self.base_url = base_url
        if self.provider == "ollama" and not self.base_url:
            self.base_url = "http://localhost:11434"  

    # ─── Auto-Detection ───────────────────────────────────────────────

    def _auto_detect(self, model, api_key, base_url):
        """Detect the best available LLM provider."""
        # 1. Check Ollama (local, preferred for privacy)
        ollama_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        if self._ollama_available(ollama_url):
            return "ollama", model or os.environ.get("OLLAMA_MODEL", "qwen3.5:9b"), None, ollama_url

        # 2. Check OpenAI
        openai_key = api_key or os.environ.get("OPENAI_API_KEY")
        if openai_key:
            return "openai", model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), openai_key, None

        # 3. Check Anthropic
        anthropic_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if anthropic_key:
            return "anthropic", model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), anthropic_key, None

        # 4. No LLM available
        return "none", None, None, None

    def _ollama_available(self, base_url: str) -> bool:
        """Check if Ollama is running."""
        try:
            req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _default_model(self, provider: str) -> Optional[str]:
        defaults = {
            "ollama": "qwen3.5:9b",
            "openai": "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-20250514",
        }
        return defaults.get(provider)

    # ─── Generation ───────────────────────────────────────────────────

    def generate(
        self,
        system: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """
        Generate a response from the LLM.

        Args:
            system: System prompt (wizard personality)
            prompt: User prompt (context + instructions)
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated text, or None if LLM is unavailable
        """
        if self.provider == "none":
            return None

        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            if self.provider == "ollama":
                return self._generate_ollama(system, prompt, temp, tokens)
            elif self.provider == "openai":
                return self._generate_openai(system, prompt, temp, tokens)
            elif self.provider == "anthropic":
                return self._generate_anthropic(system, prompt, temp, tokens)
        except Exception as e:
            print(f"[LLM] {self.provider} error: {e}")
            return None

        return None

    async def agenerate(
        self,
        system: str,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Optional[str]:
        """Async version of generate()."""
        if self.provider == "none":
            return None

        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        try:
            if self.provider == "ollama":
                return await self._agenerate_ollama(system, prompt, temp, tokens)
            elif self.provider == "openai":
                return self._generate_openai(system, prompt, temp, tokens)
            elif self.provider == "anthropic":
                return self._generate_anthropic(system, prompt, temp, tokens)
        except Exception as e:
            print(f"[LLM] {self.provider} async error: {e}")
            return None

        return None

    # ─── Ollama ───────────────────────────────────────────────────────

    def _generate_ollama(self, system: str, prompt: str, temp: float, tokens: int) -> Optional[str]:
        """Generate via Ollama (sync, using urllib — zero dependencies)."""
        url = f"{self.base_url}/api/chat"
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {
                "temperature": temp,
                "num_predict": tokens,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "").strip()

    async def _agenerate_ollama(self, system: str, prompt: str, temp: float, tokens: int) -> Optional[str]:
        """Generate via Ollama (async, using httpx)."""
        import httpx

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        "think": False,
            "options": {
                "temperature": temp,
                "num_predict": tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()

    # ─── OpenAI ───────────────────────────────────────────────────────

    def _generate_openai(self, system: str, prompt: str, temp: float, tokens: int) -> Optional[str]:
        """Generate via OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            print("[LLM] openai package not installed. Run: pip install openai")
            return None

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temp,
            max_tokens=tokens,
        )
        return response.choices[0].message.content.strip()

    # ─── Anthropic ────────────────────────────────────────────────────

    def _generate_anthropic(self, system: str, prompt: str, temp: float, tokens: int) -> Optional[str]:
        """Generate via Anthropic API."""
        try:
            import anthropic
        except ImportError:
            print("[LLM] anthropic package not installed. Run: pip install anthropic")
            return None

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=tokens,
            system=system,
            messages=[
                {"role": "user", "content": prompt},
            ],
            temperature=temp,
        )
        return response.content[0].text.strip()

    # ─── Status ───────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return the current LLM configuration status."""
        return {
            "provider": self.provider,
            "model": self.model,
            "available": self.provider != "none",
            "base_url": self.base_url if self.provider == "ollama" else None,
        }
