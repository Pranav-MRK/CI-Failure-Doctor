import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.core.config import get_settings
from main import app

client = TestClient(app)

secret = get_settings().github_webhook_secret


def make_signature(body: bytes) -> str:
    digest = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def test_failed_workflow_is_accepted():
    payload = {
        "action": "completed",
        "workflow_run": {
            "id": 12345,
            "name": "CI",
            "head_branch": "feature/test",
            "head_sha": "abc123",
            "conclusion": "failure",
        },
        "repository": {
            "full_name": "pranav/ci-doctor-test",
        },
    }

    body = json.dumps(payload).encode()

    response = client.post(
        "/webhooks/github",
        content=body,
        headers={
            "X-Hub-Signature-256": make_signature(body),
            "X-GitHub-Event": "workflow_run",
            "X-GitHub-Delivery": "delivery-123",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert response.json()["repository"] == "pranav/ci-doctor-test"


def test_invalid_signature_is_rejected():
    response = client.post(
        "/webhooks/github",
        content=b"{}",
        headers={
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Event": "workflow_run",
            "X-GitHub-Delivery": "delivery-123",
        },
    )

    assert response.status_code == 401