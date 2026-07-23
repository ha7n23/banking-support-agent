from collections.abc import Callable

from banking_agent.generation.llm_client import GeminiTextGenerator
from banking_agent.services.agent_service import BankingSupportAgent

from banking_agent.services.workflow_service import (
    InMemoryWorkflowService,
    WorkflowServiceProtocol,
)


AgentFactory = Callable[[bool], BankingSupportAgent]

workflow_service: WorkflowServiceProtocol = InMemoryWorkflowService()


def get_agent_factory() -> AgentFactory:
    """Return a factory that creates an agent with or without LLM support."""

    def factory(use_llm: bool) -> BankingSupportAgent:
        text_generator = GeminiTextGenerator() if use_llm else None
        return BankingSupportAgent(text_generator=text_generator)

    return factory

def get_workflow_service() -> WorkflowServiceProtocol:
    """Return the shared in-memory workflow service."""
    return workflow_service