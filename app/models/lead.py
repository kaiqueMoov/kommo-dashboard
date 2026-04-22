from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean
from app.models.base import Base





class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_finalized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


    kommo_pipeline_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    kommo_status_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    responsible_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
    )

    car_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    campaign_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lead_source: Mapped[str | None] = mapped_column(String(100), nullable=True)

    utm_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_content: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_term: Mapped[str | None] = mapped_column(String(255), nullable=True)

    replied_first_message: Mapped[bool] = mapped_column(Boolean, default=False)
    replied_first_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sql_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    won_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lost_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at_kommo: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at_kommo: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

  