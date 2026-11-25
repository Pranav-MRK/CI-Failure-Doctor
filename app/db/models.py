from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class WorkflowRunRecord(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    # GitHub's workflow run ID
    github_workflow_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    # GitHub sends this with each webhook delivery
    delivery_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    repository: Mapped[str] = mapped_column(String(255))
    workflow_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    branch: Mapped[str] = mapped_column(String(255))
    commit_sha: Mapped[str] = mapped_column(String(40))
    conclusion: Mapped[str] = mapped_column(String(50))
    html_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )