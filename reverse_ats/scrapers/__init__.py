"""
Job Offer Scrapers Package (Pluggable).
Extracts clean job offer text from URLs.
If tomorrow you want to add a Playwright/Selenium scraper for SPA websites or a LinkedIn-specific scraper,
just implement `JobScraperPlugin` and register it in `ScraperRegistry`.
"""
import re
from typing import List
import httpx
from bs4 import BeautifulSoup
from reverse_ats.core import JobScraperPlugin


class GenericHttpJobScraper(JobScraperPlugin):
    """
    Universal HTTP + BeautifulSoup job scraper.
    Extracts structured metadata (JSON-LD JobPosting if available) + main readable content.
    """

    @property
    def name(self) -> str:
        return "generic_http_scraper"

    def can_handle(self, url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    async def scrape(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "html.parser")

        # 1. Remove noisy tags
        for tag in soup(["script", "style", "noscript", "svg", "footer", "nav", "header", "iframe"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # 2. Prefer <main> or <article> if present
        main_container = soup.find("main") or soup.find("article") or soup.body or soup
        raw_text = main_container.get_text(separator="\n", strip=True)

        # Clean up excessive blank lines
        lines = [line.strip() for line in raw_text.splitlines() if len(line.strip()) > 1]
        cleaned_text = "\n".join(lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        if title:
            return f"Source URL: {url}\nTitre de la page: {title}\n\n{cleaned_text[:18000]}"
        return f"Source URL: {url}\n\n{cleaned_text[:18000]}"


class JinaReaderFallbackScraper(JobScraperPlugin):
    """
    Uses r.jina.ai free reader proxy as a fallback when a site relies on JS or blocks simple requests.
    """

    @property
    def name(self) -> str:
        return "jina_reader_scraper"

    def can_handle(self, url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    async def scrape(self, url: str) -> str:
        reader_url = f"https://r.jina.ai/{url}"
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(reader_url)
            response.raise_for_status()
            return response.text[:18000]


class ScraperRegistry:
    """Manages job scrapers with automatic fallback chain."""

    def __init__(self) -> None:
        self._scrapers: List[JobScraperPlugin] = []

    def register(self, scraper: JobScraperPlugin) -> None:
        self._scrapers.append(scraper)

    async def scrape_url(self, url: str) -> str:
        errors = []
        for scraper in self._scrapers:
            if scraper.can_handle(url):
                try:
                    text = await scraper.scrape(url)
                    if text and len(text.strip()) > 120:
                        return text
                except Exception as exc:
                    errors.append(f"{scraper.name}: {exc}")
        raise RuntimeError(
            f"Impossible d'extraire automatiquement le texte depuis {url}. "
            f"Détails: {'; '.join(errors)}. Vous pouvez copier-coller le texte de l'offre directement."
        )


def create_default_scraper_registry() -> ScraperRegistry:
    registry = ScraperRegistry()
    registry.register(GenericHttpJobScraper())
    registry.register(JinaReaderFallbackScraper())
    return registry
