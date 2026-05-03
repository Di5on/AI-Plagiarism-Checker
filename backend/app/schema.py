from pydantic import BaseModel
from typing import List


class SourceResponse(BaseModel):
    sources: List[str]