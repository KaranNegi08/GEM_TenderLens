"""
Crew Assembly & Workflow Execution Manager.
Orchestrates CrewAI agent pipeline with deterministic fallback execution.
"""

import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from utils_logger import get_logger

load_dotenv()
logger = get_logger(__name__)

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class TenderEvaluationCrew:
    """
    Orchestrates the multi-agent comparison workflow for GeM TenderLens.

    Execution Pathways (2 Modes):
        Mode A (CrewAI Multi-Agent Workflow):
            - Used when an LLM API key (Mistral) is configured.
            - Assembles 5 active agents (Selection, Technical, Commercial, Risk, Writer) in sequential order.
        
        Mode B (Deterministic Fallback Analyzer):
            - Used when running offline or without an API key.
            - Runs structured comparison rules to produce accurate tables & risk flags.
    """

    def __init__(
        self,
        tender_id: str,
        api_key: Optional[str] = None,
        comparison_service: Optional[Any] = None
    ):
        self.tender_id = tender_id
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("LLM_API_KEY")
        
        if comparison_service is None:
            from services.comparison_service import ComparisonService
            self.comparison_service = ComparisonService()
        else:
            self.comparison_service = comparison_service

    @traceable(name="Multi-Agent Evaluation Crew")
    def run_full_evaluation(self, document_list: List[str], vendor_dossiers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes the complete multi-agent evaluation workflow.
        Tries CrewAI execution first if API key is provided, otherwise falls back gracefully.
        """
        logger.info(f"Initiating full evaluation pipeline for tender '{self.tender_id}' with {len(vendor_dossiers)} vendors.")

        # Step 1: Check for valid LLM API key
        if self.api_key and self.api_key not in ["your_llm_api_key_here", "your_mistral_api_key_here"]:
            try:
                # Step 2A: Run multi-agent AI crew
                logger.info("Executing CrewAI multi-agent workflow with LLM API credentials...")
                result = self._run_crewai_crew(document_list, vendor_dossiers)
            except (ImportError, RuntimeError, ValueError) as e:
                # Step 2B: Fallback to rule engine if API or crew execution failure occurs
                logger.warning(f"CrewAI execution unavailable or failed ({type(e).__name__}: {e}). Falling back to deterministic evaluation engine.")
                result = self._run_deterministic_fallback(document_list, vendor_dossiers)
            except Exception as e:
                # Log unexpected errors while maintaining resilient deterministic fallback
                logger.exception(f"Unexpected error during CrewAI execution: {e}. Falling back to deterministic evaluation engine.")
                result = self._run_deterministic_fallback(document_list, vendor_dossiers)
        else:
            # Step 2C: Run rule engine directly when offline
            logger.info("No LLM API Key configured. Running deterministic service evaluation pipeline.")
            result = self._run_deterministic_fallback(document_list, vendor_dossiers)

        # Audit Log: Record evaluation crew execution event
        try:
            from services.audit_service import DatabaseAuditService
            from schemas.audit import AuditLog
            import uuid

            exec_mode = result.get("execution_mode", "CrewAI Multi-Agent Workflow")
            audit_log = AuditLog(
                log_id=f"AUDIT_{uuid.uuid4().hex[:12].upper()}",
                actor="TenderEvaluationCrew",
                action_type="COMPLIANCE_RUN",
                details={
                    "tender_id": self.tender_id,
                    "total_vendors": len(vendor_dossiers),
                    "execution_mode": exec_mode
                }
            )
            DatabaseAuditService.save_audit_log(audit_log)
        except Exception as audit_err:
            logger.warning(f"Could not save audit log for evaluation crew '{self.tender_id}': {audit_err}")

        return result

    def _assemble_crew(self, document_list: List[str]) -> Any:
        """Assembles active agents and assigned tasks into a CrewAI sequential pipeline (SRP: Agent/Task Assembly)."""
        from crewai import Crew, Process
        from crew.agents import TenderAgents
        from crew.tasks import TenderTasks

        agent_factory = TenderAgents(llm_api_key=self.api_key)
        agent_sel = agent_factory.tender_selection_agent()
        agent_tech = agent_factory.technical_compliance_agent()
        agent_comm = agent_factory.commercial_analysis_agent()
        agent_risk = agent_factory.risk_and_evidence_agent()
        agent_writer = agent_factory.evaluation_writer_agent()

        task_sel = TenderTasks.select_tender_baseline_task(agent_sel, self.tender_id, document_list)
        task_tech = TenderTasks.technical_compliance_task(agent_tech, self.tender_id)
        task_comm = TenderTasks.commercial_analysis_task(agent_comm, self.tender_id)
        task_risk = TenderTasks.risk_assessment_task(agent_risk, self.tender_id)
        task_write = TenderTasks.generate_evaluation_report_task(agent_writer, self.tender_id)

        return Crew(
            agents=[agent_sel, agent_tech, agent_comm, agent_risk, agent_writer],
            tasks=[task_sel, task_tech, task_comm, task_risk, task_write],
            process=Process.sequential,
            verbose=True
        )

    def _execute_crew(self, crew: Any) -> Any:
        """Executes the assembled CrewAI agent pipeline (SRP: Execution)."""
        result = crew.kickoff()
        logger.info(f"CrewAI workflow completed for tender '{self.tender_id}'")
        return result

    def _merge_crew_result(self, crew_result: Any, vendor_dossiers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesizes CrewAI output string into standard matrix comparison result format (SRP: Result Merging)."""
        result_data = self.comparison_service.generate_comparison_matrix(self.tender_id, vendor_dossiers)
        result_data["crewai_output"] = str(crew_result)
        return result_data

    def _run_crewai_crew(self, document_list: List[str], vendor_dossiers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Orchestrates Crew assembly, execution, and output merging."""
        crew = self._assemble_crew(document_list)
        result = self._execute_crew(crew)
        return self._merge_crew_result(result, vendor_dossiers)

    def _run_deterministic_fallback(self, document_list: List[str], vendor_dossiers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs rule-based structured analysis engine directly using the reused ComparisonService instance."""
        try:
            result = self.comparison_service.generate_comparison_matrix(self.tender_id, vendor_dossiers)
            result["execution_mode"] = "Deterministic Rule Engine (No API key required)"
            logger.info(f"Deterministic evaluation successfully completed for '{self.tender_id}'")
            return result
        except Exception as e:
            logger.exception(f"Error in deterministic evaluation pipeline: {e}")
            raise

