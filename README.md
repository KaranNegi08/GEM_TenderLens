GeM TenderLens — Technical & System Documentation
> Enterprise Multi-Agent GenAI Procurement Evaluation Platform
Version: 1.0
Primary Language: Python 3.11
UI Framework: Streamlit
Document Purpose: Architecture, modules, workflow, setup, testing, and governance reference
---
Document Overview
GeM TenderLens is an enterprise-grade, multi-agent GenAI procurement evaluation system designed to analyze Government e-Marketplace (GeM) tender documents and vendor proposals. It combines retrieval-augmented generation, structured validation, multi-agent analysis, deterministic rule-based evaluation, audit logging, and multi-format reporting.
This document describes the system architecture, technology stack, project structure, core modules, procurement workflow, database design, installation process, testing strategy, and operational safeguards.
---
GeM TenderLens is an enterprise-grade, Multi-Agent GenAI procurement evaluation system built for analyzing Government e-Marketplace (GeM) tender documents and vendor proposals. The platform automates tender indexing, proposal field extraction, compliance verification, commercial price normalization (L-1 ranking), risk analysis, and audit-compliant evaluation report generation.
Table of Contents
1.	Executive Summary
2.	System Architecture
3.	Technology Stack
4.	Project Directory Structure
5.	Core System Modules & Services
•	1. Data Schemas (`schemas/`)
•	2. RAG & Vector Engine (`rag/`)
•	3. Core Services Layer (`services/`)
•	4. Multi-Agent Crew Engine (`crew/`)
•	5. Model Context Protocol (`mcp_server.py` & `mcp_client.py`)
•	6. Utility Helpers (`utils/`)
6.	User Interface & 5-Stage Procurement Workflow
7.	Database Schema & Audit Logging
8.	Setup & Installation Guide
9.	Testing & Verification
10.	Operational Safety & Governance Guardrails
Executive Summary
Evaluating procurement proposals for government tenders requires cross-referencing complex Technical Specification Documents (TSDs), Bills of Quantities (BOQ), commercial price schedules, GST rules, warranty terms, and legal corrigenda. Manual evaluation is prone to errors, oversight of technical non-compliance, and delays.
GeM TenderLens solves this by pairing:
•	**Retrieval-Augmented Generation (RAG)** for exact, evidence-backed clause retrieval.
•	**Pydantic v2 Schema Validation** for structured financial and technical data ingestion.
•	**8-Agent CrewAI Engine** with dual execution modes (AI Multi-Agent vs. Deterministic Rule Engine fallback).
•	**Model Context Protocol (MCP)** standard server/client interface for JSON-RPC 2.0 tool invocation.
•	**4-Format Report Export Service** (ReportLab PDF, HTML/CSS, Markdown, and structured JSON).
🏗️ System Architecture
+-----------------------------------------------------------------------------------+
|                            Streamlit Web Portal (App & 5 Pages)                    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                               Services Layer & Pydantic v2                        |
|  (TenderService, VendorService, ComparisonService, ExportService, AuditService)  |
+--------------------+--------------------+--------------------+--------------------+
                     |                    |                    |
                     v                    v                    v
+--------------------+----+  +------------+-------+  +---------+--------------------+
|  CrewAI Multi-Agent     |  | RAG Engine         |  | Model Context Protocol     |
|  Engine (8 Agents)      |  | (ChromaDB +        |  | (MCP Server & Client      |
|  AI + Rule Fallback   |  |  Embeddings)       |  |  JSON-RPC 2.0 Interface)   |
+--------------------+----+  +------------+-------+  +---------+--------------------+
                     |                    |                    |
                     +--------------------+--------------------+
                                          |
                                          v
+-----------------------------------------+-----------------------------------------+
|                  PostgreSQL / SQLite Database & Data Storage                       |
|                 (Raw Uploads, Evaluation Records, Audit Logs)                     |
+-----------------------------------------------------------------------------------+
🛠️ Technology Stack
| Component | Technology | Description |
| :--- | :--- | :--- |
| Frontend UI | Streamlit 1.30+ | 5-screen interactive procurement workspace with state preservation |
| Language | Python 3.11 | Core business logic, parsing, and async management |
| Multi-Agent Framework | CrewAI 0.100+ | 8 specialized roles, sequential task assembly, and execution |
| Data Validation | Pydantic v2 | Type-safe schemas for tenders, submissions, proposals, and findings |
| Vector DB | ChromaDB | Isolated per-tender collections (`tender_<sanitized_id>`) |
| Embeddings | Cohere / Sentence-Transformers | 1024-dim embeddings with exponential backoff & local fallback |
| LLM Orchestration | Mistral AI / Groq / LiteLLM | Multi-agent reasoning, field extraction, and RAG synthesis |
| File Parser | PyMuPDF, python-docx, openpyxl, pandas | Ingests PDF, DOCX, XLSX, CSV, TXT, and `.eml` emails |
| Transactional DB | PostgreSQL / SQLite | SQLAlchemy ORM with auto-creation & SQLite fallback |
| Export Service | ReportLab, Jinja2, JSON, Markdown | Generates executive committee reports in 4 formats |
| External API | MCP (Model Context Protocol) | JSON-RPC 2.0 standardized tool and resource interface |
| Telemetry | LangSmith | Multi-agent trace logs, latency tracking, and LLM telemetry |
📁 Project Directory Structure
Gem_Tender_Project/
├── app.py                      # Main Streamlit landing page & global state initializer
├── mcp_server.py               # Standard MCP JSON-RPC 2.0 Server
├── mcp_client.py               # MCP Client implementation
├── utils_logger.py             # Centralized logging configuration
├── requirements.txt            # Python dependencies
├── crew/                       # CrewAI Multi-Agent Architecture
│   ├── __init__.py
│   ├── agents.py               # 8 Procurement Agent definitions & LLM factory
│   ├── tasks.py                # Agent task specifications & prompts
│   ├── tender_crew.py          # Workflow assembly, execution & rule engine fallback
│   └── tools.py                # Custom tools (TenderSearchTool, ProposalExtractorTool)
├── rag/                        # Retrieval-Augmented Generation Engine
│   ├── __init__.py
│   ├── chroma_client.py        # Persistent ChromaDB client manager
│   ├── chunking.py             # Sliding-window chunker with 9 metadata tags
│   ├── document_loader.py      # Multi-format document parser (PDF, DOCX, XLSX, EML)
│   ├── embeddings.py           # Cohere & Sentence-Transformers embedding pipeline
│   └── retriever.py            # Evidence-backed RAG search engine with page citations
├── schemas/                    # Pydantic v2 Data Validation Schemas
│   ├── __init__.py
│   ├── audit.py                # Audit log schema
│   ├── evaluation.py           # Technical compliance & evidence schemas
│   ├── tender.py               # Tender package & requirement matrix schemas
│   └── vendor.py               # Vendor submission & proposal schemas
├── services/                   # Business Services & Persistence Layer
│   ├── __init__.py
│   ├── audit_service.py        # Transactional audit log persistence
│   ├── comparison_service.py   # L-1 determination, commercial cost matrix & risk engine
│   ├── database.py             # SQLAlchemy engine setup & DB auto-creation
│   ├── db_models.py            # ORM Database tables (Tenders, Submissions, Audits)
│   ├── export_service.py       # 4-format report generator (PDF, HTML, MD, JSON)
│   ├── tender_service.py       # Tender package management & corrigendum handling
│   ├── validation_service.py   # Cross-schema integrity validator
│   └── vendor_service.py       # Vendor intake, email parsing, dossier creation
├── utils/                      # Helper Functions & System Utilities
│   ├── __init__.py
│   ├── evaluator_helper.py     # Rule-based compliance evaluation helpers
│   ├── gst_helper.py           # GST normalization & calculation logic
│   ├── proposal_extractor.py   # Regex & heuristic price/warranty/delivery extractor
│   ├── session_state.py        # Streamlit state initialization helper
│   └── status_badges.py        # UI HTML status pill generators
├── pages/                      # Streamlit Multi-Page UI Screens
│   ├── 1_tender_workspace.py   # Active Tender selection, uploading & requirement indexing
│   ├── 2_vendor_intake.py      # Vendor submission ingestion & field extraction
│   ├── 3_rag_search.py         # Semantic search portal with clause citations
│   ├── 4_vendor_comparison.py  # Multi-agent/Rule comparison & L-1 cost matrix
│   └── 5_review_export.py      # Committee decision sign-off & report export portal
├── docs/                       # System Architecture & Documentation
│   ├── architecture.md
│   └── PROJECT_DOCUMENTATION.md
└── tests/                      # Automated Test Suite (18 Test Files, 47 Tests)
⚙️ Core System Modules & Services
1. Data Schemas (`schemas/`)
Built with Pydantic v2 to ensure type safety:
•	**`tender.py`**: `TenderRequirement` (clause ID, category, mandatory status) and `TenderPackage` (metadata, documents, requirements).
•	**`vendor.py`**: `VendorSubmission` (vendor details, timestamps, attachment paths) and `VendorProposal` (quoted amount, tax, delivery, warranty, technical claims, certificates).
•	**`evaluation.py`**: `EvidenceCitation` (file, page, clause ID, quote) and `EvaluationFinding` (status: `compliant`, `non_compliant`, `review_required`).
•	**`audit.py`**: `AuditLog` (action type, actor, timestamp, details).
2. RAG & Vector Engine (`rag/`)
•	**`chroma_client.py`**: Manages persistent ChromaDB vector collections isolated per tender (`tender_<sanitized_id>`).
•	**`chunking.py`**: Implements fixed-size sliding-window chunking (default 500 chars with 100 overlap) and attaches 9 metadata tags (tender_id, filename, file_type, page_number, clause_id, section, requirement_type, category, vendor_id).
•	**`document_loader.py`**: Ingests PDF (PyMuPDF), DOCX, XLSX/CSV (Pandas), TXT, and `.eml` email files. Flags low-density scanned PDFs for OCR review.
•	**`embeddings.py`**: Dual-mode embedding engine using Cohere API (`embed-english-v3.0`, 1024 dims) with exponential backoff and automatic local `SentenceTransformers` fallback.
•	**`retriever.py`**: Queries ChromaDB for specific tender requirements and returns top matches formatted with evidence citations.
3. Core Services Layer (`services/`)
•	**`tender_service.py`**: Registers tender packages, extracts requirements, handles corrigenda updates, and updates vector store indexes.
•	**`vendor_service.py`**: Ingests vendor email attachments, runs proposal field extraction, and builds structured vendor dossiers.
•	**`comparison_service.py`**:
•	Normalizes base price, GST taxes, delivery timelines, and warranty terms.
•	Computes **Financial L-1** vs. **Technically Qualified L-1**.
•	Evaluates Micro and Small Enterprises (MSE) / Make in India (MII) preference rules.
•	Generates technical compliance matrix and risk queue.
•	**`export_service.py`**: Exports evaluation reports in 4 formats: ReportLab PDF, styled HTML/CSS, clean Markdown, and raw JSON.
•	**`audit_service.py`**: Records immutable procurement audit events into PostgreSQL/SQLite.
•	**`validation_service.py`**: Enforces strict validation checks across tenders and submissions.
•	**`database.py` & `db_models.py`**: Manages SQLAlchemy ORM models (`TenderModel`, `SubmissionModel`, `AuditLogModel`) with automatic PostgreSQL database creation and SQLite fallback.
4. Multi-Agent Crew Engine (`crew/`)
The system employs an 8-Agent Pipeline:
11.	**Tender Selection Agent**: Confirms active tender version and corrigenda.
12.	**Knowledge Base Agent**: Indexes clauses and metadata in ChromaDB.
13.	**Email Intake Agent**: Processes incoming vendor emails and attachments.
14.	**Extraction Agent**: Extracts financial, tax, warranty, and delivery fields.
15.	**Technical Compliance Agent**: Maps specifications against mandatory rules.
16.	**Commercial Analysis Agent**: Ranks vendor bids by total cost and delivery.
17.	**Risk & Evidence Agent**: Flags compliance gaps and missing proof.
18.	**Evaluation Writer Agent**: Compiles committee-ready report with page citations.
Dual-Mode Execution:
•	**Mode A (CrewAI AI Workflow)**: Active when LLM API key (Mistral/Groq) is present.
•	**Mode B (Deterministic Rule Engine)**: Fallback execution when offline or without API key.
5. Model Context Protocol (`mcp_server.py` & `mcp_client.py`)
Implements standard Model Context Protocol (MCP) via JSON-RPC 2.0:
•	**`tools/list`**: Exposes registered tools (`vector_search`, `extract_proposal`, `parse_vendor_email`, `list_tenders`).
•	**`tools/call`**: Executes requested tool with input arguments.
•	**`resources/list` & `resources/read`**: Lists and retrieves tender package resources.
6. Utility Helpers (`utils/`)
•	**`proposal_extractor.py`**: Standardized regex & heuristic extraction of prices, GST, delivery days, warranty, and certificates.
•	**`evaluator_helper.py`**: Rule-based technical evaluation logic.
•	**`gst_helper.py`**: GST rate normalization and inclusion checks.
•	**`session_state.py`**: Centralized Streamlit session state management.
•	**`status_badges.py`**: HTML status pills for UI rendering.
🖥️ User Interface & 5-Stage Procurement Workflow
 app.py (Main Landing Page) 
          |
          +--->  Page 1: Tender Workspace  ---> Upload/Select Tender & Index Documents
          |
          +--->  Page 2: Vendor Intake     ---> Process Vendor Submissions & Proposals
          |
          +--->  Page 3: Tender RAG Search ---> Query Clauses with Page/File Citations
          |
          +--->  Page 4: Vendor Comparison ---> Run 8-Agent Crew / Rule Engine & L-1 Matrix
          |
          +--->  Page 5: Review & Export   ---> Sign-off Committee Decision & Export Reports
19.	**Page 1: Tender Workspace**: Upload or select GeM tender documents, view requirement matrix, upload corrigenda, and trigger vector indexing.
20.	**Page 2: Vendor Intake**: Parse incoming vendor `.eml` emails or proposal files (PDF/DOCX), review extracted prices/taxes, and build dossiers.
21.	**Page 3: Tender RAG Search**: Perform natural language queries against indexed tender clauses and vendor claims with full evidence citations.
22.	**Page 4: Vendor Comparison**: Trigger multi-agent or rule evaluation, compare Financial vs. Qualified L-1 bids, inspect MSE preferences, and view risk flags.
23.	**Page 5: Review & Export**: Record committee decisions, inspect timestamped audit trail, and download evaluation packages in PDF, HTML, MD, or JSON.
🗄️ Database Schema & Audit Logging
Database tables defined in `services/db_models.py`:
•	**`tenders`**: `tender_id` (PK), `title`, `category`, `status`, `created_at`, `requirements_json`, `documents_json`.
•	**`vendor_submissions`**: `id` (PK), `vendor_id`, `vendor_name`, `tender_id`, `received_at`, `proposal_data_json`, `attachment_paths_json`.
•	**`audit_logs`**: `log_id` (PK), `timestamp`, `actor`, `action_type`, `details_json`.
🚀 Setup & Installation Guide
Prerequisites
•	Python 3.11+
•	Virtual Environment (`venv`)
Installation Steps
# 1. Clone repository
git clone https://github.com/KaranNegi08/GEM_TenderLens.git
cd GEM_TenderLens

# 2. Create and activate virtual environment
python -m venv .venv
# On Windows:
.venvScriptsactivate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install required packages
pip install -r requirements.txt

# 4. Configure Environment Variables (.env)
cp .env.example .env  # or edit .env
Environment Configuration (`.env`)
MISTRAL_API_KEY=your_mistral_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
DATABASE_URL=sqlite:///./tenderlens.db  # or postgresql://user:pass@localhost:5432/tenderlens_db
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
Running the Web Application
streamlit run app.py
Testing the MCP Interface
python mcp_server.py
python mcp_client.py
🧪 Testing & Verification
The project features a comprehensive unit & integration test suite (18 test files, 47 test cases):
# Run full test suite
python -m pytest tests/

# Run individual module tests
python -m pytest tests/test_mcp_interface.py
python -m pytest tests/test_schemas.py
python -m pytest tests/test_vendor_service_fixes.py
🔐 Operational Safety & Governance Guardrails
24.	**Human-in-the-Loop Sign-off**: GeM TenderLens is a decision-support system. Final procurement contract awards must be signed off by human procurement officers.
25.	**Strict Evidence Traceability**: Every finding includes exact document citations (file name, page number, clause reference).
26.	**Review Flags for Low Confidence**: Extraction confidence scores below `0.70` or unverified vendor claims trigger mandatory human review alerts.
27.	**Isolated Vector Storage**: Each tender workspace operates within a strictly isolated ChromaDB collection (`tender_<id>`), preventing cross-tender data leakages.
28.	**Immutable Audit Trail**: All key actions (intake, search, crew evaluation runs, report exports) produce timestamped audit logs.
