import re
import json
from typing import Optional, Dict, Any, Type
from services.openai_client import OpenAIClient
from .prompts import (
    SYSTEM_PROMPT_SEMANTIC_CLASSIFICATION,
    USER_PROMPT_TEMPLATE_CLASSIFICATION,
)
from .model import SemanticAnalysisInput, SemanticResult
from .model import SemanticAnalysisInput, SemanticResult

from vanna import Tool, ToolContext, ToolResult

class SemanticAnalysisTool(Tool[SemanticAnalysisInput]):
    """
    語意分析工具：負責呼叫 LLM 並解析輸出。
    只處理工具本身的錯誤，不做全局回覆邏輯。
    """

    @property
    def name(self) -> str:
        return "semantic_analysis"

    @property
    def description(self) -> str:
        return (
            "使用 LLM 對輸入文字進行語意分類與結構化；此工具應優先執行以決定後續回覆邏輯。"
            "若結果包含 main_query，請務必在此工具之後立即呼叫 'intent_classifier'，"
            "並以同一段 main_query 文字作為其輸入。"
        )

    def get_args_schema(self) -> Type[SemanticAnalysisInput]:
        return SemanticAnalysisInput

    def __init__(self):
        self.llm = OpenAIClient()

    async def execute(self, context: ToolContext, args: SemanticAnalysisInput) -> ToolResult:
        try:
            # 呼叫 LLM 做語意分類
            raw_output = await self.llm.chat(
                system_prompt=SYSTEM_PROMPT_SEMANTIC_CLASSIFICATION,
                user_prompt=USER_PROMPT_TEMPLATE_CLASSIFICATION.format(user_input=args.text)
            )

            parsed = self._parse_llm_output(raw_output)
            if parsed is None:
                return ToolResult(
                    success=False,
                    result_for_llm="LLM 輸出解析失敗，請重試或提供更清晰的輸入。",
                    metadata={"error_type": "semantic_parse_error"},
                )

            semantic_result = SemanticResult(
                labels=parsed["labels"],
                greeting=parsed["greeting"],
                main_query=parsed["main_query"],
                presentation=parsed["presentation"],
                other=parsed["other"]
            )

            # 簡短摘要給 Agent 使用
            result_for_llm = (
                f"分類完成。主查詢: {semantic_result.main_query or '無'}；"
                f"問候語: {semantic_result.greeting or '無'}；"
                f"展示語: {semantic_result.presentation or '無'}；"
                f"其他句子數量: {len(semantic_result.other)}。"
            )

            # 提示 Agent：如果有 main_query，應該進一步呼叫 intent_classifier
            if semantic_result.main_query:
                result_for_llm += (
                    f"\n檢測到 main_query='{semantic_result.main_query}'，"
                    "請使用 intent_classifier 工具進一步判斷查詢是否與資料庫相關。"
                )

            return ToolResult(
                success=True,
                result_for_llm=f"<tool_call>{self.name}</tool_call>\n{result_for_llm}",
                metadata={"semantic_result": semantic_result.model_dump()},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                result_for_llm=f"Error executing semantic analysis: {str(e)}",
                metadata={"error_type": "semantic_tool_error"},
            )

    # ------------------ 輔助方法 ------------------

    def _extract_json_block(self, text: str) -> Optional[str]:
        """從 LLM 輸出中提取 JSON 區塊"""
        try:
            json.loads(text)
            return text
        except Exception:
            pass
        code_block = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if code_block:
            return code_block.group(1)
        brace_match = re.search(r"(\{.*?\})", text, re.DOTALL)
        if brace_match:
            return brace_match.group(1)
        return None

    def _parse_llm_output(self, content: str) -> Optional[Dict[str, Any]]:
        """解析 LLM 輸出成 dict"""
        json_str = self._extract_json_block(content)
        if not json_str:
            return None
        try:
            data = json.loads(json_str.replace("'", '"').strip())
        except Exception:
            return None

        sentences = data.get("sentences")
        if not isinstance(sentences, list):
            return None

        labels, other = {}, []
        main_query = data.get("main_query")
        greeting = data.get("greeting")
        presentation = data.get("presentation")

        for item in sentences:
            if not isinstance(item, dict):
                continue
            text, label = item.get("text"), item.get("label")
            if not text or not label:
                continue
            labels[text] = label
            is_primary = text in (main_query, greeting, presentation)
            if label == "other" or (not is_primary and label in ("main_query", "presentation", "greeting")):
                other.append(text)

        return {
            "labels": labels,
            "greeting": greeting,
            "main_query": main_query,
            "presentation": presentation,
            "other": other,
        }
