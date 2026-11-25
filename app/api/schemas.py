from typing import Literal

from pydantic import BaseModel, ConfigDict


class Repository(BaseModel):
    full_name: str


class WorkflowRun(BaseModel):
    id: int
    name: str | None = None
    head_branch: str
    head_sha: str
    conclusion: str | None = None
    html_url: str | None = None


class WorkflowRunPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: Literal["completed"]
    workflow_run: WorkflowRun
    repository: Repository