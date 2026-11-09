# Reverse ATS

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/Licence-Propri%C3%A9taire-red?style=flat-square)

Interface web locale pour adapter automatiquement un CV et une lettre de motivation à une offre d'emploi cible.

L'application analyse les mots-clés attendus par les logiciels de tri de candidatures (ATS) et génère des documents sur-mesure au format A4 à partir des compétences, projets et expériences réels enregistrés dans le profil utilisateur.

## Fonctionnalités principales

- **Gestion multi-CV** : import de un ou plusieurs CVs existants (`.pdf`, `.docx`, `.txt`, `.md`) avec extraction automatique du texte.
- **Profil détaillé (Master Bio)** : espace de saisie libre pour décrire l'ensemble de son parcours, ses projets techniques et ses réalisations. Les données sont sauvegardées localement.
- **Analyse d'offre d'emploi** : récupération automatique du texte d'une annonce depuis un lien web (URL) ou par simple copier-coller.
- **Génération sur-mesure** : création d'un CV d'une page et d'une lettre de motivation adaptés au poste visé, accompagnés d'un score de correspondance et des mots-clés retenus.
- **Édition directe et export PDF** : aperçu au format A4 (modèle 2 colonnes ou modèle 1 colonne classique) modifiable directement au clic avant export en PDF vectoriel.

## Installation et lancement

### Prérequis

- Python 3.11 ou supérieur
- Git

### 1. Récupérer le projet

```bash
git clone https://github.com/ndh51/ReverseATS.git
cd ReverseATS
```

### 2. Créer l'environnement virtuel et installer les dépendances

**Sous Windows (PowerShell) :**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Sous Linux / macOS :**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Démarrer le serveur

```bash
python main.py
```

L'interface est ensuite accessible dans le navigateur à l'adresse `http://localhost:8080`.
Pour utiliser un autre port, créez un fichier `.env` à partir de `.env.example` et modifiez la variable `PORT`.

## Configuration des moteurs d'IA

L'application fonctionne avec plusieurs fournisseurs d'IA configurables directement depuis le bouton **Clés IA** en haut à droite de l'interface :

1. **Google Gemini (Google AI Studio)**
   - Créez une clé gratuite sur [aistudio.google.com/apikey](https://aistudio.google.com/apikey) (assurez-vous que le projet associé est sur le niveau de facturation *Gratuit / Free tier*).
   - Modèles disponibles : `gemini-3.8-flash`, `gemini-4-argon`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemma-4-31b-it`, `gemma-4-26b-a4b-it`.
2. **Groq Cloud**
   - Créez une clé gratuite sur [console.groq.com/keys](https://console.groq.com/keys).
   - Modèles disponibles : `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`.
3. **Ollama (100% local et hors-ligne)**
   - Nécessite [Ollama](https://ollama.com/) installé sur la machine (`http://localhost:11434`).
   - Permet d'utiliser des modèles locaux sans clé API ni connexion internet.
4. **Mode sans clé API**
   - Génère le prompt complet prêt à être copié dans n'importe quel chat web (ChatGPT, Claude, Gemini).
   - Permet ensuite de coller la réponse JSON obtenue pour mettre en page le CV et la lettre en un clic.

## Utilisation

1. **Mon Profil & CVs** : renseignez vos coordonnées, importez vos CVs actuels et complétez votre biographie détaillée. Cliquez sur *Enregistrer mon profil complet*.
2. **Offre & Ciblage IA** : collez le lien ou le texte de l'offre d'emploi, choisissez le moteur d'IA, la langue et le ton, puis lancez la génération.
3. **Résultat A4 & Export PDF** : consultez l'analyse des mots-clés, choisissez le modèle visuel du CV, cliquez directement sur le texte de la feuille A4 si vous souhaitez ajuster une phrase, puis cliquez sur *Télécharger / Exporter en PDF (A4)*.

## Structure du projet

Le code est découpé en modules indépendants dans le dossier `reverse_ats/` afin de faciliter l'ajout ou le remplacement d'un composant :

```text
ReverseATS/
├── main.py                         # Point d'entrée du serveur web
├── requirements.txt                # Dépendances Python
├── .env.example                    # Exemple de configuration
└── reverse_ats/
    ├── core/                       # Modèles de données et interfaces des plugins
    ├── parsers/                    # Lecture des fichiers CV (PDF, Word, Texte)
    ├── scrapers/                   # Extraction des offres d'emploi depuis une URL
    ├── providers/                  # Connecteurs IA (Gemini, Groq, Ollama, Mode manuel)
    ├── storage/                    # Sauvegarde locale du profil et de l'historique
    ├── services/                   # Logique applicative
    ├── api/                        # Routes HTTP FastAPI
    └── web/static/                 # Interface utilisateur et feuilles de style A4
```

## Licence

Copyright (c) 2026 [ndh51](https://github.com/ndh51). Tous droits réservés.

Ce logiciel est propriétaire et n'est pas Open Source. Toute copie, modification, distribution ou utilisation non autorisée est interdite. Consultez le fichier [LICENSE](./LICENSE) pour les conditions complètes.
