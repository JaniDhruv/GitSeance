# 🔮 GitSéance (GitSeance)

```
   _____ _____ _______    _____ ______     _   _  _____ ______ 
  / ____|_   _|__   __|  / ____|  ____|   /\   | \ | |/ ____|  ____|
 | |  __  | |    | |    | (___ | |__     /  \  |  \| | |    | |__   
 | | |_ | | |    | |     \___ \|  __|   / /\ \ | . ` | |    |  __|  
 | |__| |_| |_   | |     ____) | |____ / ____ \| |\  | |____| |____ 
  \_____|_____|  |_|    |_____/|______/_/    \_\_| \_|\_____|______|
```

> **An Open-Source AI Necromancer that brings "dead" GitHub repositories back to life — and predicts which files are about to die next.**
> 
> *Tagline:* *"Every codebase has ghosts. GitSéance channels them."*

Built for **Hacktoberfest Open-Source AI Challenge: Week 4 ("Ghost in the Machine")**.

---

## 🌟 The Core Problem

73% of abandoned code repositories haven't been touched in over two years. In nearly every enterprise and open-source project, there is a haunted file marked with `// DO NOT TOUCH: NOBODY KNOWS WHY THIS WORKS`. When the original author moves on, their domain knowledge vanishes with them. The code slowly rots, vulnerabilities creep in, and fear prevents anyone from refactoring it.

**GitSéance** turns the graveyard of legacy code into an interactive, grounded séance.

---

## 🧠 The Four Specialized Agents

```
                        ┌───────────────────────────────┐
                        │   Haunted Terminal (CRT UI)   │
                        └──────────────┬────────────────┘
                                       │
                                       ▼
                         FastAPI Orchestration Core
                                       │
        ┌──────────────┬───────────────┴───────────────┬──────────────┐
        ▼              ▼                               ▼              ▼
  💀 The Reaper   📊 The Oracle                  🔮 The Medium   🔍 The Searcher
 (Dead Code AST) (TabPFN-3.5 Mortality ML)       (Gemma 3 LLM)   (SerpApi Web Search)
        │              │                               │              │
        ▼              ▼                               ▼              ▼
   GitHub API      Prior Labs API                 Google GenAI    SerpApi & CVEs
```

### 1. 💀 The Reaper Agent (`backend/agents/reaper.py`)
- Traverses the entire Git commit tree and AST.
- Computes granular file-level metrics: days since last commit, unique authors, churn velocity, bug-fix commit ratio (`fix`, `bug`, `patch`), and test coverage.
- Classifies files into 6 haunting states:
  - 💀 **Clinically Dead**: Untouched for 2+ years.
  - 👻 **Haunted**: Contains fear comments (`do not touch`, `hack`, `black magic`) or high churn.
  - 🪦 **Orphaned**: 100% single-author bus factor where author has departed.
  - ☠️ **Cursed**: Exceptionally high ratio of bug-fix commits.
  - 🌫️ **Fading**: Stagnant code declining in touch frequency.
  - ✨ **Active**: Healthy, actively maintained files.

### 2. 📊 The Oracle Agent (`backend/agents/oracle.py` + `backend/services/tabpfn_client.py`)
- **Powered by Prior Labs TabPFN-3.5**: A Foundation Model for Tabular Data.
- Transforms git forensic indicators into a 7-dimensional feature matrix:
  - `days_since_last_commit`
  - `total_commits`
  - `unique_authors`
  - `bug_fix_commit_ratio`
  - `lines_ratio` (added vs deleted)
  - `has_tests` (binary test indicator)
  - `churn_velocity` (commits per month)
- In contrast to rigid rule-based linters, TabPFN’s Bayesian Prior computes calibrated **Mortality Probability (0.0 to 1.0)**, predicting which active files are on the verge of becoming unmaintainable.

### 3. 🔮 The Medium Agent (`backend/agents/medium.py` + `backend/services/gemma_client.py`)
- **Powered by Google Gemma 3 Open-Weight LLM**.
- Channels the persona of the original developer who made the last commit.
- Delivers a structured spiritual monologue:
  - **The Ghost's Confession**: Why the code was originally written under bygone constraints.
  - **The Unfinished Business**: What the ghost regrets not implementing.
  - **The Revival Blueprint**: Concrete migration steps, modern syntax replacements, and effort estimations.

### 4. 🔍 The Searcher Agent (`backend/agents/searcher.py` + `backend/services/serpapi_client.py`)
- **Powered by SerpApi**.
- Automatically extracts dependencies from `requirements.txt`, `package.json`, `Gemfile`, or `go.mod`.
- Performs live web queries to surface modern 2026 replacements and active CVE security advisories.

### 5. 🔊 The Ghost's Voice (`backend/services/elevenlabs_client.py`)
- **Powered by ElevenLabs Neural TTS**.
- Converts the Gemma séance monologue into spooky, atmospheric narration with selectable personas (*Aria Spectral Whisper*, *Roger Ancient Architect*, *Sarah Soft Echo*).
- Features a synchronized real-time Web Audio API waveform visualizer on the frontend.

---

## 🎨 Haunted CRT Frontend

- **Zero-Bloat Vanilla Stack**: Pure HTML5, Vanilla CSS3, and JavaScript ES6+ (no heavy Node build steps).
- **Authentic Retro CRT Physics**: Phosphor green glow, authentic scanlines, glass vignette curvature, and screen jitter.
- **Audio Synthesis Engine**: Web Audio API generates authentic mechanical keystroke clicks and ethereal summoning hums.
- **Interactive Particle System**: Floating ectoplasmic canvas wisps and mouse trails.

---

## 🛠️ Technology Integration Matrix

| Partner / Tool | Role in GitSéance |
|---|---|
| **TabPFN 3.5** | Bayesian tabular neural network predicting file abandonment risk |
| **Gemma 3** | Open-weight LLM channeling developer ghosts & revival blueprints |
| **ElevenLabs** | Neural voice text-to-speech for audible ghost channeling |
| **SerpApi** | Live search grounding for 2026 library replacements & CVE lookups |
| **Sentry** | Distributed tracing and AI Agent transaction monitoring |
| **Render** | Dockerized cloud container deployment |
| **FastAPI** | High-performance asynchronous Python backend |

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Configure
```bash
git clone https://github.com/JaniDhruv/GitSeance.git
cd GitSeance

# Copy configuration template
cp .env.example .env
```

Edit `.env` with your API keys:
```env
GITHUB_TOKEN=ghp_your_github_token       # (Optional, boosts rate limits to 5,000 req/hr)
GOOGLE_API_KEY=your_gemini_or_gemma_key   # Google AI Studio (free tier)
TABPFN_API_KEY=your_tabpfn_api_key       # Prior Labs API key
SERPAPI_KEY=your_serpapi_key             # SerpApi free key (100 searches/mo)
ELEVENLABS_API_KEY=your_elevenlabs_key   # ElevenLabs free key
SENTRY_DSN=your_sentry_dsn               # Sentry error & AI tracing
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Run the Necromancer
```bash
cd backend
uvicorn main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser. The haunted terminal will ignite!

---

## 🐳 Docker Deployment

```bash
docker build -t gitseance .
docker run -p 8000:8000 --env-file .env gitseance
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
