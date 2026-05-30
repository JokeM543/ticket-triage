from typing import Literal

from pydantic import BaseModel, Field


class TicketTriageSchema(BaseModel):
    category: str
    urgency: Literal["Low", "Medium", "High", "Critical"]
    sentiment: Literal["Negative", "Neutral", "Positive"]
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
