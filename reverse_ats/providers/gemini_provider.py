"""
Google Gemini LLM Provider Plugin (Free Tier via Google AI Studio).
Uses the official `google-genai` SDK (>= 2.30.1) with `client.interactions.create`
and current models (`gemini-3.8-flash`, `gemini-4-argon`, `gemini-3.5-flash-lite`).
"""
import json
import os
import re
from typing import Dict, List, Optional
from google import genai
from reverse_ats.core import (
    LLMProviderPlugin,
    CandidateProfile,
    JobOfferInput,
    ReverseATSResult,
)
from reverse_ats.providers.prompts import (
    get_system_instruction,
    build_user_prompt,
    get_clean_json_schema,
)


def _extract_json_dict(raw_text: str) -> dict:
    """Safely parse JSON from model output even if wrapped in markdown fences."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


class GeminiProviderPlugin(LLMProviderPlugin):
    """Google Gemini API provider using the modern `google-genai` Interactions API."""

    @property
    def provider_id(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Google Gemini (Gratuit via Google AI Studio)"

    @property
    def available_models(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "gemini-3.8-flash",
                "label": "Gemini 3.8 Flash (Recommandé — Rapide, Gratuit & 1M tokens)",
            },
            {
                "id": "gemini-4-argon",
                "label": "Gemini 4 Argon (Modèle Pro / Raisonnement maximal — 1M tokens)",
            },
            {
                "id": "gemini-3.5-flash-lite",
                "label": "Gemini 3.5 Flash-Lite (Ultra-rapide & Quota gratuit maximum)",
            },
            {
                "id": "gemini-3.1-flash-lite",
                "label": "Gemini 3.1 Flash-Lite (Léger, haute fréquence & 100% gratuit)",
            },
            {
                "id": "gemma-4-31b-it",
                "label": "Gemma 4 31B Instruct (Open-Weights Google — Quota gratuit élevé)",
            },
            {
                "id": "gemma-4-26b-a4b-it",
                "label": "Gemma 4 26B MoE (Ultra-rapide — Quota gratuit illimité/élevé)",
            },
        ]

    @property
    def requires_api_key(self) -> bool:
        return True

    async def generate_tailored_application(
        self,
        profile: CandidateProfile,
        job_offer: JobOfferInput,
        api_key: Optional[str] = None,
    ) -> ReverseATSResult:
        resolved_key = (api_key or job_offer.api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        if not resolved_key:
            raise ValueError(
                "Clé API Gemini manquante. Créez-en une gratuitement en 10 secondes sur "
                "https://aistudio.google.com/apikey (sans carte bancaire) et collez-la dans Paramètres Clé API."
            )

        model_name = job_offer.model_name or "gemini-3.8-flash"
        # Guard against deprecated model strings
        if any(model_name.startswith(dep) for dep in ("gemini-2.5", "gemini-2.0", "gemini-1.5")):
            model_name = "gemini-3.8-flash"

        system_instruction = get_system_instruction(job_offer.language, job_offer.tone)
        user_prompt = build_user_prompt(profile, job_offer)
        schema = get_clean_json_schema()

        client = genai.Client(api_key=resolved_key)

        interaction = client.interactions.create(
            model=model_name,
            system_instruction=system_instruction,
            input=user_prompt,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": schema,
            },
        )

        output_text = interaction.output_text
        if not output_text:
            raise RuntimeError("Le modèle Gemini a renvoyé une réponse vide.")

        parsed = _extract_json_dict(output_text)
        result = ReverseATSResult(**parsed)
        result.provider_used = self.provider_id
        result.model_used = model_name
        return result
