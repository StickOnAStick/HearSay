from pydantic import BaseModel


class Keyword(BaseModel):
    keyword: str
    frequency: int
    sentiment: float # +-1


class CaludeOutput(BaseModel):
    keywords: list[Keyword]
    summary: str # Summary of the 

class InputReview(BaseModel):
    