from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, JSON
from datetime import datetime


# -------------------------------------------------------------------
# Database Models
# -------------------------------------------------------------------

class DebateBase(SQLModel):
    video_id: str = Field(index=True, unique=True)
    youtube_url: str
    total_duration_seconds: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Debate(DebateBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Store structured JSON blobs for speakers and transcript ledger
    speakers_data: List[dict] = Field(default=[], sa_type=JSON)
    ledger_data: List[dict] = Field(default=[], sa_type=JSON)


class DebateRead(DebateBase):
    id: int
    speakers_data: List[dict]
    ledger_data: List[dict]