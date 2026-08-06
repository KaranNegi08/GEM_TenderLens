"""
CrewAI Task Definitions for GeM TenderLens.
Defines sequential tasks for tender package setup, vendor intake, technical/commercial review, and report writing.
"""

from typing import List, Dict, Any
from crewai import Task
from utils_logger import get_logger

logger = get_logger(__name__)


class TenderTasks:
    """Task factory for CrewAI workflow tasks."""

    @staticmethod
    def _create_task(description: str, expected_output: str, agent: Any):
        return Task(description=description, expected_output=expected_output, agent=agent)

    @staticmethod
    def select_tender_baseline_task(agent: Any, tender_id: str, document_list: List[str]):
        return TenderTasks._create_task(
            description=f"Review uploaded tender package for tender reference '{tender_id}'. Files: {', '.join(document_list)}.",
            expected_output="Confirmed tender baseline summary with active governing document.",
            agent=agent
        )

    @staticmethod
    def ingest_vendor_proposals_task(agent: Any, vendor_dossiers: List[Dict[str, Any]]):
        return TenderTasks._create_task(
            description=f"Ingest vendor proposal submissions for {len(vendor_dossiers)} vendors.",
            expected_output="Validated vendor dossiers with text availability reports.",
            agent=agent
        )

    @staticmethod
    def technical_compliance_task(agent: Any, tender_id: str):
        return TenderTasks._create_task(
            description=f"Compare vendor technical specs against mandatory requirements for tender '{tender_id}'.",
            expected_output="Structured Technical Compliance Matrix with citations.",
            agent=agent
        )

    @staticmethod
    def commercial_analysis_task(agent: Any, tender_id: str):
        return TenderTasks._create_task(
            description=f"Normalize quoted prices, tax calculations, delivery days, and warranty for tender '{tender_id}'.",
            expected_output="Commercial Comparison Table with total normalized prices and L-1 ranking.",
            agent=agent
        )

    @staticmethod
    def risk_assessment_task(agent: Any, tender_id: str):
        return TenderTasks._create_task(
            description=f"Review findings for tender '{tender_id}' to flag missing proof and draft clarification items.",
            expected_output="Risk and Clarification Queue.",
            agent=agent
        )

    @staticmethod
    def generate_evaluation_report_task(agent: Any, tender_id: str):
        return TenderTasks._create_task(
            description=f"Synthesize findings for tender '{tender_id}' into evaluation report.",
            expected_output="Committee-ready Tender Evaluation Report.",
            agent=agent
        )
