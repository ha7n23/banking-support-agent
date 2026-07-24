from collections.abc import Callable, Generator

from banking_agent.core.config import WORKFLOW_STORAGE_BACKEND
from banking_agent.database.connection import get_session_factory
from banking_agent.generation.llm_client import GeminiTextGenerator
from banking_agent.services.agent_service import BankingSupportAgent
from banking_agent.services.database_workflow_service import DatabaseWorkflowService
from banking_agent.services.workflow_service import (
    InMemoryWorkflowService,
    WorkflowServiceProtocol,
)


AgentFactory = Callable[[bool], BankingSupportAgent]

memory_workflow_service: WorkflowServiceProtocol = InMemoryWorkflowService()


def get_agent_factory() -> AgentFactory:
    """Return a factory that creates an agent with or without LLM support."""

    def factory(use_llm: bool) -> BankingSupportAgent:
        text_generator = GeminiTextGenerator() if use_llm else None
        return BankingSupportAgent(text_generator=text_generator)

    return factory


def get_workflow_service() -> Generator[WorkflowServiceProtocol, None, None]:
    """Yield the configured workflow service."""
    if WORKFLOW_STORAGE_BACKEND == "memory":
        yield memory_workflow_service
        return

    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield DatabaseWorkflowService(session)
    finally:
        session.close()