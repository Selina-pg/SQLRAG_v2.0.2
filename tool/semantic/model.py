from pydantic import BaseModel
from typing import Optional, Dict, List

class SemanticAnalysisInput(BaseModel):
    """
    語意分析工具的輸入格式。
    接收使用者輸入的原始文字。
    """
    text: str


class SemanticResult(BaseModel):
    labels: Dict[str, str]
    main_query: Optional[str] = None
    greeting: Optional[str] = None
    presentation: Optional[str] = None
    other: List[str] = []