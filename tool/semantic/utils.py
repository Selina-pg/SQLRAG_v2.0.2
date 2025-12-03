from .model import SemanticResult
from .prompts import DEFAULT_GREETING_RESPONSE, DEFAULT_PRESENTATION_RESPONSE

def build_semantic_reply(result: SemanticResult) -> str:
    """
    根據語意解析結果，生成系統的引導性回覆。
    """
    if result.main_query:
        return ""
    if result.presentation:
        return DEFAULT_PRESENTATION_RESPONSE
    if result.greeting or result.other:
        return DEFAULT_GREETING_RESPONSE
    return ""
