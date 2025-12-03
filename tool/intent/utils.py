from .prompts import INTENT_LABELS, INTENT_SUGGESTIONS

def get_label(abcd: str) -> str:
    return INTENT_LABELS.get(abcd, "未知")

def get_suggestion(abcd: str) -> str:
    return INTENT_SUGGESTIONS.get(abcd, "")