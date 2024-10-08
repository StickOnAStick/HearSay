from pydantic import BaseModel
from anthropic.types import ContentBlock

class Keyword(BaseModel):
    keyword: str
    frequency: int
    sentiment: float # +-1
    embedding: list[float] | None

class LLMOutput(BaseModel):
    keywords: list[Keyword]
    rating: float
    summary: str # Summary of the

class Cluster(BaseModel):
    keywords: list[Keyword]
    