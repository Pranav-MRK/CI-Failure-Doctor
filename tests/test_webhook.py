import hashlib
import hmac
import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.models import WorkflowRunRecord
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
    delivery_id = f"test-accept-{uuid4().hex}"
    workflow_id = uuid4().int % 2_000_000_000

    payload = {
        "action": "completed",
        "workflow_run": {
            "id": workflow_id,
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

    try:
        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": make_signature(body),
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": delivery_id,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
        assert response.json()["repository"] == "pranav/ci-doctor-test"
    finally:
        with SessionLocal() as db:
            record = db.scalar(
                select(WorkflowRunRecord).where(
                    WorkflowRunRecord.delivery_id == delivery_id
                )
            )
            if record is not None:
                db.delete(record)
                db.commit()


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


def test_failed_workflow_is_saved_to_database():
    delivery_id = f"test-persistence-{uuid4().hex}"
    workflow_id = uuid4().int % 2_000_000_000

    payload = {
        "action": "completed",
        "workflow_run": {
            "id": workflow_id,
            "name": "CI persistence test",
            "head_branch": "test/persistence",
            "head_sha": "def456",
            "conclusion": "failure",
        },
        "repository": {
            "full_name": "pranav/ci-doctor-persistence-test",
        },
    }

    body = json.dumps(payload).encode()

    try:
        response = client.post(
            "/webhooks/github",
            content=body,
            headers={
                "X-Hub-Signature-256": make_signature(body),
                "X-GitHub-Event": "workflow_run",
                "X-GitHub-Delivery": delivery_id,
                "Content-Type": "application/json",
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

        with SessionLocal() as db:
            record = db.scalar(
                select(WorkflowRunRecord).where(
                    WorkflowRunRecord.delivery_id == delivery_id
                )
            )

            assert record is not None
            assert record.github_workflow_id == workflow_id
            assert record.repository == "pranav/ci-doctor-persistence-test"
    finally:
        with SessionLocal() as db:
            record = db.scalar(
                select(WorkflowRunRecord).where(
                    WorkflowRunRecord.delivery_id == delivery_id
                )
            )
            if record is not None:
                db.delete(record)
                db.commit()