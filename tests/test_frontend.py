from fastapi.testclient import TestClient

from banking_agent.api.app import app


client = TestClient(app)


def test_workflow_ui_loads() -> None:
    response = client.get("/ui")

    assert response.status_code == 200
    assert "Banking Support Workflow Agent" in response.text
    assert "Support request" in response.text
    assert "/static/app.js" in response.text
    assert "/static/styles.css" in response.text