from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ProcessedRequest(Base):
    __tablename__ = "processed_requests"

    correlation_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    report_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))