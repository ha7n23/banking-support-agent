from fastapi import FastAPI

from banking_agent.api.routes import router
from banking_agent.core.config import APP_NAME


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=APP_NAME,
        description=(
            "A controlled tool-using banking support agent with "
            "confirmation-gated actions."
        ),
        version="0.1.0",
    )

    app.include_router(router)

    return app


app = create_app()