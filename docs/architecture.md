# GeM TenderLens - System Architecture

**GeM TenderLens** is a Streamlit-based Multi-Agent GenAI application designed for government procurement teams evaluating GeM tenders and vendor proposals. It coordinates isolated ChromaDB vector databases, Pydantic v2 schema validation, PostgreSQL transactional storage, an 8-agent CrewAI workflow, Model Context Protocol (MCP) integrations, and a 4-format report export service.

---

## Architectural Layers

```
                                +-----------------------------------+
                                |     Streamlit UI (App & 5 Pages)  |
                                +-----------------+-----------------+
                                                  |
                                                  v
                                +-----------------+-----------------+
                                |      Services & Validation        |
                                +--------+----------------+---------+
                                         |                |
                     +-------------------+                +-------------------+
                     |                                                        |
                     v                                                        v
+--------------------+--------------------+                +------------------+------------------+
|     CrewAI Multi-Agent Workflow Engine   |                |   ChromaDB Isolated RAG Knowledge   |
| (Tender, Tech, Comm, Risk, Writer Agents)|                |  Base (Tender-isolated Collections) |
+-------------------------+---------------+                +------------------+------------------+
                          |                                                   |
                          v                                                   v
+-------------------------+---------------+                +------------------+------------------+
|   Transactional Database (PostgreSQL /  |                |   Model Context Protocol (MCP)      |
|  SQLite Fallback) & Audit Service       |                |   Server & Client Tools Interface   |
+-----------------------------------------+                +-------------------------------------+
```

---

## Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | Streamlit | 5-screen interactive procurement portal (Workspace, Intake, RAG, Comparison, Review & Export) |
| **Programming Language** | Python 3.11 | Core application logic, text processing, schema validation, and multi-agent pipeline |
| **Multi-Agent Framework** | CrewAI | 8 agent roles, task specifications, crew assembly, orchestration, and execution |
| **Validation Schemas** | Pydantic v2 | Type-safe structured data models for tenders, bids, citations, findings, and audit logs |
| **RAG Vector Database** | ChromaDB | Isolated per-tender collections (`tender_<id>`) with metadata filtering |
| **Embeddings** | Cohere API (`embed-english-v3.0`) / Sentence-Transformers | 1024-dimension embeddings with batching, exponential backoff, and local fallback |
| **LLM Layer** | Mistral AI (`mistral-small-latest`) / LiteLLM | Multi-agent reasoning, field extraction, RAG synthesis, and contract evaluation |
| **File Parsing** | PyMuPDF, python-docx, openpyxl, pandas, email parser | Ingests digital PDFs, Word, Excel, CSV, TXT, and `.eml` emails |
| **Transactional Database** | PostgreSQL / SQLite (SQLAlchemy) | `tenderlens_db` with automatic database creation and local SQLite fallback |
| **Object Storage** | Local Directory (`./data/uploads`) / Cloud Store | Stores original tender documents and vendor proposals as immutable evidence |
| **Report Export** | ReportLab, Jinja/HTML, JSON, Markdown | Generates committee-ready evaluation reports in 4 formats (MD, HTML, JSON, PDF) |
| **External Integration** | MCP (`mcp_server.py`, `mcp_client.py`) & CrewAI Tools | Controlled tools for vector search, proposal extraction, audit logs, and compliance |
| **Observability** | LangSmith | Multi-agent trace logs, latency tracking, and prompt execution telemetry |

---

## Inputs and Outputs Matrix

| Area | Inputs | Outputs |
| :--- | :--- | :--- |
| **Tender Workspace (Stage 1)** | GeM tender reference, bid document, BOQ, specifications, corrigenda | Active workspace registration, requirement matrix, indexed ChromaDB collection |
| **Vendor Intake (Stage 2)** | Vendor emails (`.eml`), quotations, technical proposals, certificates, SLAs | Vendor dossier, extracted structured proposal fields, indexed proposal chunks |
| **RAG Retrieval (Stage 3)** | Active tender reference and reviewer query | Dual-source comparative answer with exact page, clause, and file evidence citations |
| **Technical Review (Stage 4)** | Mandatory tender requirements and vendor claims | Compliance matrix, deviation summaries, scanned PDF flags, unverified claim alerts |
| **Commercial Review (Stage 4)** | BOQ, quoted base price, GST, delivery SLAs, warranty terms | Comparable cost matrix, L-1 ranking, MSE/MII preference evaluation |
| **Final Review & Export (Stage 5)**| Evaluated findings and committee decision sign-offs | Committee decision record, audit log history, 4 export report files (MD, HTML, JSON, PDF) |

---

## CrewAI Multi-Agent Pipeline (8 Agents)

1. **Tender Selection Agent**: Identifies the governing GeM tender package baseline and active corrigenda.  
   *Output*: Confirmed tender baseline reference
2. **Knowledge Base Agent**: Manages text chunking, 9 metadata tags, and vector store embeddings in ChromaDB.  
   *Output*: Searchable tender knowledge base collection
3. **Email Intake Agent**: Processes incoming vendor emails (`.eml`), parses attachment files, and establishes dossiers.  
   *Output*: Structured vendor submission dossier
4. **Accessibility Auditor Agent**: Evaluates page text density and flags scanned non-searchable PDFs.  
   *Output*: Accessibility status and manual OCR review queue flags
5. **RAG Clause Retrieval Agent**: Queries ChromaDB for mandatory tender requirements and vendor proposal evidence.  
   *Output*: Retrieved requirement and proposal evidence context
6. **Technical Compliance Agent**: Maps vendor specifications against mandatory tender clauses with exact page citations.  
   *Output*: Technical compliance matrix
7. **Commercial Analysis Agent**: Normalizes base prices, taxes (GST), warranty, and delivery terms; calculates L-1 ranking and MSE/MII preference logic.  
   *Output*: Commercial comparison matrix
8. **Risk & Evaluation Writer Agent**: Flags low-confidence extractions (<0.7), missing proof certificates, and synthesizes findings into a neutral evaluation pack.  
   *Output*: Reviewer-ready evaluation pack and executive summary

---

## Operational Guardrails

- **No Automated Award**: The system provides evaluation support only. Human procurement officers remain responsible for final sign-off, clarification requests, rejections, and award decisions.
- **Evidence Traceability**: Every material finding includes source evidence citations with filename, page number, clause ID, and excerpt.
- **Review Queue for Low Confidence**: Extraction scores below 0.7 or unverified claims are flagged as `review_required`.
- **Corrigenda Re-evaluation**: Uploading a corrigendum triggers re-indexing and automated re-evaluation of affected tender requirements.
- **Strict Collection Isolation**: ChromaDB collections remain strictly isolated by tender workspace (`tender_<sanitized_id>`).
- **Database Auto-Creation & Fallback**: Automatically creates PostgreSQL database if missing; falls back smoothly to SQLite if PostgreSQL service is unavailable.
- **Immutable Source Evidence**: Original uploaded files remain untouched as legal evidence.
- **OCR Access Boundary**: Scanned or image-only documents are flagged for mandatory human review.
