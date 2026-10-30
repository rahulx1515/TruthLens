# TruthLens

**Evidence-based, multilingual news and claim verification**

TruthLens is a web application that helps users examine factual claims
in news articles, headlines, URLs, and short text. Instead of deciding
whether a story is true from writing style alone, its primary
verification workflow extracts checkable claims, searches for relevant
external reporting, evaluates evidence with a multilingual
natural-language-inference (NLI) model, and produces a report that users
can inspect.

> **Important:** TruthLens is an assistive verification tool, not an
> authoritative fact-checking organization. Its verdicts depend on the
> quality, availability, language coverage, and freshness of retrieved
> sources. Always inspect the cited sources and use human judgment for
> consequential decisions.

------------------------------------------------------------------------

## Contents

-   [What TruthLens does](#what-truthlens-does)
-   [Features](#features)
-   [Verification workflow](#verification-workflow)
-   [Verdict categories](#verdict-categories)
-   [Languages](#languages)
-   [Architecture and technology](#architecture-and-technology)
-   [Repository structure](#repository-structure)
-   [Local setup](#local-setup)
-   [Configuration](#configuration)
-   [Running the application](#running-the-application)
-   [Tests and evaluation](#tests-and-evaluation)
-   [API overview](#api-overview)
-   [Known limitations](#known-limitations)
-   [Responsible use](#responsible-use)

------------------------------------------------------------------------

## What TruthLens does

A user submits a news article, headline, URL, or claim. TruthLens
attempts to:

1.  Extract individual factual claims that can be checked.
2.  Search external sources for potentially relevant evidence.
3.  retrieve and rank source passages for each claim.
4.  Compare evidence with claims using a multilingual NLI model.
5.  Generate a structured report containing verdicts, evidence,
    quotations, and source links.

The evidence-based verification workflow is the primary product. A
separate legacy machine-learning classifier is retained for comparison
and educational purposes; its stylistic prediction must not be treated
as evidence that a factual claim is true or false.

## Features

-   **Claim extraction:** Uses a locally hosted Ollama model
    (`llama3.2:latest`) when available, with rule-based fallback
    behavior.
-   **Evidence discovery:** Integrates configurable SearXNG search,
    GDELT, and RSS sources.
-   **Evidence retrieval and ranking:** Collects source material and
    ranks passages for relevance to extracted claims.
-   **Multilingual NLI:** Uses
    `MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli` to estimate
    entailment, neutrality, and contradiction between evidence and
    claims.
-   **Source transparency:** Reports source links and supporting
    quotations so users can inspect the underlying material.
-   **Syndication handling:** Attempts to avoid counting near-identical
    syndicated coverage as independent corroboration.
-   **Conservative verdict behavior:** Insufficient evidence should
    result in `UNVERIFIED`, not an automatic false or refuted verdict.
-   **Guest verification support:** Supports guest-session workflows
    with server-issued identifiers and claim tokens.
-   **User experience:** Includes verification progress, report views,
    history, dashboard views, and evidence exploration.
-   **Legacy ML module:** Preserves the earlier TF-IDF/classifier
    workflow as a separate analysis path.

Feature availability can depend on configuration and the external
services reachable from the environment.

## Verification workflow

``` text
User input
   |
   v
Input validation and language handling
   |
   v
Atomic claim extraction
   |
   v
Search query generation and evidence discovery
   |
   v
Publisher-page retrieval and text extraction
   |
   v
Passage ranking and syndication deduplication
   |
   v
Multilingual NLI comparison
   |
   v
Verdict synthesis and report generation
   |
   v
Inspectable verification report
```

Search results are discovery signals, not proof. The verification
pipeline should rely on retrieved source content rather than search
snippets alone. NLI scores are model outputs; they are not probabilities
that a claim is objectively true.

## Verdict categories

  -----------------------------------------------------------------------
  Verdict                             Meaning
  ----------------------------------- -----------------------------------
  `SUPPORTED`                         Retrieved evidence supports the
                                      claim.

  `REFUTED`                           Retrieved evidence directly
                                      contradicts the claim.

  `MIXED`                             Evidence supports some aspects
                                      while contradicting or disputing
                                      others.

  `OUTDATED`                          The claim or report may have been
                                      accurate in the past but is no
                                      longer current in the relevant
                                      context.

  `UNVERIFIED`                        Available evidence is insufficient,
                                      inconclusive, or unavailable.
  -----------------------------------------------------------------------

A verdict is an automated assessment of the evidence retrieved during a
particular run. It can change as sources, search coverage, and the
underlying facts change.

## Languages

The current verification work focuses on:

-   **English (`en`)**
-   **Hindi (`hi`)**, including Devanagari text and normalization of
    Hindi-specific characters.

The NLP layer includes handling for Devanagari vowel signs, virama,
anusvara, danda punctuation, and Devanagari numerals. Hinglish or other
code-mixed text may require additional evaluation and should not be
assumed to have the same reliability as standard English or Hindi input.

The architecture may be extended to other languages, but a language
should only be described as supported after its retrieval sources,
normalization, and verification quality have been evaluated.

## Architecture and technology

  -----------------------------------------------------------------------
  Layer                               Technology
  ----------------------------------- -----------------------------------
  Frontend                            React 18, TypeScript, Vite,
                                      Tailwind CSS

  Backend API                         Python, FastAPI, Pydantic

  Persistence                         SQLAlchemy and Alembic; SQLite for
                                      local use, with
                                      PostgreSQL-compatible configuration

  Local language model                Ollama with `llama3.2:latest`

  Evidence reasoning                  Hugging Face Transformers / PyTorch
                                      multilingual NLI model

  Search and discovery                Configurable SearXNG, GDELT, and
                                      RSS sources

  Legacy classifier                   scikit-learn and TF-IDF
  -----------------------------------------------------------------------

### Important model separation

The evidence-verification workflow is the source of factual verdicts.
The legacy stylistic classifier is a separate feature and must not be
used to override, strengthen, or weaken evidence-based verdicts.

## Repository structure

``` text
TruthLens/
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── app/
│   │   ├── api/v1/              # API routes
│   │   ├── core/                # Configuration and security
│   │   ├── database/            # Database setup and sessions
│   │   ├── models/              # SQLAlchemy models
│   │   ├── nlp/                 # Language handling and normalization
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Extraction, retrieval, NLI, verdicts, reports
│   │   └── ml/                   # Legacy ML and Ollama integration
│   └── tests/                    # Backend tests
├── frontend/
│   └── src/
│       ├── components/           # Reusable UI components
│       ├── layouts/              # Application layouts
│       ├── pages/                # Application pages
│       ├── services/             # Backend API clients
│       ├── types/                # TypeScript types
│       └── tests/                # Frontend tests
├── ml/
│   ├── experiments/              # Evaluation and benchmark scripts
│   ├── notebooks/                # Research notebooks
│   └── results/                  # Evaluation outputs, when present
├── docs/                         # Project documentation and reports
├── .env.example                  # Example environment configuration
└── README.md
```

Some files may differ as the project evolves. Treat the current
repository tree and source code as authoritative.

## Local setup

### Prerequisites

-   Python 3.12+
-   Node.js 18+ and npm
-   Git
-   Ollama, if you want to use local LLM-based claim extraction
-   Sufficient RAM and disk space for the local language and NLI models

### 1. Clone the repository

``` bash
git clone https://github.com/rahulx1515/TruthLens.git
cd TruthLens
```

### 2. Configure environment variables

Copy the example configuration:

**Windows PowerShell**

``` powershell
Copy-Item .env.example .env
```

**macOS / Linux**

``` bash
cp .env.example .env
```

Review `.env.example` and set the values required by your environment.
Do not commit `.env` or paste secrets into issue reports.

### 3. Install backend dependencies

From the repository root:

``` bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**

``` powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
source .venv/bin/activate
```

Install dependencies:

``` bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

### 4. Configure and migrate the database

From the repository root:

``` bash
cd backend
alembic upgrade head
cd ..
```

Make sure the backend environment configuration points to the database
you intend to use. For local development, use the SQLite configuration
supplied by the project.

### 5. Set up Ollama (optional, for local LLM extraction)

Install and start Ollama, then pull the configured model:

``` bash
ollama pull llama3.2:latest
```

Confirm that Ollama is reachable at the configured base URL (commonly
`http://127.0.0.1:11434`). If Ollama is unavailable, the application may
use its configured fallback behavior; LLM-dependent output may differ.

### 6. Install frontend dependencies

``` bash
cd frontend
npm install
cd ..
```

## Configuration

Use `.env.example` as the source of truth for supported environment
variables. Common configuration areas include:

-   Database connection URL
-   JWT/authentication settings
-   Ollama base URL and model name
-   Search provider endpoints and enablement
-   CORS / frontend origin settings
-   Request and retrieval limits

Do not assume a provider is configured just because its integration
exists in the code. Search availability depends on valid configuration
and network access. Never commit credentials, API keys, `.env` files,
private keys, or production secrets.

## Running the application

Open two terminals from the repository root.

### Backend

``` bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

-   API base URL: `http://127.0.0.1:8000`
-   Swagger documentation: `http://127.0.0.1:8000/docs`
-   ReDoc: `http://127.0.0.1:8000/redoc`

The health endpoint is defined by the backend application; check the
route implementation if the path differs in your checkout.

### Frontend

``` bash
cd frontend
npm run dev
```

Vite prints the local URL in the terminal (commonly
`http://localhost:5173`). Open that URL in your browser.

## Tests and evaluation

Run the test suites from the repository root, using the test paths that
exist in your checkout.

### Backend

``` bash
python -m pytest backend/tests -v
```

### Frontend

``` bash
cd frontend
npm test -- --run
```

### Frontend production build

``` bash
npm run build
```

### Evaluation scripts

The `ml/experiments/` directory contains evaluation and benchmark
scripts. Run a script only after checking its inputs, expected runtime,
and output paths. Keep benchmark datasets separate from training data
and document the evaluation method when publishing results.

### Interpreting existing benchmark results

The repository may include small manually curated evaluation sets and
local-machine performance measurements. These are useful for regression
checks, but they do not establish production-grade accuracy or
calibrated confidence. In particular:

-   A result on 10 English and 10 Hindi examples is a small preliminary
    evaluation, not evidence of broad real-world accuracy.
-   Latency and memory measurements depend on hardware, model cache
    state, input length, and batch size.
-   NLI entailment/contradiction scores are not calibrated truth
    probabilities.
-   Legacy classifier metrics apply only to that classifier and its
    evaluation dataset; they do not measure the evidence-verification
    pipeline.

When reporting results, include dataset size, language, sampling method,
hardware, cold/warm state, and the exact command used.

## API overview

The API is versioned under `/api/v1`. The exact request and response
schemas are defined in the backend source and can be inspected through
Swagger at `/docs` while the backend is running.

The verification API includes routes for submitting verification jobs,
checking job status, retrieving reports, retrying eligible failed jobs,
and viewing verification history. Authentication, dashboard, and legacy
analysis routes are also present in the API layer.

Example verification request shape (confirm the current schema in
Swagger before use):

``` json
{
  "text": "Paste a factual claim or news text here.",
  "language": "en"
}
```

## Known limitations

-   **Search coverage:** Search providers can be unavailable,
    rate-limited, incomplete, or biased toward particular publishers and
    languages.
-   **Source quality:** A retrieved page is not automatically
    authoritative. Users should assess the publisher, date, original
    reporting, and context.
-   **Retrieval errors:** Relevant evidence may be missed, and
    irrelevant or duplicated passages may be retrieved.
-   **NLI limitations:** The multilingual NLI model can misread
    negation, dates, numbers, attribution, causality, and nuanced
    language.
-   **Confidence interpretation:** Any confidence value shown by the
    application is a system heuristic unless separately calibrated and
    validated. It must not be interpreted as the probability that a
    claim is true.
-   **Language coverage:** English and Hindi are the primary target
    languages; code-mixed and other-language performance requires
    separate evaluation.
-   **Performance:** Local inference can be slow on CPU-only machines,
    particularly during model loading or long verification runs.
-   **Temporal claims:** Whether a claim is outdated depends on the time
    context and the quality of available dated evidence.
-   **No guarantee of completeness:** A report reflects evidence found
    during that run, not every source that exists.

## Responsible use

TruthLens is designed to assist research and critical reading. It is not
a substitute for professional fact-checking, legal advice, medical
advice, or editorial judgment.

-   Verify important claims against the original sources.
-   Distinguish factual assertions from opinions, predictions, satire,
    and interpretations.
-   Treat `UNVERIFIED` as "not established from the available evidence,"
    not as "false."
-   Do not use an automated verdict as the sole basis for decisions that
    could harm a person or organization.
-   Respect source terms, copyright, privacy, and applicable laws when
    retrieving or sharing content.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE)
for details.
