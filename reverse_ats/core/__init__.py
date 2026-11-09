"""
Core domain contracts, DTOs, and Abstract Base Classes (Ports).
Every plugin (Parser, Scraper, LLM Provider, Storage, Exporter) depends ONLY on `core`.
Swapping any component requires zero changes to the rest of the application.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# 1. DOMAIN MODELS (Pydantic Contracts)
# ============================================================================

class UploadedCV(BaseModel):
    """Represents an uploaded CV document with its extracted text."""
    id: str
    filename: str
    extracted_text: str
    uploaded_at: str


class CandidateProfile(BaseModel):
    """The persistent candidate profile combining raw CVs and detailed bio."""
    full_name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: List[str] = Field(default_factory=list, description="GitHub, LinkedIn, Portfolio URLs")
    master_bio: str = Field(
        default="",
        description="Detailed free-form biography: skills, projects, achievements, context, preferences"
    )
    uploaded_cvs: List[UploadedCV] = Field(default_factory=list)


class JobOfferInput(BaseModel):
    """Input representing the target job offer and customization preferences."""
    raw_text: str = ""
    source_url: Optional[str] = None
    language: str = "Français"
    tone: str = "Professionnel & Impactant"
    template_style: str = "modern_sidebar"
    custom_instructions: str = ""
    provider_id: str = "gemini"
    model_name: str = "gemini-3.8-flash"
    api_key: Optional[str] = None


# --- Structured Output Models for the Generated CV & Cover Letter ---

class ExperienceItem(BaseModel):
    role: str
    company: str
    period: str
    location: str = ""
    highlights: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str
    tech_stack: str = ""
    period: str = ""
    description: str
    link: str = ""


class EducationItem(BaseModel):
    degree: str
    institution: str
    period: str
    details: str = ""


class SkillCategory(BaseModel):
    category: str
    skills: List[str] = Field(default_factory=list)


class TailoredCV(BaseModel):
    """Structured representation of the tailored CV ready to be rendered by any template."""
    full_name: str
    target_title: str
    email: str = ""
    phone: str = ""
    location: str = ""
    links: List[str] = Field(default_factory=list)
    executive_summary: str
    skill_categories: List[SkillCategory] = Field(default_factory=list)
    experiences: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    certifications_or_extras: List[str] = Field(default_factory=list)


class TailoredCoverLetter(BaseModel):
    """Structured representation of the tailored Cover Letter."""
    recipient_company: str
    recipient_role: str
    date_location: str = ""
    subject: str
    salutation: str
    opening_paragraph: str
    body_paragraphs: List[str] = Field(default_factory=list)
    closing_paragraph: str
    sign_off: str
    signature_name: str


class ATSAnalysis(BaseModel):
    """ATS Match analysis and strategic explanations."""
    match_score: int = Field(ge=0, le=100, description="Estimated ATS match score from 0 to 100")
    matched_keywords: List[str] = Field(default_factory=list)
    missing_or_weak_keywords: List[str] = Field(default_factory=list)
    tailoring_strategy: List[str] = Field(
        default_factory=list,
        description="Concrete explanations of how the CV was adapted to beat the ATS"
    )


class ReverseATSResult(BaseModel):
    """Complete result returned by any LLMProvider."""
    ats_analysis: ATSAnalysis
    cv: TailoredCV
    cover_letter: TailoredCoverLetter
    provider_used: str = ""
    model_used: str = ""
    fallback_prompt: Optional[str] = None


# ============================================================================
# 2. ABSTRACT INTERFACES (PORTS FOR PLUGGABLE PACKAGES)
# ============================================================================

class DocumentParserPlugin(ABC):
    """Interface for extracting text from uploaded CV files (.pdf, .docx, .txt, .md)."""

    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of lowercase file extensions supported (e.g., ['.pdf'])."""
        pass

    @abstractmethod
    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extract plain text from raw file bytes."""
        pass


class JobScraperPlugin(ABC):
    """Interface for extracting job description text from a URL."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL."""
        pass

    @abstractmethod
    async def scrape(self, url: str) -> str:
        """Fetch and clean the job offer text from the given URL."""
        pass


class LLMProviderPlugin(ABC):
    """Interface for AI providers (Gemini, Groq, Ollama, Prompt-Only, etc.)."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier (e.g. 'gemini', 'groq', 'ollama', 'prompt_only')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name for the UI."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> List[Dict[str, str]]:
        """List of models supported by this provider."""
        pass

    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        pass

    @abstractmethod
    async def generate_tailored_application(
        self,
        profile: CandidateProfile,
        job_offer: JobOfferInput,
        api_key: Optional[str] = None,
    ) -> ReverseATSResult:
        """Generate the tailored CV, Cover Letter, and ATS Analysis."""
        pass


class StorageBackendPlugin(ABC):
    """Interface for persisting the CandidateProfile and generation history."""

    @abstractmethod
    def load_profile(self) -> CandidateProfile:
        pass

    @abstractmethod
    def save_profile(self, profile: CandidateProfile) -> CandidateProfile:
        pass

    @abstractmethod
    def load_settings(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_generation(self, result: ReverseATSResult, job_title: str) -> str:
        pass

    @abstractmethod
    def list_generations(self) -> List[Dict[str, Any]]:
        pass
