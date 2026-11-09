"""
LLM Provider Registry (Pluggable Factory).
To add a new AI provider tomorrow (e.g., Anthropic, OpenAI, Mistral), create a class implementing
`LLMProviderPlugin` and register it in `create_default_provider_registry()`.
"""
from typing import Dict, List, Any
from reverse_ats.core import LLMProviderPlugin
from reverse_ats.providers.gemini_provider import GeminiProviderPlugin
from reverse_ats.providers.other_providers import (
    GroqProviderPlugin,
    OllamaProviderPlugin,
    ManualPromptProviderPlugin,
)


class ProviderRegistry:
    """Registry of all pluggable AI providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, LLMProviderPlugin] = {}

    def register(self, provider: LLMProviderPlugin) -> None:
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> LLMProviderPlugin:
        if provider_id not in self._providers:
            raise KeyError(
                f"Fournisseur IA '{provider_id}' non enregistré. "
                f"Disponibles : {', '.join(self._providers.keys())}"
            )
        return self._providers[provider_id]

    def list_providers_metadata(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": p.provider_id,
                "name": p.display_name,
                "requires_api_key": p.requires_api_key,
                "models": p.available_models,
            }
            for p in self._providers.values()
        ]


def create_default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(GeminiProviderPlugin())
    registry.register(GroqProviderPlugin())
    registry.register(OllamaProviderPlugin())
    registry.register(ManualPromptProviderPlugin())
    return registry
