from pydantic import BaseModel

class TokenLimitResponse(BaseModel):
    model: str
    token_limit: int