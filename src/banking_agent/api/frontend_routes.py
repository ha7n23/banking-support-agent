from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "web" / "templates"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/ui", response_class=HTMLResponse)
def workflow_ui(request: Request) -> HTMLResponse:
    """Serve the lightweight workflow automation UI."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {"request": request},
    )