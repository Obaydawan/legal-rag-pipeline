# Legal RAG Pipeline — Project Guideline & Handoff Brief

**Purpose of this document:** This is the architecture and decision record for `legal-rag-pipeline`, Obaid's flagship LLM/RAG data engineering portfolio project. Claude made the architectural decisions and phase plan below; Gemini's role from here is execution — running commands, writing/debugging code against this spec, and fixing errors as they come up. Treat this document as the source of truth for *what* to build; Gemini handles *how* to get each piece working.

---

## Project goal

Build a production-style RAG (Retrieval-Augmented Generation) pipeline over legal contracts — ingest raw documents, chunk and embed them, store in a vector database, serve retrieval through an API, and evaluate retrieval quality rigorously. This is the highest freelance-demand AI-data-engineering niche not yet covered by Obaid's other projects (EmberRisk, TransactSafe, StreamPulse, ecommerce_pipeline).

**Why this project exists:** Freelancing is the top priority (over scholarships/recruiting). StreamPulse already proves streaming ingestion + NL-to-SQL over structured data; this project proves the *distinct* skill of RAG over unstructured documents — still the highest-demand AI-data niche on freelance platforms.

---

## Domain & dataset (locked decisions — do not change without discussing with Obaid)

- **Domain:** Legal contracts. Chosen over financial filings (SEC EDGAR) and technical documentation based on freelance demand research — legal is a confirmed growth category on Fiverr specifically, and law firms are actively investing in "legal technologist" hybrid roles.
- **Dataset:** [CUAD (Contract Understanding Atticus Dataset)](https://www.atticusprojectai.org/cuad) v1 — 510 real commercial contracts, 13,000+ expert-annotated clause labels across 41 categories (Governing Law, Indemnity, Termination, Confidentiality, etc.), CC BY 4.0 licensed.
- **Why CUAD specifically:** The expert annotations double as a ready-made evaluation set — Phase 4.4's retrieval eval harness needs query → expected-answer pairs, and CUAD provides thousands of these for free instead of requiring hand-written eval questions.

---

## Architecture (locked)

```
RAW CONTRACTS (CUAD .txt files)
        |
        v
AIRFLOW INGEST DAG  ──  chunking (overlap-aware, sentence-boundary-aware)
        |                (must handle real legal-text quirks: page headers,
        |                 signature blocks, all-caps section titles — check
        |                 a few real .txt files before finalizing the chunker)
        v
EMBEDDING  ──  open-source model (bge-small or e5, via sentence-transformers)
        |       incremental — don't re-embed unchanged documents
        v
PGVECTOR  ──  self-hosted Postgres in Docker (no signup, no card — matches
        |      the no-card-tool constraint used across all of Obaid's projects)
        v
RETRIEVAL API  ──  FastAPI, read-only
        |
        v
EVAL HARNESS  ──  precision/recall against CUAD's expert annotations
        |
        v
MONITORING  ──  Streamlit dashboard (pipeline health, index freshness,
                 retrieval metrics — same pattern as TransactSafe/StreamPulse)
```

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | Apache Airflow (Docker) | Consistent with StreamPulse/TransactSafe |
| Chunking | Custom Python (start simple, sentence-aware splitting) | No need for a heavy library at this scale |
| Embeddings | bge-small or e5 via `sentence-transformers` | Open-source, free, no API costs |
| Vector store | pgvector (self-hosted Postgres, Docker) | No signup/card required — matches Obaid's card-free tool constraint |
| Serving | FastAPI | Read-only retrieval endpoint |
| Eval | Custom precision/recall harness against CUAD annotations | Free ground-truth data already exists in the dataset |
| Monitoring | Streamlit | Consistent with all other projects |
| Testing | pytest | Consistent with StreamPulse's testing discipline |
| CI | GitHub Actions | Same pattern as TransactSafe and StreamPulse (see conventions below) |

**No paid or card-requiring services anywhere in this stack.**

---

## Repo

- **Name:** `legal-rag-pipeline`
- **Environment:** WSL2/Ubuntu terminal, Python, standard venv workflow (matches all other projects)
- Local repo path convention: `~/projects/legal-rag-pipeline`

---

## Phase plan

```
[ ] 4.1  Domain & Data Selection — DONE (legal contracts, CUAD dataset)
[ ] 4.2  Ingestion & Chunking Pipeline
         - Scaffold repo, download CUAD into data/raw/
         - Write chunking script (data/raw/*.txt → data/processed/chunks.jsonl)
         - Check real contract text for formatting quirks BEFORE finalizing
           the chunker (page headers, signature blocks, all-caps titles)
         - Wrap in an Airflow DAG (single PythonOperator task to start)
         - Verify: run script directly, spot-check output, then run via Airflow
[ ] 4.3  Embedding & Vector Store
         - Set up pgvector in Docker (self-hosted, no card)
         - Embed chunks with bge-small/e5 via sentence-transformers
         - Incremental indexing — skip re-embedding unchanged documents
         - Add as a second Airflow task after chunking
[ ] 4.4  Retrieval & Evaluation Harness
         - Build eval set from CUAD_v1.json's expert-annotated Q&A pairs
         - Measure precision/recall — this is what proves the pipeline works,
           not just "looks right"
         - This is the step most RAG tutorials skip — don't skip it
[ ] 4.5  Serving Layer & Monitoring
         - FastAPI endpoint: read-only retrieval, query logging, latency
         - Streamlit dashboard: pipeline health, index freshness, retrieval metrics
[ ] 4.6  Freelance Packaging
         - Case-study README (architecture diagram, before/after query examples,
           cost breakdown) — same service-framing pattern as ecommerce_pipeline
         - Post as a fixed-scope Upwork/Fiverr package once complete
```

---

## Project conventions (carried over from Obaid's other projects — follow these)

1. **Testing discipline.** Every layer that transforms data gets tests. TransactSafe has 29+ dbt tests; StreamPulse has 50 automated tests including a dedicated idempotency proof and 21 tests attacking its safety guardrails. This project should have an equivalent real test suite — not just "it ran without crashing."
2. **CI on GitHub Actions.** Both TransactSafe and StreamPulse have working CI (dbt build/test + pytest running on every push). Set this up once the core pipeline is stable — but do it *after* the pipeline works locally first, not before. (Lesson learned the hard way on StreamPulse: a host-bind-mounted Docker volume caused a CI-only crash-loop that took a long debugging session to trace to a permissions mismatch. If this project uses any Dockerized service with persistent data, use a named Docker volume, not a host bind mount, from the start.)
3. **Airflow added after the pipeline is proven stable, not before.** StreamPulse's own engineering journal notes this explicitly: "scheduling untested code just makes failures harder to debug." Get the chunking/embedding scripts working standalone first, then wrap in Airflow.
4. **No paid or card-requiring tools, ever**, unless Obaid explicitly says otherwise. This has been a hard constraint across every project so far.
5. **Document real debugging history**, not just the happy path — StreamPulse's `PROJECT_JOURNAL.md` (documenting a real multi-day DuckDB/MotherDuck auth bug and a Python-version deployment issue) is a model worth following. Freelance clients and recruiters both respond well to evidence of real problem-solving, not just working demos.
6. **Service framing in the final README**, not academic framing. Every other project's README leads with what problem it solves for a client, includes an architecture diagram, and ends with an "available as a service" pitch.

---

## Division of labor

- **Claude:** architecture decisions, phase planning, reviewing diffs/output for correctness, deciding what to prioritize next, writing/updating this guideline document and roadmap files as decisions get made.
- **Gemini:** hands-on execution — writing code against this spec, running commands, debugging errors, fixing issues that come up during implementation.
- **Obaid:** runs commands in the terminal, reports back errors/output, makes final calls when Claude and Gemini disagree.

If Gemini's suggested fix for a problem conflicts with something in this document (architecture, tool choice, or convention), flag it back to Claude before proceeding — don't silently deviate from the locked decisions above.
