# 🎯 Reverse ATS Studio — Générateur Modulaire de CV & Lettre de Motivation sur-mesure par IA

**Reverse ATS Studio** est une application web locale permettant d'inverser la logique des **ATS** (*Applicant Tracking Systems* — les robots de tri de candidatures utilisés par les recruteurs).

À partir de **vos CVs existants**, de votre **Biographie détaillée ("Master Profile")** et d'une **offre d'emploi cible** (via son **lien URL** ou son **texte**), l'application analyse les mots-clés attendus par le recruteur et génère automatiquement :
1. Un **Score de correspondance ATS** avec la liste des mots-clés intégrés et l'explication de la stratégie d'adaptation.
2. Un **CV sur-mesure d'une page A4** (avec 2 designs au choix : *Moderne 2 colonnes* ou *Classique 1 colonne 100% ATS*), **éditable en direct** au clic.
3. Une **Lettre de Motivation sur-mesure A4**, également éditable en direct.
4. Un **Export PDF vectoriel propre** (avec vrai texte sélectionnable pour être lu à 100% par les robots ATS).

> **Règle d'or de l'IA intégrée :** Le moteur ne **s'invente jamais** de fausses expériences ou de faux diplômes. Il puise exclusivement dans vos vrais projets et compétences (présents dans vos CVs et votre Master Bio) pour les reformuler, les réordonner et les aligner sur le vocabulaire exact de l'offre d'emploi.

---

## 🚀 Comment lancer le projet

### 1. Démarrage rapide (PowerShell sous Windows)

Si l'environnement virtuel `.venv` est déjà créé (ce qui est le cas dans `C:\DEV\ReverseATS`) :

```powershell
cd C:\DEV\ReverseATS
.\.venv\Scripts\python.exe main.py
```

Puis ouvrez votre navigateur sur : **[http://localhost:8080](http://localhost:8080)**

---

### 2. Installation complète depuis zéro (si vous clonez le projet ailleurs)

```powershell
cd C:\DEV\ReverseATS

# 1. Créer l'environnement virtuel Python
python -m venv .venv

# 2. Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer le serveur web
python main.py
```

*(Par défaut, le serveur écoute sur le port `8080`. Vous pouvez changer le port via la variable d'environnement `PORT=8090` dans un fichier `.env`.)*

---

## 🔑 Comment configurer l'IA gratuitement (4 solutions incluses)

Cliquez sur le bouton **"Clés IA (Gratuit)"** en haut à droite de l'interface web (`http://localhost:8080`) pour configurer le moteur de votre choix :

### Option 1 : Google Gemini API (via Google AI Studio)
- Rendez-vous sur [aistudio.google.com/apikey](https://aistudio.google.com/apikey).
- Créez une clé API sur un projet dont le niveau de facturation est **"Gratuit" (Free Tier)**.
  - *Attention :* Si votre compte Google principal possède déjà un portefeuille prépayé Google Cloud à `0 €` (affiché *"Niveau 1 / Tier 1"*), Google renverra une erreur `402 Prepayment credits depleted`. Dans ce cas, créez la clé avec un compte Gmail secondaire sans facturation Cloud pour bénéficier du **Free Tier** gratuit, ou utilisez **Groq Cloud** ci-dessous !
- **Modèles inclus :**
  - `gemini-3.8-flash` *(Recommandé — rapide, 1M tokens)*
  - `gemini-4-argon` *(Modèle Pro — raisonnement approfondi)*
  - `gemini-3.5-flash-lite` & `gemini-3.1-flash-lite` *(Ultra-rapides, quotas élevés)*
  - `gemma-4-31b-it` & `gemma-4-26b-a4b-it` *(Modèles Open-Weights Google)*

### Option 2 : Groq Cloud API (100% Gratuit, sans carte bancaire, ultra-rapide)
- Rendez-vous sur [console.groq.com/keys](https://console.groq.com/keys) (connexion en 1 clic avec Google).
- Créez une clé gratuite (`gsk_...`) et collez-la dans le champ **Clé API Groq Cloud** de l'interface.
- Sélectionnez **"Groq Cloud (Gratuit — Llama 3.3 70B)"** : génération complète en moins de 2 secondes.

### Option 3 : Ollama Local (100% Hors-ligne sur votre PC)
- Si [Ollama](https://ollama.com/) tourne sur votre machine (`http://localhost:11434`), sélectionnez **"Ollama Local"** pour utiliser vos modèles locaux (`qwen2.5:14b`, `llama3.2`, `mistral`) sans aucune connexion internet ni clé API.

### Option 4 : Mode "Sans Clé API" (Générateur de Prompt + Import JSON)
- Si vous n'avez aucune clé API mais que vous avez un abonnement web (ex: **Gemini Advanced / Pro Web**, **ChatGPT Plus**, **Claude**), choisissez **"Mode Sans Clé API"**.
- L'application génère le **Prompt structuré complet** contenant votre profil, vos CVs, l'offre d'emploi et le schéma JSON attendu.
- Copiez ce prompt dans votre chat web habituel, puis collez la réponse JSON obtenue dans la case **"Importer le JSON"** : votre CV A4 et votre Lettre de Motivation A4 se mettent en page instantanément !

---

## 📖 Guide d'utilisation étape par étape

1. **Onglet `1. Mon Profil & CVs` (À faire une seule fois)**
   - Renseignez vos coordonnées (Nom, Titre, Email, Téléphone, Ville, Liens GitHub/LinkedIn).
   - **Importez un ou plusieurs CVs** (`.pdf`, `.docx`, `.txt`, `.md`). Le texte de chaque CV est extrait automatiquement et conservé.
   - **Remplissez votre "Master Bio"** : décrivez en détail tous vos projets scolaires, personnels et professionnels, vos stacks techniques, vos résultats chiffrés et ce que vous recherchez. Cliquez sur **Enregistrer mon profil complet**.
2. **Onglet `2. Offre & Ciblage IA` (Pour chaque candidature)**
   - Collez le **lien URL de l'offre** et cliquez sur **"🔍 Extraire le texte du lien"** (ou collez directement le texte de l'offre).
   - Choisissez le fournisseur IA, le modèle, la langue (*Français* ou *Anglais*) et le ton souhaité.
   - Ajoutez éventuellement une instruction spécifique (ex: *"Mets en avant mon expérience Docker et Python"*).
   - Cliquez sur **"🚀 Générer le CV & la Lettre sur-mesure"**.
3. **Onglet `3. Résultat A4 & Export PDF`**
   - Consultez votre **Score ATS**, les mots-clés intégrés et les choix stratégiques effectués.
   - Basculez entre le **CV Optimisé A4** (2 designs au choix : *Moderne 2 Colonnes* ou *Classique 1 Colonne ATS*) et la **Lettre de Motivation A4**.
   - **Édition directe :** Cliquez sur n'importe quel titre, puce ou paragraphe directement sur la feuille A4 pour retoucher un mot à la volée.
   - Cliquez sur **"🖨️ Télécharger / Exporter en PDF (A4)"** et choisissez **"Enregistrer au format PDF"** (pensez à cocher *"Graphiques d'arrière-plan"* dans les options d'impression du navigateur pour conserver les couleurs de la colonne latérale).

---

## 🧩 Architecture Modulaire & Interpluggable (`reverse_ats/`)

Le code a été conçu selon une architecture **Hexagonale / Ports & Adapters** stricte. Chaque package est indépendant et ne dépend que des contrats abstraits définis dans [`reverse_ats/core/__init__.py`](file:///C:/DEV/ReverseATS/reverse_ats/core/__init__.py) :

```text
C:\DEV\ReverseATS\
├── main.py                             # Point d'entrée & Injection de dépendances (Wiring)
├── requirements.txt                    # Dépendances Python
├── .env.example                        # Modèle de variables d'environnement
├── data/                               # Données persistées localement (non écrasées au redémarrage)
│   ├── profile.json                    # Coordonnées + Master Bio + CVs extraits
│   ├── settings.json                   # Clés API et préférences sauvegardées
│   └── history/                        # Historique complet de toutes les candidatures générées
└── reverse_ats/
    ├── core/
    │   └── __init__.py                 # Modèles Pydantic (DTOs) & Interfaces Abstraites (ABC Ports)
    ├── parsers/
    │   └── __init__.py                 # Plugins d'extraction de CV (PDF, DOCX, TXT/MD) + ParserRegistry
    ├── scrapers/
    │   └── __init__.py                 # Plugins d'extraction d'offres web (HTTP BS4 + Jina Fallback) + ScraperRegistry
    ├── providers/
    │   ├── __init__.py                 # ProviderRegistry (Factory des moteurs IA)
    │   ├── prompts.py                  # Prompt système Reverse ATS & Schéma JSON centralisés
    │   ├── gemini_provider.py          # Plugin officiel Google Gemini (`google-genai` SDK)
    │   └── other_providers.py          # Plugins Groq Cloud, Ollama Local et Mode Sans Clé API
    ├── storage/
    │   └── __init__.py                 # Plugin de stockage (`JsonFileStoragePlugin`)
    ├── services/
    │   └── __init__.py                 # Orchestrateur métier découplé (`ReverseATSService`)
    ├── api/
    │   └── __init__.py                 # Contrôleurs REST FastAPI (`/api/*`)
    └── web/static/
        ├── index.html                  # Interface utilisateur & Feuilles A4 CSS Print
        └── app.js                      # Logique frontend, édition directe & templates de CV
```

### Comment faire évoluer ou remplacer un module demain ?
- **Ajouter un nouveau fournisseur IA (ex: Mistral, OpenAI, Anthropic)** :
  Créez une classe héritant de `LLMProviderPlugin` dans `reverse_ats/providers/` et enregistrez-la avec `registry.register(...)` dans [`reverse_ats/providers/__init__.py`](file:///C:/DEV/ReverseATS/reverse_ats/providers/__init__.py). Elle apparaîtra automatiquement dans l'interface web !
- **Ajouter un nouveau format de fichier CV (ex: `.odt`, `.rtf`)** :
  Créez une classe héritant de `DocumentParserPlugin` et enregistrez-la dans [`reverse_ats/parsers/__init__.py`](file:///C:/DEV/ReverseATS/reverse_ats/parsers/__init__.py).
- **Remplacer le stockage JSON par une base SQLite ou PostgreSQL** :
  Créez une classe héritant de `StorageBackendPlugin` dans [`reverse_ats/storage/__init__.py`](file:///C:/DEV/ReverseATS/reverse_ats/storage/__init__.py) et passez-la à `ReverseATSService` dans [`main.py`](file:///C:/DEV/ReverseATS/main.py).
