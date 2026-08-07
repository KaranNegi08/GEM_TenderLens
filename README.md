🚀 GeM TenderLens — Multi-Agent Tender Proposal Comparison System

GeM TenderLens is an enterprise-oriented GenAI procurement evaluation system that helps procurement teams analyze vendor proposals against official Government e-Marketplace (GeM) tender requirements.

The system combines RAG, CrewAI multi-agent orchestration, ChromaDB, Mistral AI, Cohere, PostgreSQL, MCP, Pydantic v2, Streamlit, and LangSmith to provide evidence-backed technical and commercial evaluation.

It supports multi-format document ingestion, clause-level retrieval with citations, vendor comparison, compliance analysis, audit trails, human-in-the-loop review, and committee-ready report exports.

Important: GeM TenderLens is a decision-support system. Final procurement and award decisions remain with authorized procurement officials.

✨ Key Features

📑 Tender Workspace & Versioning

Select and manage governing GeM tender documents.

Handle bid documents, technical specifications, BOQ files, and corrigenda.

Maintain isolated ChromaDB collections for each tender.

📂 Multi-Format Vendor Intake

Supports .eml, .pdf, .docx, .xlsx, .csv, and .txt.

Extracts structured vendor proposal information such as price, GST, delivery SLA, and warranty.

🔍 RAG-Based Clause Search

Searches both tender requirements and vendor proposal content.

Provides source file, page number, clause ID, and excerpt-level evidence.

Uses keyword boosting to improve retrieval of exact procurement terms.

🤖 8-Agent CrewAI Evaluation Pipeline

Tender Selection Agent

Knowledge Base Agent

Email Intake Agent

Accessibility Auditor Agent

RAG Clause Retrieval Agent

Technical Compliance Evaluator

Commercial Analysis Agent

Risk & Evaluation Writer Agent

🛡️ Guardrails & Human-in-the-Loop

Detects scanned/image-only documents.

Flags inaccessible documents for manual review.

Requires reviewer sign-off before final procurement decisions.

Maintains evidence traceability and audit logs.

💰 Commercial Comparison

Normalized vendor price comparison.

L-1 ranking.

GST comparison.

Delivery SLA and warranty comparison.

MSE/MII preference handling.

🔄 Deterministic Fallback

Provides a rule-based comparison engine when LLM credentials are unavailable or API calls fail.

🗄️ PostgreSQL + SQLite Fallback

Stores workspace metadata, reviewer actions, and audit logs.

Automatically creates the application database when required.

Falls back to local SQLite when PostgreSQL is unavailable.

🔌 Model Context Protocol (MCP)

Exposes controlled tools for vector search, proposal extraction, compliance validation, and audit logging.

📊 LangSmith Observability

Supports multi-agent execution tracing, prompt telemetry, and token usage tracking.

📤 Committee-Ready Exports

Markdown (.md)

HTML (.html)

JSON (.json)

PDF (.pdf)

🏗️ System Architecture

                         ┌─────────────────────┐
                         │   Streamlit UI      │
                         │  5-Stage Workflow   │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
     Tender Documents       Vendor Proposals        Reviewer Actions
             │                      │                      │
             └──────────────┬───────┴──────────────────────┘
                            ▼
                  ┌───────────────────┐
                  │ Document Processing│
                  │ & Validation       │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ Chunking +        │
                  │ Metadata          │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ ChromaDB           │
                  │ Isolated per Tender│
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ Dual-Source RAG   │
                  │ Tender + Vendor   │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ CrewAI             │
                  │ 8-Agent Evaluation │
                  └─────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Compliance      Commercial       Risk &
       Evaluation      Comparison       Findings
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                  ┌───────────────────┐
                  │ Reviewer Sign-Off │
                  │ + Audit Trail     │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ Report Export     │
                  │ MD / HTML / JSON  │
                  │ PDF               │
                  └───────────────────┘

🧰 Technology Stack

Category

Technology

Frontend

Streamlit

Language

Python 3.11+

Agent Framework

CrewAI

LLM

Mistral AI

Embeddings

Cohere / SentenceTransformers fallback

Vector Database

ChromaDB

Data Validation

Pydantic v2

Database

PostgreSQL

Local Fallback DB

SQLite

ORM

SQLAlchemy

Agent Communication / Tools

MCP

Observability

LangSmith

PDF Export

ReportLab

Testing

Pytest

Document Formats

PDF, DOCX, XLSX, CSV, EML, TXT

📁 Project Structure

gem-tenderlens/
│
├── app.py
├── flow.txt
├── mcp_server.py
├── mcp_client.py
├── run_tests.py
├── utils_logger.py
├── requirements.txt
├── README.md
├── .env
│
├── pages/
│   ├── 1_tender_workspace.py
│   ├── 2_vendor_intake.py
│   ├── 3_rag_search.py
│   ├── 4_vendor_comparison.py
│   └── 5_review_export.py
│
├── schemas/
│   ├── tender.py
│   ├── vendor.py
│   ├── evaluation.py
│   └── audit.py
│
├── rag/
│   ├── chroma_client.py
│   ├── document_loader.py
│   ├── chunking.py
│   ├── embeddings.py
│   └── retriever.py
│
├── crew/
│   ├── agents.py
│   ├── tasks.py
│   ├── tender_crew.py
│   └── tools.py
│
├── services/
│   ├── tender_service.py
│   ├── vendor_service.py
│   ├── comparison_service.py
│   ├── database.py
│   ├── db_models.py
│   ├── audit_service.py
│   ├── export_service.py
│   └── validation_service.py
│
├── data/
│   ├── chroma_db/
│   ├── uploads/
│   └── create_sample_data.py
│
├── docs/
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── api_integrations.md
│   ├── architecture.md
│   ├── chromadb_strategy.md
│   ├── deployment.md
│   └── schemas.md
│
├── tests/
│
└

⚙️ Prerequisites

Before running the project, make sure you have:

Python 3.11+

PostgreSQL (optional because SQLite fallback is available)

Mistral AI API key

Cohere API key

LangSmith API key (optional, for observability)

🚀 Installation

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd gem-tenderlens

2. Create a virtual environment

Windows

python -m venv .venv
.venv\Scripts\activate

Linux / macOS

python3 -m venv .venv
source .venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

🔐 Environment Configuration

Create a .env file in the project root.

# Mistral
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_MODEL=mistral-small-latest

# Cohere
COHERE_API_KEY=your_cohere_api_key
COHERE_MODEL=embed-english-v3.0

# PostgreSQL
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/tenderlens_db

# Storage
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
STORAGE_BUCKET=./data/uploads

# LangSmith
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=gem-tenderlens

⚠️ Security

Never commit .env or API keys/passwords to GitHub.

Add the following to .gitignore:

.env
.venv/
__pycache__/
*.pyc

data/chroma_db/
data/uploads/
data/*.db

.pytest_cache/
.streamlit/secrets.toml

🧪 Generate Sample Data

The project includes a sample-data generator.

python data/create_sample_data.py

✅ Run Tests

Run the complete test suite:

python run_tests.py

Or use Pytest directly:

pytest tests/ -v

▶️ Run the Application

Start the Streamlit application:

streamlit run app.py

The application provides a five-stage procurement workflow.

🔄 Application Workflow

Stage 1 — Tender Workspace

Select or enter a GeM Tender ID.

Upload the official tender package.

Upload specifications, BOQ, and corrigenda when applicable.

Extract requirements and metadata.

Build an isolated ChromaDB collection.

Tender Package
      ↓
Document Loader
      ↓
Chunking
      ↓
Metadata Extraction
      ↓
Embeddings
      ↓
ChromaDB

Stage 2 — Vendor Intake

Vendor proposal emails and documents are ingested and converted into structured proposal dossiers.

Extracted information can include:

Quoted Price

GST

Delivery SLA

Warranty

Proposal claims

Document accessibility status

Vendor proposal chunks are stored with:

document_type = "vendor_proposal"

Stage 3 — RAG Clause Search

Users can ask natural-language procurement questions such as:

What is the warranty and payment term requirement?

The retriever searches:

Tender Requirements
        +
Vendor Proposals
        ↓
Relevant Evidence
        ↓
Mistral AI Synthesis
        ↓
Answer + Citations

Evidence includes:

Source file

Page number

Clause ID

Relevant excerpt

Stage 4 — Vendor Comparison

The CrewAI evaluation pipeline analyzes vendors for:

Technical Compliance

Requirement
    ↓
Vendor Evidence
    ↓
Compliance Evaluation
    ↓
Finding + Citation

Commercial Comparison

The system normalizes vendor commercial information and compares:

Base price

GST

Total price

L-1 ranking

Delivery SLA

Warranty

Applicable MSE/MII preference

If LLM execution fails, the deterministic comparison service can be used as a fallback.

Stage 5 — Review & Export

Reviewers can:

Approve findings

Reject findings

Request clarification

Record committee decisions

Review audit logs

Export the final evaluation package

Supported exports:

Markdown
HTML
JSON
PDF

🤖 Multi-Agent Architecture

The CrewAI pipeline contains eight specialized agents:

Agent

Responsibility

Tender Selection Agent

Selects and manages the governing tender package

Knowledge Base Agent

Builds and manages tender knowledge

Email Intake Agent

Processes vendor proposal emails

Accessibility Auditor

Detects scanned/inaccessible documents

RAG Clause Retrieval Agent

Retrieves clause-level evidence

Technical Compliance Agent

Evaluates technical requirements

Commercial Analysis Agent

Performs normalized commercial comparison

Risk & Evaluation Writer

Produces findings and evaluation output

This separation allows each agent to focus on a specific procurement responsibility instead of relying on one general-purpose agent.

🔍 RAG Design

GeM TenderLens uses a dual-source retrieval strategy.

                 User Query
                     │
                     ▼
              Query Processing
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
 Tender Requirement       Vendor Proposal
     Chunks                    Chunks
          │                     │
          └──────────┬──────────┘
                     ▼
              Hybrid Retrieval
                     │
             Keyword Boosting
                     │
                     ▼
              Relevant Evidence
                     │
                     ▼
             Mistral AI Synthesis
                     │
                     ▼
           Answer + Source Citations

Each tender maintains an isolated vector collection using a tender-specific identifier such as:

tender_<tender_id>

This helps prevent cross-tender retrieval contamination.

🛡️ Guardrails

1. Human-in-the-Loop

AI recommendations are decision support only. Authorized procurement officials make final award decisions.

2. Evidence Traceability

Material findings are linked to source evidence such as:

Source File
Page Number
Clause ID
Excerpt

3. Scanned Document Detection

Scanned or image-only documents are flagged for manual review.

is_scanned = True

4. Tender Isolation

Each tender uses its own vector collection:

tender_<id>

5. LLM Failure Fallback

If an LLM/API call fails, the system can use deterministic rule-based comparison logic where supported.

6. Database Fallback

PostgreSQL is the primary database, with SQLite available as a local fallback.

🗄️ Data & Persistence

ChromaDB

Used for:

Tender requirement chunks

Vendor proposal chunks

Semantic retrieval

Tender-specific vector isolation

PostgreSQL

Used for transactional information such as:

Tender workspaces

Reviewer actions

Audit logs

Evaluation metadata

SQLite

Used as a fallback when PostgreSQL is unavailable.

📊 Example Evaluation Flow

Official Tender
      │
      ├── Technical Requirements
      ├── Commercial Requirements
      ├── Delivery Requirements
      └── Warranty / Payment Terms
              │
              ▼
        Knowledge Base
              │
              ▼
       Vendor Proposals
              │
              ▼
       RAG Evidence Retrieval
              │
              ▼
       CrewAI Evaluation
              │
       ┌──────┴───────┐
       ▼              ▼
Technical          Commercial
Compliance         Comparison
       │              │
       └──────┬───────┘
              ▼
       Risk & Findings
              │
              ▼
       Human Review
              │
              ▼
     Committee Decision
              │
              ▼
       Final Evaluation

📤 Export Formats

The system can generate committee-ready evaluation packages in:

Format

Purpose

Markdown

Developer/reviewer-friendly report

HTML

Browser-based report

JSON

Machine-readable evaluation output

PDF

Committee-ready document

🧪 Testing

The project contains unit and integration tests covering major application components.

Run:

pytest tests/ -v

or:

python run_tests.py

📚 Documentation

Additional project documentation is available under the docs/ directory:

docs/
├── SYSTEM_ARCHITECTURE.md
├── api_integrations.md
├── architecture.md
├── chromadb_strategy.md
├── deployment.md
└── schemas.md

🔐 Production Security Recommendations

Before deploying this project to production:

Store secrets using environment variables or a secret manager.

Never commit API keys, database passwords, or .env files.

Restrict database access.

Enable authentication and authorization for procurement users.

Encrypt sensitive uploaded documents.

Implement access control between procurement teams/tenants.

Configure secure logging and monitoring.

Review all AI-generated findings before official procurement decisions.

🚢 Deployment

Deployment manifests are provided under:

deployment/
├── Dockerfile
├── railway.json
└── render.yaml

The project documentation also contains deployment guidance for supported environments.

🎯 Project Goals

GeM TenderLens is designed to reduce the manual effort involved in:

Reading large tender documents

Finding mandatory clauses

Comparing vendor proposals

Validating technical compliance

Normalizing commercial offers

Tracking reviewer decisions

Maintaining evidence traceability

Preparing committee evaluation reports

The goal is not to replace procurement officers, but to provide them with a faster, traceable, and evidence-backed evaluation workflow.

👨‍💻 Author

Karan Negi

Data Engineering / GenAI Developer

Interests:

Data Engineering

Generative AI

RAG Systems

Agentic AI

AWS

Python

PySpark

Data Pipelines

⭐ Future Enhancements

Potential future improvements include:

Advanced OCR integration for scanned tender documents

Fine-grained role-based access control

Multi-tenant cloud deployment

Advanced evaluation benchmarks for agent accuracy

Automated procurement policy validation

Improved multilingual document processing

Real-time procurement workflow notifications

Enhanced dashboard analytics

📄 License

Add your preferred open-source or proprietary license before publishing the repository.

⭐ Support

If you find the project useful, consider giving the repository a ⭐ on GitHub.
