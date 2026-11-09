"""
API Package (FastAPI REST Controllers).
Clean HTTP layer exposing the ReverseATSService to the web frontend (or any future mobile/CLI client).
"""
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from reverse_ats.core import CandidateProfile, JobOfferInput, ReverseATSResult
from reverse_ats.services import ReverseATSService


class ScrapeUrlRequest(BaseModel):
    url: str


class ImportJsonRequest(BaseModel):
    raw_json: str


def create_api_router(service: ReverseATSService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/config")
    async def get_config() -> Dict[str, Any]:
        return service.get_providers_and_settings()

    @router.post("/config")
    async def update_config(payload: Dict[str, Any]) -> Dict[str, Any]:
        return service.save_settings(payload)

    @router.get("/profile", response_model=CandidateProfile)
    async def get_profile() -> CandidateProfile:
        return service.get_profile()

    @router.put("/profile", response_model=CandidateProfile)
    async def save_profile(profile: CandidateProfile) -> CandidateProfile:
        return service.update_profile(profile)

    @router.post("/profile/cv", response_model=CandidateProfile)
    async def upload_cv(file: UploadFile = File(...)) -> CandidateProfile:
        try:
            content = await file.read()
            return service.upload_cv_file(content, file.filename or "cv.pdf")
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.delete("/profile/cv/{cv_id}", response_model=CandidateProfile)
    async def delete_cv(cv_id: str) -> CandidateProfile:
        return service.delete_cv_file(cv_id)

    @router.post("/scrape-job")
    async def scrape_job(req: ScrapeUrlRequest) -> Dict[str, str]:
        try:
            text = await service.extract_job_from_url(req.url.strip())
            return {"extracted_text": text}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.post("/generate")
    async def generate_tailored(job_input: JobOfferInput) -> Dict[str, Any]:
        try:
            return await service.generate_application(job_input)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @router.post("/import-json")
    async def import_manual_json(req: ImportJsonRequest) -> Dict[str, Any]:
        """Allows importing a JSON response generated from an external free chat (e.g. ChatGPT/Claude Web)."""
        try:
            cleaned = req.raw_json.strip()
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1:
                cleaned = cleaned[start : end + 1]
            parsed = json.loads(cleaned)
            result = ReverseATSResult(**parsed)
            result.provider_used = "manual_import"
            gen_id = service.storage.save_generation(result, job_title=result.cv.target_title)
            return {"generation_id": gen_id, "data": result.model_dump()}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"JSON invalide : {exc}")

    @router.get("/history")
    async def get_history():
        return service.list_history()

    @router.get("/history/{gen_id}")
    async def get_history_item(gen_id: str):
        try:
            return service.storage.get_generation(gen_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    return router
