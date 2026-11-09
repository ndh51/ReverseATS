"""
Centralized Prompt Builder & Schema Generator.
Shared across all LLM Provider plugins so that changing the prompt strategy or JSON schema
happens in ONE single place.
"""
from typing import Dict, Any
from reverse_ats.core import CandidateProfile, JobOfferInput, ReverseATSResult


def get_system_instruction(language: str, tone: str) -> str:
    return (
        "Tu es un expert en recrutement technique, optimisation ATS (Applicant Tracking System) "
        "et coaching de carrière de haut niveau.\n"
        "Ta mission est de réaliser du 'Reverse ATS' :\n"
        "1. Analyser en profondeur l'offre d'emploi fournie (mots-clés implicites et explicites, "
        "compétences clés, culture d'entreprise, responsabilités).\n"
        "2. Puiser UNIQUEMENT dans les faits réels présents dans les CVs et la Biographie détaillée (Master Bio) "
        "du candidat pour construire un CV sur-mesure (1 page A4) et une lettre de motivation percutante.\n"
        "3. RÈGLE D'OR : Ne JAMAIS inventer de fausses entreprises, de faux diplômes ou de faux projets. "
        "En revanche, reformule les réalisations, réorganise l'ordre des points, mets en avant les projets "
        "les plus pertinents de sa bio, et adopte exactement la terminologie (mots-clés ATS) de l'offre d'emploi "
        "lorsqu'elle correspond aux compétences réelles du candidat.\n"
        f"4. Langue de rédaction obligatoire : {language}.\n"
        f"5. Ton souhaité : {tone}.\n"
        "6. Réponds UNIQUEMENT avec un objet JSON valide respectant strictement le schéma demandé."
    )


def build_user_prompt(profile: CandidateProfile, job_offer: JobOfferInput) -> str:
    cvs_section = ""
    if profile.uploaded_cvs:
        parts = []
        for idx, cv in enumerate(profile.uploaded_cvs, start=1):
            parts.append(f"=== CV SOURCE #{idx} ({cv.filename}) ===\n{cv.extracted_text}")
        cvs_section = "\n\n".join(parts)
    else:
        cvs_section = "(Aucun fichier CV uploadé — utilise les informations de la Master Bio ci-dessous)"

    contact_info = (
        f"Nom complet : {profile.full_name}\n"
        f"Titre habituel : {profile.title}\n"
        f"Email : {profile.email}\n"
        f"Téléphone : {profile.phone}\n"
        f"Localisation : {profile.location}\n"
        f"Liens (GitHub/LinkedIn/Portfolio) : {', '.join(profile.links)}\n"
    )

    custom_instr = (
        f"\nINSTRUCTIONS SPÉCIFIQUES DU CANDIDAT POUR CETTE OFFRE :\n{job_offer.custom_instructions}\n"
        if job_offer.custom_instructions.strip()
        else ""
    )

    schema_json = ReverseATSResult.model_json_schema()

    return (
        "Voici l'ensemble du dossier du candidat ainsi que l'offre d'emploi cible.\n\n"
        "------------------------------------------------------------\n"
        "1. COORDONNÉES DU CANDIDAT\n"
        "------------------------------------------------------------\n"
        f"{contact_info}\n"
        "------------------------------------------------------------\n"
        "2. MASTER BIO / DESCRIPTION DÉTAILLÉE (Compétences, Projets, Contexte)\n"
        "------------------------------------------------------------\n"
        f"{profile.master_bio or '(Non renseignée)'}\n\n"
        "------------------------------------------------------------\n"
        "3. CVs EXISTANTS DU CANDIDAT\n"
        "------------------------------------------------------------\n"
        f"{cvs_section}\n\n"
        "------------------------------------------------------------\n"
        "4. OFFRE D'EMPLOI CIBLE\n"
        "------------------------------------------------------------\n"
        f"{job_offer.raw_text}\n"
        f"{custom_instr}\n"
        "------------------------------------------------------------\n"
        "FORMAT DE SORTIE ATTENDU (JSON STRICT)\n"
        "------------------------------------------------------------\n"
        f"Langue : {job_offer.language} | Ton : {job_offer.tone}\n"
        "Génère un JSON respectant exactement la structure de `ReverseATSResult` "
        "(avec les clés principales `ats_analysis`, `cv`, `cover_letter`)."
    )


def get_clean_json_schema() -> Dict[str, Any]:
    """Returns the JSON schema for ReverseATSResult without provider-internal metadata fields."""
    return {
        "type": "object",
        "required": ["ats_analysis", "cv", "cover_letter"],
        "properties": {
            "ats_analysis": {
                "type": "object",
                "required": [
                    "match_score",
                    "matched_keywords",
                    "missing_or_weak_keywords",
                    "tailoring_strategy",
                ],
                "properties": {
                    "match_score": {
                        "type": "integer",
                        "description": "Score ATS de 0 à 100 après optimisation du CV",
                    },
                    "matched_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Mots-clés de l'offre intégrés dans le CV généré",
                    },
                    "missing_or_weak_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Compétences demandées dans l'offre mais absentes du profil réel du candidat",
                    },
                    "tailoring_strategy": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Explications concrètes des choix d'adaptation effectués pour cette offre",
                    },
                },
            },
            "cv": {
                "type": "object",
                "required": [
                    "full_name",
                    "target_title",
                    "email",
                    "phone",
                    "location",
                    "links",
                    "executive_summary",
                    "skill_categories",
                    "experiences",
                    "projects",
                    "education",
                    "languages",
                    "certifications_or_extras",
                ],
                "properties": {
                    "full_name": {"type": "string"},
                    "target_title": {
                        "type": "string",
                        "description": "Titre du CV aligné sur l'intitulé exact du poste visé",
                    },
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "location": {"type": "string"},
                    "links": {"type": "array", "items": {"type": "string"}},
                    "executive_summary": {
                        "type": "string",
                        "description": "Accroche percutante de 3-4 lignes riche en mots-clés ATS",
                    },
                    "skill_categories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["category", "skills"],
                            "properties": {
                                "category": {"type": "string"},
                                "skills": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "experiences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["role", "company", "period", "location", "highlights"],
                            "properties": {
                                "role": {"type": "string"},
                                "company": {"type": "string"},
                                "period": {"type": "string"},
                                "location": {"type": "string"},
                                "highlights": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Puces orientées résultats et mots-clés ATS",
                                },
                            },
                        },
                    },
                    "projects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "tech_stack", "period", "description", "link"],
                            "properties": {
                                "name": {"type": "string"},
                                "tech_stack": {"type": "string"},
                                "period": {"type": "string"},
                                "description": {"type": "string"},
                                "link": {"type": "string"},
                            },
                        },
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["degree", "institution", "period", "details"],
                            "properties": {
                                "degree": {"type": "string"},
                                "institution": {"type": "string"},
                                "period": {"type": "string"},
                                "details": {"type": "string"},
                            },
                        },
                    },
                    "languages": {"type": "array", "items": {"type": "string"}},
                    "certifications_or_extras": {"type": "array", "items": {"type": "string"}},
                },
            },
            "cover_letter": {
                "type": "object",
                "required": [
                    "recipient_company",
                    "recipient_role",
                    "date_location",
                    "subject",
                    "salutation",
                    "opening_paragraph",
                    "body_paragraphs",
                    "closing_paragraph",
                    "sign_off",
                    "signature_name",
                ],
                "properties": {
                    "recipient_company": {"type": "string"},
                    "recipient_role": {"type": "string"},
                    "date_location": {"type": "string"},
                    "subject": {"type": "string"},
                    "salutation": {"type": "string"},
                    "opening_paragraph": {"type": "string"},
                    "body_paragraphs": {"type": "array", "items": {"type": "string"}},
                    "closing_paragraph": {"type": "string"},
                    "sign_off": {"type": "string"},
                    "signature_name": {"type": "string"},
                },
            },
        },
    }
