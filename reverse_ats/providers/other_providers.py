"""
Additional Pluggable AI Providers:
1. GroqProviderPlugin: Free high-speed API for Llama 3.3 70B via OpenAI-compatible HTTP endpoint.
2. OllamaProviderPlugin: 100% local & offline LLM execution via local Ollama server.
3. PromptGeneratorFallbackPlugin: Zero-API mode that builds the complete ready-to-paste prompt
   and can also import a JSON response pasted by the user.
"""
import json
import os
import re
from typing import Dict, List, Optional
import httpx
from reverse_ats.core import (
    LLMProviderPlugin,
    CandidateProfile,
    JobOfferInput,
    ReverseATSResult,
    ATSAnalysis,
    TailoredCV,
    TailoredCoverLetter,
)
from reverse_ats.providers.prompts import (
    get_system_instruction,
    build_user_prompt,
    get_clean_json_schema,
)


def _extract_json_dict(raw_text: str) -> dict:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


class GroqProviderPlugin(LLMProviderPlugin):
    """Groq Cloud Free API Provider (OpenAI-compatible REST call, zero extra SDK required)."""

    @property
    def provider_id(self) -> str:
        return "groq"

    @property
    def display_name(self) -> str:
        return "Groq Cloud (Gratuit — Llama 3.3 70B)"

    @property
    def available_models(self) -> List[Dict[str, str]]:
        return [
            {"id": "llama-3.3-70b-versatile", "label": "Llama 3.3 70B Versatile (Gratuit & Rapide)"},
            {"id": "llama-3.1-8b-instant", "label": "Llama 3.1 8B Instant"},
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
        resolved_key = (api_key or job_offer.api_key or os.getenv("GROQ_API_KEY", "")).strip()
        if not resolved_key:
            raise ValueError(
                "Clé API Groq manquante. Créez-en une gratuitement sur https://console.groq.com/keys"
            )

        model_name = job_offer.model_name or "llama-3.3-70b-versatile"
        schema_str = json.dumps(get_clean_json_schema(), ensure_ascii=False)
        system_instruction = (
            get_system_instruction(job_offer.language, job_offer.tone)
            + f"\n\nSCHÉMA JSON OBLIGATOIRE :\n{schema_str}"
        )
        user_prompt = build_user_prompt(profile, job_offer)

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {resolved_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"]
        parsed = _extract_json_dict(content)
        result = ReverseATSResult(**parsed)
        result.provider_used = self.provider_id
        result.model_used = model_name
        return result


class OllamaProviderPlugin(LLMProviderPlugin):
    """100% Local & Offline Ollama Provider."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        return "Ollama Local (100% Hors-Ligne sur votre PC)"

    @property
    def available_models(self) -> List[Dict[str, str]]:
        return [
            {"id": "qwen2.5:14b", "label": "Qwen 2.5 14B (Local)"},
            {"id": "llama3.2:latest", "label": "Llama 3.2 (Local)"},
            {"id": "mistral:latest", "label": "Mistral 7B (Local)"},
        ]

    @property
    def requires_api_key(self) -> bool:
        return False

    async def generate_tailored_application(
        self,
        profile: CandidateProfile,
        job_offer: JobOfferInput,
        api_key: Optional[str] = None,
    ) -> ReverseATSResult:
        model_name = job_offer.model_name or "llama3.2:latest"
        system_instruction = get_system_instruction(job_offer.language, job_offer.tone)
        user_prompt = build_user_prompt(profile, job_offer)

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                    "format": get_clean_json_schema(),
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        content = data["message"]["content"]
        parsed = _extract_json_dict(content)
        result = ReverseATSResult(**parsed)
        result.provider_used = self.provider_id
        result.model_used = model_name
        return result


class ManualPromptProviderPlugin(LLMProviderPlugin):
    """
    Zero-API fallback mode: generates the exact structured prompt so the user can copy-paste it
    into any free web chat (ChatGPT, Claude, Gemini Web) or preview a smart template immediately.
    """

    @property
    def provider_id(self) -> str:
        return "manual_prompt"

    @property
    def display_name(self) -> str:
        return "Mode Sans Clé API (Générateur de Prompt + Maquette Éditable)"

    @property
    def available_models(self) -> List[Dict[str, str]]:
        return [
            {
                "id": "interactive_mock_and_prompt",
                "label": "Générer le Prompt Complet + Pré-remplir le CV A4 Éditable",
            }
        ]

    @property
    def requires_api_key(self) -> bool:
        return False

    async def generate_tailored_application(
        self,
        profile: CandidateProfile,
        job_offer: JobOfferInput,
        api_key: Optional[str] = None,
    ) -> ReverseATSResult:
        system_instruction = get_system_instruction(job_offer.language, job_offer.tone)
        user_prompt = build_user_prompt(profile, job_offer)
        schema_str = json.dumps(get_clean_json_schema(), indent=2, ensure_ascii=False)
        full_copyable_prompt = (
            f"{system_instruction}\n\n{user_prompt}\n\n"
            f"SCHÉMA JSON ATTENDU :\n```json\n{schema_str}\n```"
        )

        # Build an intelligent pre-filled template from the user's profile so they can also edit directly
        result = ReverseATSResult(
            ats_analysis=ATSAnalysis(
                match_score=85,
                matched_keywords=["Mode Sans Clé API Activé", "Édition Directe A4", "Prompt Prêt à Copier"],
                missing_or_weak_keywords=[],
                tailoring_strategy=[
                    "Vous avez utilisé le mode 'Sans Clé API'.",
                    "Vous pouvez soit éditer directement le CV et la Lettre A4 ci-dessous en cliquant sur n'importe quel texte, soit copier le Prompt complet généré pour le coller dans ChatGPT/Claude/Gemini Web puis importer le JSON obtenu.",
                ],
            ),
            cv=TailoredCV(
                full_name=profile.full_name or "Votre Nom Prénom",
                target_title=profile.title or "Titre du Poste Visé",
                email=profile.email or "email@exemple.com",
                phone=profile.phone or "+33 6 00 00 00 00",
                location=profile.location or "Paris, France",
                links=profile.links or ["linkedin.com/in/profil", "github.com/profil"],
                executive_summary=(
                    profile.master_bio[:350] + "..."
                    if len(profile.master_bio) > 350
                    else (
                        profile.master_bio
                        or "Cliquez ici pour éditer votre résumé exécutif adapté à l'offre d'emploi."
                    )
                ),
                skill_categories=[
                    {"category": "Compétences Clés", "skills": ["Python", "Architecture Modulaire", "API REST", "Gestion de Projet"]},
                    {"category": "Outils & Méthodes", "skills": ["Git", "Docker", "CI/CD", "Agile / Scrum"]},
                ],
                experiences=[
                    {
                        "role": profile.title or "Expérience Principale (Cliquez pour modifier)",
                        "company": "Entreprise",
                        "period": "2023 - Présent",
                        "location": profile.location or "France",
                        "highlights": [
                            "Cliquez directement sur ce texte dans l'aperçu A4 pour modifier vos réalisations.",
                            "Ajoutez votre clé API Google AI Studio gratuite pour que Gemini génère automatiquement tout le CV et la lettre sur-mesure.",
                        ],
                    }
                ],
                projects=[
                    {
                        "name": "Projet Phare",
                        "tech_stack": "Python, FastAPI, IA",
                        "period": "2026",
                        "description": "Conception d'une architecture modulaire orientée plugins.",
                        "link": "",
                    }
                ],
                education=[
                    {
                        "degree": "Diplôme / Formation",
                        "institution": "École / Université",
                        "period": "2020 - 2023",
                        "details": "Spécialisation Informatique & Ingénierie",
                    }
                ],
                languages=["Français (Natif)", "Anglais (Professionnel)"],
                certifications_or_extras=[],
            ),
            cover_letter=TailoredCoverLetter(
                recipient_company="Entreprise Cible",
                recipient_role=profile.title or "Poste Visé",
                date_location=f"{profile.location or 'Paris'}, le 30 octobre 2026",
                subject=f"Candidature au poste de {profile.title or 'Développeur'}",
                salutation="Madame, Monsieur,",
                opening_paragraph=(
                    "Votre offre d'emploi a immédiatement retenu mon attention. "
                    "Cliquez directement sur n'importe quel paragraphe de cette feuille A4 pour personnaliser le texte."
                ),
                body_paragraphs=[
                    "Mon parcours et mes projets détaillés dans mon profil démontrent ma capacité à répondre rapidement aux enjeux techniques et opérationnels de votre équipe.",
                    "Rigoureux et autonome, je conçois des solutions maintenables, modulaires et orientées résultats.",
                ],
                closing_paragraph=(
                    "Je serais ravi d'échanger avec vous lors d'un entretien afin de vous présenter plus en détail mes réalisations."
                ),
                sign_off="Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
                signature_name=profile.full_name or "Votre Nom Prénom",
            ),
            provider_used=self.provider_id,
            model_used="interactive_mock_and_prompt",
            fallback_prompt=full_copyable_prompt,
        )
        return result
