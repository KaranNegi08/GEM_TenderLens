"""
CrewAI Agent Definitions for GeM TenderLens.
Defines all 8 specialized procurement agents with roles, goals, and backstories.
"""

import os
from typing import Optional, Any
from crewai import Agent, LLM
from utils_logger import get_logger

logger = get_logger(__name__)


def get_crew_llm(
    api_key: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[LLM]:
    """Creates and configures a CrewAI LLM instance for Mistral or Groq providers."""
    groq_key, mistral_key, fallback_key = os.getenv("GROQ_API_KEY"), os.getenv("MISTRAL_API_KEY"), os.getenv("LLM_API_KEY")
    target_provider = (provider or os.getenv("LLM_PROVIDER", "")).lower()

    if target_provider == "groq" or (not target_provider and groq_key):
        chosen_provider = "groq"
        chosen_key = api_key or groq_key or fallback_key
        default_model = os.getenv("GROQ_MODEL") or os.getenv("LLM_MODEL") or "groq/llama-3.3-70b-versatile"
        base_url = "https://api.groq.com/openai/v1"
    elif target_provider == "mistral" or mistral_key or fallback_key or api_key:
        chosen_provider = "mistral"
        chosen_key = api_key or mistral_key or fallback_key
        default_model = os.getenv("MISTRAL_MODEL") or os.getenv("LLM_MODEL") or "mistral/mistral-small-latest"
        base_url = "https://api.mistral.ai/v1"
    else:
        return None

    if not chosen_key or chosen_key == "your_llm_api_key_here":
        logger.warning("No valid LLM API key provided for CrewAI LLM initialization.")
        return None

    chosen_model = model or default_model
    if not any(chosen_model.startswith(prefix) for prefix in [f"{chosen_provider}/", "openai/"]):
        chosen_model = f"{chosen_provider}/{chosen_model}"

    logger.info(f"Initializing CrewAI LLM with provider '{chosen_provider}' and model '{chosen_model}'.")
    try:
        return LLM(model=chosen_model, api_key=chosen_key)
    except Exception as e:
        logger.warning(f"Native LLM initialization failed ({e}). Using OpenAI-compatible endpoint fallback.")
        clean_model = chosen_model.replace(f"{chosen_provider}/", "")
        return LLM(model=f"openai/{clean_model}", api_key=chosen_key, base_url=base_url)


class TenderAgents:
    """
    Factory class for creating all 8 specialized CrewAI procurement agents.

    The 8 Procurement Agents:
        1. Tender Selection Agent: Confirms active tender version & corrigenda.
        2. Knowledge Base Agent: Indexes clauses & tags metadata in ChromaDB.
        3. Email Intake Agent: Parses vendor emails & proposal attachments.
        4. Extraction Agent: Extracts structured prices, tax & warranty data.
        5. Technical Compliance Agent: Evaluates vendor specs against mandatory tender rules.
        6. Commercial Analysis Agent: Ranks vendor bids by total cost and delivery.
        7. Risk & Evidence Agent: Flags compliance gaps & unverified vendor claims.
        8. Evaluation Writer Agent: Compiles committee-ready report with page citations.
    """

    def __init__(
        self,
        llm_api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        llm: Optional[LLM] = None
    ):
        self.api_key = llm_api_key or os.getenv("MISTRAL_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
        self.llm = llm or get_crew_llm(api_key=self.api_key, provider=provider, model=model)

    def _create_agent(self, role: str, goal: str, backstory: str):
        agent_kwargs = {
            "role": role,
            "goal": goal,
            "backstory": backstory,
            "verbose": True,
            "allow_delegation": False
        }
        if self.llm:
            agent_kwargs["llm"] = self.llm
        return Agent(**agent_kwargs)

    def tender_selection_agent(self):
        return self._create_agent(
            role="Tender Selection Agent",
            goal="Identify the governing GeM tender package, confirm active version, and account for corrigenda.",
            backstory="You are a Senior GeM Procurement Specialist expert at evaluating official government tender packages."
        )

    def knowledge_base_agent(self):
        return self._create_agent(
            role="Knowledge Base Agent",
            goal="Chunk tender clauses and populate metadata-rich vectors in ChromaDB.",
            backstory="You are a Vector DB Architect specializing in legal and procurement document chunking and metadata tagging."
        )

    def email_intake_agent(self):
        return self._create_agent(
            role="Email Intake Agent",
            goal="Organize vendor proposal emails, parse attachments, and establish vendor dossiers.",
            backstory="You are a Procurement Intake Coordinator responsible for ingesting vendor proposal communications."
        )

    def extraction_agent(self):
        return self._create_agent(
            role="Extraction Agent",
            goal="Extract structured financial, commercial, and technical fields from vendor submissions.",
            backstory="You are a Data Extraction Specialist adept at pulling exact prices, tax calculations, and warranty terms."
        )

    def technical_compliance_agent(self):
        return self._create_agent(
            role="Technical Compliance Agent",
            goal="Map vendor technical evidence against mandatory tender specifications. Mark a certification/document requirement as Compliant only if a specific certificate number, reference ID, or validity date is present in the vendor's text. If the vendor only makes a general claim without a verifiable reference, mark as Review Required.",
            backstory="You are a Technical Auditor responsible for verifying whether offered vendor products meet mandatory GeM parameters."
        )

    def commercial_analysis_agent(self):
        return self._create_agent(
            role="Commercial Analysis Agent",
            goal="Normalize vendor price quotes, taxes, delivery lead-times, and payment terms into a comparable cost matrix.",
            backstory="You are a Commercial Financial Analyst expert in GeM price evaluation and L-1 determination."
        )

    def risk_and_evidence_agent(self):
        return self._create_agent(
            role="Risk and Evidence Agent",
            goal="Identify compliance gaps, unverified claims, missing certificates, and low-confidence extractions. Flag unverified claims lacking certificate numbers or proof as Review Required.",
            backstory="You are a Procurement Risk Assessor tasked with catching potential discrepancies and raising formal clarification queries."
        )

    def evaluation_writer_agent(self):
        return self._create_agent(
            role="Evaluation Writer Agent",
            goal="Synthesize all agent findings into a neutral, evidence-backed evaluation report with exact citations.",
            backstory="You are an Executive Procurement Committee Secretary responsible for drafting clear comparison reports."
        )
