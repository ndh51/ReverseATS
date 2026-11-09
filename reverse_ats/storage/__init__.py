"""
Storage Backend Package (Pluggable).
Default implementation stores data in clean local JSON files inside `data/`.
Tomorrow you can swap `JsonFileStoragePlugin` with `SQLiteStoragePlugin` or `PostgresStoragePlugin`
without changing a single line of business logic or API routes.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from reverse_ats.core import (
    StorageBackendPlugin,
    CandidateProfile,
    ReverseATSResult,
)


class JsonFileStoragePlugin(StorageBackendPlugin):
    """Persists CandidateProfile, Settings, and Generation History in local JSON files."""

    def __init__(self, data_dir: str = "data") -> None:
        self.base_path = Path(data_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.history_dir = self.base_path / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.base_path / "profile.json"
        self.settings_file = self.base_path / "settings.json"

    def load_profile(self) -> CandidateProfile:
        if not self.profile_file.exists():
            default_profile = CandidateProfile(
                full_name="",
                title="",
                email="",
                phone="",
                location="",
                links=[],
                master_bio="",
                uploaded_cvs=[],
            )
            self.save_profile(default_profile)
            return default_profile

        try:
            raw = json.loads(self.profile_file.read_text(encoding="utf-8"))
            return CandidateProfile(**raw)
        except Exception:
            return CandidateProfile()

    def save_profile(self, profile: CandidateProfile) -> CandidateProfile:
        self.profile_file.write_text(
            json.dumps(profile.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return profile

    def load_settings(self) -> Dict[str, Any]:
        default_settings = {
            "default_provider": "gemini",
            "default_model": "gemini-3.8-flash",
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        }
        if not self.settings_file.exists():
            return default_settings
        try:
            saved = json.loads(self.settings_file.read_text(encoding="utf-8"))
            return {**default_settings, **saved}
        except Exception:
            return default_settings

    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        current = self.load_settings()
        current.update(settings)
        self.settings_file.write_text(
            json.dumps(current, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return current

    def save_generation(self, result: ReverseATSResult, job_title: str) -> str:
        gen_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        record = {
            "id": gen_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "job_title": job_title or result.cv.target_title,
            "company": result.cover_letter.recipient_company,
            "match_score": result.ats_analysis.match_score,
            "provider_used": result.provider_used,
            "model_used": result.model_used,
            "result": result.model_dump(),
        }
        file_path = self.history_dir / f"{gen_id}.json"
        file_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return gen_id

    def list_generations(self) -> List[Dict[str, Any]]:
        records = []
        for f in sorted(self.history_dir.glob("*.json"), reverse=True)[:30]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                records.append({
                    "id": data.get("id", f.stem),
                    "created_at": data.get("created_at", ""),
                    "job_title": data.get("job_title", ""),
                    "company": data.get("company", ""),
                    "match_score": data.get("match_score", 0),
                    "provider_used": data.get("provider_used", ""),
                })
            except Exception:
                continue
        return records

    def get_generation(self, gen_id: str) -> Dict[str, Any]:
        file_path = self.history_dir / f"{gen_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Génération '{gen_id}' introuvable.")
        return json.loads(file_path.read_text(encoding="utf-8"))
