from typing import Optional
from pydantic import BaseModel

class IntentInput(BaseModel):
    query: str

class IntentResult(BaseModel):
    main_query: Optional[str]
    abcd: str
    raw_response: str
    label: str
    suggestion: str
