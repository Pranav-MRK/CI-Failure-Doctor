import hashlib
import hmac

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.api.schemas import WorkflowRunPayload
from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.models import WorkflowRunRecord

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
):
    settings = get_settings()

    if not settings.github_webhook_secret:
        raise HTTPException(
            status_code=500,
            detail="GitHub webhook secret is not configured",
        )

    if not x_hub_signature_256:
        raise HTTPException(
            status_code=401,
            detail="Missing GitHub signature",
        )

    body = await request.body()

    expected_signature = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        expected_signature,
        x_hub_signature_256,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub signature",
        )

    if x_github_event != "workflow_run":
        return {
            "status": "ignored",
            "reason": "Unsupported event",
        }

    if not x_github_delivery:
        raise HTTPException(
            status_code=400,
            detail="Missing GitHub delivery ID",
        )

    try:
        payload = WorkflowRunPayload.model_validate_json(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload",
        ) from exc

    workflow = payload.workflow_run

    if workflow.conclusion != "failure":
        return {
            "status": "ignored",
            "reason": "Workflow did not fail",
        }

    with SessionLocal() as db:
        existing = db.scalar(
            select(WorkflowRunRecord).where(
                WorkflowRunRecord.delivery_id == x_github_delivery
            )
        )

        if existing:
            return {
                "status": "already_processed",
                "delivery_id": x_github_delivery,
                "workflow_id": existing.github_workflow_id,
            }

        record = WorkflowRunRecord(
            github_workflow_id=workflow.id,
            delivery_id=x_github_delivery,
            repository=payload.repository.full_name,
            workflow_name=workflow.name,
            branch=workflow.head_branch,
            commit_sha=workflow.head_sha,
            conclusion=workflow.conclusion,
            html_url=workflow.html_url,
        )

        db.add(record)
        db.commit()

    return {
        "status": "accepted",
        "delivery_id": x_github_delivery,
        "repository": payload.repository.full_name,
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "branch": workflow.head_branch,
        "commit": workflow.head_sha,
        "conclusion": workflow.conclusion,
    }