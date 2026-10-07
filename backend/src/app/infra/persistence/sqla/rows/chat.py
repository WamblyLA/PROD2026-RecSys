from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column


class ChatRow:
    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_a_id: Mapped[UUID]
    user_b_id: Mapped[UUID]
    created_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]


class MessageRow:
    id: Mapped[UUID] = mapped_column(primary_key=True)
    chat_id: Mapped[UUID]
    sender_user_id: Mapped[UUID]
    text: Mapped[str]
    created_at: Mapped[datetime]
    deleted_at: Mapped[datetime | None]
