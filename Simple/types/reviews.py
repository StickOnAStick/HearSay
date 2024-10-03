from pydantic import BaseModel
from pendulum import DateTime
import pendulum

class Review(BaseModel):
    review_id: str
    business_id: str
    rating: float
    summary: str
    text: str
    date: int | DateTime

    @classmethod
    def convert_timestamp(self):
        self.date = pendulum.from_timestamp(self.date)