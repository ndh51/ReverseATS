"""
ReverseATS - Main Application Factory & Server Entrypoint.
Wires together the independent pluggable packages:
- `reverse_ats.core` (Contracts & DTOs)
- `reverse_ats.parsers` (PDF, DOCX, TXT/MD Document Parsers)
- `reverse_ats.scrapers` (Generic HTTP + Jina Fallback Job Scrapers)
- `reverse_ats.providers` (Gemini API, Groq API, Ollama Local, Manual Prompt Mode)
- `reverse_ats.storage` (Local JSON Storage Backend)
- `reverse_ats.services` (Application Orchestrator)
- `reverse_ats.api` (FastAPI REST Router)
"""
import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from reverse_ats.parsers import create_default_parser_registry
from reverse_ats.scrapers import create_default_scraper_registry
from reverse_ats.providers import create_default_provider_registry
from reverse_ats.storage import JsonFileStoragePlugin
from reverse_ats.services import ReverseATSService
from reverse_ats.api import create_api_router

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "reverse_ats" / "web" / "static"
DATA_DIR = BASE_DIR / "data"


def create_app() -> FastAPI:
    """Dependency Injection Factory assembling all pluggable modules."""
    parser_registry = create_default_parser_registry()
    scraper_registry = create_default_scraper_registry()
    provider_registry = create_default_provider_registry()
    storage_backend = JsonFileStoragePlugin(data_dir=str(DATA_DIR))

    service = ReverseATSService(
        parser_registry=parser_registry,
        scraper_registry=scraper_registry,
        provider_registry=provider_registry,
        storage=storage_backend,
    )

    app = FastAPI(
        title="Reverse ATS Studio",
        description="Modular & Pluggable AI Resume & Cover Letter Tailoring Platform",
        version="1.0.0",
    )

    # Mount REST API router
    app.include_router(create_api_router(service))

    # Mount static frontend assets
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_spa():
        return FileResponse(str(STATIC_DIR / "index.html"))

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    print(f"\n[ReverseATS] Serveur demarre sur : http://localhost:{port}\n")
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
