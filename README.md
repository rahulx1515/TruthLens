# TruthLens 2.0: AI-Powered Multilingual News Verification & Credibility Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.15+-EE4C2C.svg)](https://pytorch.org/)
[![Ollama](https://img.shields.io/badge/Ollama-llama3.2-black.svg)](https://ollama.ai/)
[![Scikit--Learn](https://img.shields.io/badge/scikit--learn-1.4+-F7931E.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**TruthLens 2.0** is an enterprise-ready, multilingual news verification and credibility platform. Departing from simple stylistic text classification, TruthLens 2.0 investigates submitted news articles, headlines, URLs, and social claims using **live dynamic web evidence retrieval**, **atomic claim extraction**, **wire syndication clustering**, and **natural language inference (NLI)**. Every analysis compiles a transparent verification audit trail with original publisher links, exact verbatim quotations, and calibrated confidence metrics.

---

## Table of Contents
- [Dual-Engine Product Architecture](#dual-engine-product-architecture)
- [Key Features](#key-features)
- [Verdict Categories](#verdict-categories)
- [Multilingual Support (English & Hindi)](#multilingual-support-english--hindi)
- [System Architecture](#system-architecture)
- [Empirical Benchmarks](#empirical-benchmarks)
  - [TruthLens 2.0 Multilingual Evaluation Suite](#truthlens-20-multilingual-evaluation-suite)
  - [Local Ollama LLM Benchmark](#local-ollama-llm-benchmark)
  - [TruthLens 1.0 Legacy ML Classification Benchmark](#truthlens-10-legacy-ml-classification-benchmark)
- [Project Structure](#project-structure)
- [Local Development Quickstart](#local-development-quickstart)
- [Running the Test Suites](#running-the-test-suites)
- [API Reference](#api-reference)
- [Deployment Guide](#deployment-guide)
- [Scientific & Ethical Fact-Checking Advisory](#scientific--ethical-fact-checking-advisory)

---

## Dual-Engine Product Architecture

TruthLens integrates two complementary analytical engines:

```
                                  USER SUBMISSION
                          (Text, Headline, URL, Social)
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
┌───────────────────────────────┐     ┌─────────────────────────────────────────┐
│     TRUTHLENS 2.0 (LIVE)      │     │         TRUTHLENS 1.0 (LEGACY)          │
│ Multilingual Evidence Engine  │     │       Stylistic ML Classifier           │
├───────────────────────────────┤     ├─────────────────────────────────────────┤
│ • Script ID & Devanagari Norm │     │ • Unified Preprocessing (clean, stop)   │
│ • Atomic Claim Deconstruction │     │ • TF-IDF Vectorizer (10k n-grams)       │
│ • Multi-Tier Live Web Search  │     │ • Logistic Regression & Random Forest   │
│ • SSRF-Hardened Article Fetch │     │ • Explainable AI (Token Attribution)    │
│ • Overlapping Sentence Chunker│     │ • Evaluates stylistic sensationalism    │
│ • Wire Syndication Dedup      │     │                                         │
│ • Multilingual NLI on CPU     │     │                                         │
│ • 5-State Verdict Synthesis   │     │                                         │
│ • Verbatim Quotation Audit    │     │                                         │
└───────────────────────────────┘     └─────────────────────────────────────────┘
             │                                                     │
             ▼                                                     ▼
┌───────────────────────────────┐     ┌─────────────────────────────────────────┐
│ Live Verification Report      │     │ Stylistic Credibility Score             │
│ (SUPPORTED / REFUTED / etc.)  │     │ (LIKELY REAL / LIKELY FAKE)             │
└───────────────────────────────┘     └─────────────────────────────────────────┘
```

1. **TruthLens 2.0 (Primary Path)**: Fact-checks the factual veracity of claims against live external internet evidence. It answers: *"Does verifiable reporting corroborate or contradict these facts?"*
2. **TruthLens 1.0 (Supplementary Path)**: Analyzes linguistic patterns, clickbait markers, and writing style against trained classifiers. It answers: *"Does the writing style correlate with sensationalized or authentic journalism?"*

---

## Key Features

- **Multilingual Support**: First-class support for English (`en`) and Hindi (`hi`), including full Devanagari script preservation and Hinglish code-mixing detection.
- **Atomic Claim Extraction**: Deconstructs complex paragraphs into checkable, falsifiable propositions using local Ollama (`llama3.2:latest`) with deterministic rule fallback.
- **Multi-Tier Live Search**: Queries local or external SearXNG HTTP endpoints, GDELT 2.0 DOC API, and curated RSS feeds without requiring Docker.
- **Wire-Service Syndication Clustering**: Employs 3-gram character Jaccard similarity to prevent syndicated wire copies (e.g., PTI, ANI, Reuters, AP) from falsely inflating confirmation counts.
- **Multilingual NLI Verifier**: Evaluates premise-hypothesis entailment and contradiction using lightweight transformer models capped to 4 CPU threads.
- **Zero-False-Refutation Policy**: Missing evidence is strictly assigned **`UNVERIFIED`**—the system never assumes a claim is fake simply because corroborating articles are scarce.
- **SSRF-Protected Scraper**: Validates DNS resolutions and every individual redirect hop against private and link-local CIDR ranges.
- **Interactive UI & Progress Monitor**: React 18 single-page application with real-time job status polling, animated progress bars, confidence meters, and filterable quotation cards.

---

## Verdict Categories

TruthLens 2.0 evaluates evidence to produce one of 5 transparent verdicts:

| Verdict | Meaning | Evidence Standard |
| :--- | :--- | :--- |
| **`SUPPORTED`** | Verified Authentic | Corroborated by independent authoritative publishers with consistent facts. |
| **`REFUTED`** | Debunked / False | Directly contradicted or debunked by authoritative investigative sources. |
| **`MIXED`** | Partial / Disputed | Supported in certain aspects but refuted in others; conflicting accounts found. |
| **`OUTDATED`** | Genuine but Historical | Accurate reporting from $\ge 3$ years ago misleadingly recirculated as breaking news. |
| **`UNVERIFIED`** | Insufficient Evidence | Passages lack conclusive entailment or refutation; no definitive confirmation found. |

---

## Multilingual Support (English & Hindi)

TruthLens 2.0 includes a specialized NLP registry and custom normalizers (`backend/app/nlp/`):
- **Devanagari Orthography**: `HindiNormalizer` preserves complete vowel signs (matras: `ा`, `ि`, `ी`, `ु`, `ू`, `े`, `ै`, `ो`, `ौ`), halant/virama (`्`), anusvara (`ं`), and sentence dandas (`।`, `॥`).
- **Code-Mixing (Hinglish)**: Script detection calculates Latin-to-Devanagari character ratios to identify Hinglish news text and route to appropriate tokenizers.
- **Devanagari Numerals**: Automatically translates numerals (`०-९`) to standard digits (`0-9`) while preserving the surrounding semantic context.
- **Extensible Architecture**: Language profile interfaces ready for Bengali (`bn`), Marathi (`mr`), Spanish (`es`), and French (`fr`).

---

## Empirical Benchmarks

### TruthLens 2.0 Multilingual Evaluation Suite
Evaluated against a curated, manually reviewed benchmark of **10 English and 10 Hindi test cases** spanning political, scientific, economic, viral rumors, outdated events, and zero-evidence cases:

| Language | Test Cases | Accuracy | Matra Failures | False Refutations | Benchmark Latency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **English (`en`)** | 10 | **100.0%** (10/10) | N/A | **0** | 0.28s / claim |
| **Hindi (`hi`)** | 10 | **100.0%** (10/10) | **0** | **0** | 0.32s / claim |
| **Overall Pipeline** | 20 | **100.0%** (20/20) | **0** | **0** | 6.06s total |

Full benchmark metrics recorded in `ml/results/multilingual_evaluation_report.json`.

---

### Local Ollama LLM Benchmark
Benchmarked directly on the host machine (**16 GB RAM, Intel integrated graphics, CPU-only**):

| Metric | Measured Observation | Status |
| :--- | :--- | :--- |
| **Model** | `llama3.2:latest` (3.2B parameters, Q4_K_M) | **Selected & Active** |
| **Disk Size** | 2.02 GB | Verified |
| **Peak RAM Footprint Added** | **1,149 MB** (Total: 14.2 GB / 15.7 GB) | Fits 16 GB ceiling |
| **JSON Schema Adherence** | **100%** compliance with Pydantic claim schema | Verified |
| **English Extraction Latency** | 29.30s (cold) / ~14s (warm) | Verified |
| **Hindi Extraction Latency** | 15.54s (warm) | Verified |

Full benchmark data logged in `ml/results/ollama_benchmark_results.json`.

---

### TruthLens 1.0 Legacy ML Classification Benchmark
Evaluated on 6,493 holdout test samples from the ISOT dataset (stratified 80/20 train/test split):

| Model Architecture | Accuracy | Precision | Recall | F1-Score | Latency / Query |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Logistic Regression (Production)** | **97.71%** | **98.31%** | **97.44%** | **97.88%** | **0.0005 ms** |
| Random Forest (Alternative) | 98.12% | 99.10% | 97.42% | 98.25% | 0.0201 ms |
| Neural Network (MLP) | 97.55% | 97.81% | 97.67% | 97.74% | 0.0112 ms |
| K-Nearest Neighbors (KNN) | 91.42% | 91.49% | 92.82% | 92.15% | 0.5059 ms |

---

## Project Structure

```
truthlens/
├── backend/
│   ├── alembic/                      # Database migration scripts (001_initial, 002_evidence_verification)
│   ├── app/
│   │   ├── api/v1/                   # REST Endpoints (auth, analyze, verify, dashboard, models)
│   │   ├── core/                     # Configuration, security, JWT
│   │   ├── database/                 # SQLAlchemy engine, session
│   │   ├── models/                   # User, Article, Analysis, VerificationJob, VerificationClaimRecord
│   │   ├── nlp/                      # Multilingual registry, Hindi & English normalizers
│   │   ├── schemas/                  # Pydantic models (claim, evidence, search, verification)
│   │   ├── services/                 # Claim extractor, search service, evidence collector, NLI verifier, verdict engine, orchestrator
│   │   └── ml/                       # Legacy ML predictors, artifacts, Ollama client
│   └── tests/                        # Pytest suite (NLP, Claim, Search, Evidence, NLI, API, Verification)
├── frontend/
│   ├── src/
│   │   ├── components/               # UI components, modals, alerts, cards
│   │   ├── layouts/                  # Navbar, footer, main layout
│   │   ├── pages/                    # VerifyPage, VerificationReportPage, AnalyzePage, Dashboard, etc.
│   │   ├── services/                 # API clients (verificationApi, api)
│   │   ├── types/                    # TypeScript interfaces (verification, api)
│   │   └── tests/                    # Vitest UI tests (verification, forms, navigation, analyze)
├── ml/
│   ├── experiments/                  # Ollama benchmark, multilingual evaluation pipeline
│   ├── notebooks/                    # Original ML research notebooks (preserved)
│   └── results/                      # Audit results, benchmark outputs
├── ARCHITECTURE.md                   # Complete architectural specification & sequence diagrams
├── README.md                         # Product guide & developer manual
└── pytest.ini                        # Test runner configuration
```

---

## Local Development Quickstart

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** & **npm**
- **Ollama** installed and running locally (`http://127.0.0.1:11434`) with model `llama3.2:latest`

### Step 1: Clone and Configure Environment
```bash
# Copy example environment configuration
cp .env.example .env
```

### Step 2: Install Backend Dependencies
```bash
python -m pip install -r backend/requirements.txt
```

### Step 3: Run Database Migrations
```bash
cd backend
alembic upgrade head
cd ..
```

### Step 4: Pull Local LLM Model (Ollama)
Ensure the Ollama application is active on your host machine:
```bash
ollama pull llama3.2:latest
```

### Step 5: Start the Backend Server
From the project root:
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger): `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

### Step 6: Start the Frontend Application
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:5173`
- Direct Live Verification UI: `http://localhost:5173/verify`

---

## Running the Test Suites

### 1. Comprehensive Backend Unit Tests (46 tests)
Tests NLP normalizers, claim extraction, search service, passage chunking, syndication deduplication, NLI verdict synthesis, and legacy ML preprocessing:
```bash
python -m pytest backend/tests/test_nlp_multilingual.py backend/tests/test_claim_extractor.py backend/tests/test_search_service.py backend/tests/test_evidence_services.py backend/tests/test_nli_verdict_pipeline.py backend/tests/test_ml_preprocessing.py backend/tests/test_ml_predictor.py -v
```

### 2. Backend API Integration Tests (12 tests)
Tests authentication, legacy credibility prediction, user history isolation, and TruthLens 2.0 verification job lifecycle:
```bash
python -m pytest backend/tests/test_api_integration.py backend/tests/test_verification_api.py -v
```

### 3. Frontend Vitest Tests (9 tests)
Tests verification input forms, polling monitor, evidence explorer, authentication forms, and navigation:
```bash
cd frontend
npm test -- --run
```

### 4. Multilingual 20-Case Verification Benchmark Suite
Runs the full end-to-end verification engine across 10 English and 10 Hindi news claims:
```bash
python ml/experiments/evaluate_multilingual_pipeline.py
```

### 5. Frontend Production Build Check
```bash
cd frontend
npm run build
```

---

## API Reference

### TruthLens 2.0: Evidence Verification Endpoints
- `POST /api/v1/verify` — Submit a news text, headline, or URL for live evidence-based verification.
  ```json
  {
    "text": "The Federal Reserve maintained benchmark interest rates at 5.25% on Wednesday.",
    "headline": "Federal Reserve Holds Rates at 5.25%",
    "language": "en"
  }
  ```
  Returns: `{ "job_id": "...", "status": "QUEUED", "progress": 0 }`
- `GET /api/v1/verify/{id}/status` — Poll current job state machine progress (`QUEUED`, `EXTRACTING`, `SEARCHING`, `RETRIEVING`, `VERIFYING`, `GENERATING_REPORT`, `COMPLETED`, `FAILED`).
- `GET /api/v1/verify/{id}` — Retrieve the completed verification audit report with final verdict, claim breakdowns, and evidence quotations.
- `POST /api/v1/verify/{id}/retry` — Safely retry a failed verification job.
- `GET /api/v1/verify` — Paginated history of verification jobs.

### TruthLens 1.0: Legacy Stylistic Analysis Endpoints
- `POST /api/v1/analyze` — Evaluate news credibility from headline, text, or URL using scikit-learn models.
- `GET /api/v1/analyses` — Paginated analysis history.
- `GET /api/v1/analyses/{id}` — Detailed report with token-level Explainable AI attributions.
- `GET /api/v1/dashboard/stats` — Real-time analytics, 7-day volume trends, and credibility distribution.
- `GET /api/v1/models/performance` — Audited classification confusion matrices, F1-scores, and latency.

### Authentication
- `POST /api/v1/auth/register` — Register a new user account.
- `POST /api/v1/auth/login` — Sign in and obtain a JWT bearer token.
- `GET /api/v1/auth/me` — Retrieve the authenticated profile.

---

## Deployment Guide

TruthLens is fully designed for local execution and self-hosting:

### Local / Server Multi-Container (Docker Compose)
To spin up the complete stack with local PostgreSQL:
```bash
docker-compose up --build -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Database: `localhost:5432`

---

## Scientific & Ethical Fact-Checking Advisory

> [!IMPORTANT]
> **Factual Claim Verification vs. Opinion**: TruthLens 2.0 is designed to verify falsifiable factual assertions using corroborated web reporting. It does not judge subjective political viewpoints, satire, or value judgments.
> 
> **Zero-False-Refutation Policy**: Absence of retrieved internet evidence is NEVER treated as proof of falsehood. If the search returns no reputable reporting or evidence is inconclusive, TruthLens assigns **`UNVERIFIED`** rather than claiming an article is fake.
> 
> **Human-in-the-Loop Verification**: Automated verification outputs should serve as an assistive intelligence tool alongside human editorial review and domain expertise.
