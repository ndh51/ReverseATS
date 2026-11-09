"""
Service Orchestrator.
Depends ONLY on the abstract registries (`ParserRegistry`, `ScraperRegistry`, `ProviderRegistry`, `StorageBackendPlugin`).
Zero direct dependency on any concrete parser, scraper, database, or AI SDK.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List
from reverse_ats.core import (
    CandidateProfile,
    UploadedCV,
    JobOfferInput,
    ReverseATSResult,
    StorageBackendPlugin,
)
from reverse_ats.parsers import ParserRegistry
from reverse_ats.scrapers import ScraperRegistry
from reverse_ats.providers import ProviderRegistry


class ReverseATSService:
    """Application facade orchestrating the pluggable modules."""

    def __init__(
        self,
        parser_registry: ParserRegistry,
        scraper_registry: ScraperRegistry,
        provider_registry: ProviderRegistry,
        storage: StorageBackendPlugin,
    ) -> None:
        self.parsers = parser_registry
        self.scrapers = scraper_registry
        self.providers = provider_registry
        self.storage = storage

    # --- Profile & CVs ---

    def get_profile(self) -> CandidateProfile:
        return self.storage.load_profile()

    def update_profile(self, profile: CandidateProfile) -> CandidateProfile:
        return self.storage.save_profile(profile)

    def upload_cv_file(self, file_bytes: bytes, filename: str) -> CandidateProfile:
        extracted_text = self.parsers.parse(file_bytes, filename)
        if not extracted_text:
            raise ValueError(f"Aucun texte lisible n'a pu être extrait de '{filename}'.")

        profile = self.storage.load_profile()
        new_cv = UploadedCV(
            id=uuid.uuid4().hex[:10],
            filename=filename,
            extracted_text=extracted_text,
            uploaded_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )
        profile.uploaded_cvs.append(new_cv)
        return self.storage.save_profile(profile)

    def delete_cv_file(self, cv_id: str) -> CandidateProfile:
        profile = self.storage.load_profile()
        profile.uploaded_cvs = [cv for cv in profile.uploaded_cvs if cv.id != cv_id]
        return self.storage.save_profile(profile)

    # --- Job Offer Scraping ---

    async def extract_job_from_url(self, url: str) -> str:
        return await self.scrapers.scrape_url(url)

    # --- Settings & Providers ---

    def get_providers_and_settings(self) -> Dict[str, Any]:
        settings = self.storage.load_settings()
        return {
            "providers": self.providers.list_providers_metadata(),
            "supported_cv_extensions": self.parsers.supported_extensions(),
            "settings": {
                "default_provider": settings.get("default_provider", "gemini"),
                "default_model": settings.get("default_model", "gemini-3.8-flash"),
                "has_gemini_key": bool(settings.get("gemini_api_key")),
                "has_groq_key": bool(settings.get("groq_api_key")),
                "gemini_key_preview": (
                    settings["gemini_api_key"][:6] + "..." + settings["gemini_api_key"][-4:]
                    if len(settings.get("gemini_api_key", "")) > 10
                    else ""
                ),
                "groq_key_preview": (
                    settings["groq_api_key"][:6] + "..." + settings["groq_api_key"][-4:]
                    if len(settings.get("groq_api_key", "")) > 10
                    else ""
                ),
                "ollama_base_url": settings.get("ollama_base_url", "http://localhost:11434"),
            },
        }

    def save_settings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        updates: Dict[str, Any] = {}
        if "gemini_api_key" in payload and payload["gemini_api_key"] is not None:
            updates["gemini_api_key"] = payload["gemini_api_key"].strip()
        if "groq_api_key" in payload and payload["groq_api_key"] is not None:
            updates["groq_api_key"] = payload["groq_api_key"].strip()
        if "ollama_base_url" in payload and payload["ollama_base_url"]:
            updates["ollama_base_url"] = payload["ollama_base_url"].strip()
        if "default_provider" in payload:
            updates["default_provider"] = payload["default_provider"]
        if "default_model" in payload:
            updates["default_model"] = payload["default_model"]
        self.storage.save_settings(updates)
        return self.get_providers_and_settings()

    # --- Tailoring Generation ---

    async def generate_application(self, job_input: JobOfferInput) -> Dict[str, Any]:
        profile = self.storage.load_profile()
        settings = self.storage.load_settings()

        # If URL provided and raw_text is empty, scrape automatically
        if job_input.source_url and not job_input.raw_text.strip():
            job_input.raw_text = await self.scrapers.scrape_url(job_input.source_url)

        if not job_input.raw_text.strip():
            raise ValueError("Veuillez fournir le texte de l'offre d'emploi ou un lien URL valide.")

        provider = self.providers.get(job_input.provider_id)

        # Resolve API key from input or stored settings
        api_key = job_input.api_key
        if not api_key:
            if job_input.provider_id == "gemini":
                api_key = settings.get("gemini_api_key", "")
            elif job_input.provider_id == "groq":
                api_key = settings.get("groq_api_key", "")

        result: ReverseATSResult = await provider.generate_tailored_application(
            profile=profile,
            job_offer=job_input,
            api_key=api_key,
        )

        gen_id = self.storage.save_generation(result, job_title=result.cv.target_title)
        return {
            "generation_id": gen_id,
            "data": result.model_dump(),
        }

    def list_history(self) -> List[Dict[str, Any]]:
        return self.storage.list_generations()
