from typing import Type

from vanna import Tool, ToolContext, ToolResult
from vanna.components import UiComponent, SimpleTextComponent, NotificationComponent, ComponentType
from .model import IntentInput, IntentResult
from .prompts import SYSTEM_PROMPT_INTENT_CLASSIFICATION
from .utils import get_label, get_suggestion
from services.openai_client import OpenAIClient


class IntentClassifierTool(Tool[IntentInput]):

    @property
    def name(self) -> str:
        return "intent_classifier"

    @property
    def description(self) -> str:
        return (
            "此工具應在 semantic_analysis 有 main_query 時呼叫，"
            "用來判斷查詢是否與資料庫相關 (A/B/C/D)。"
        )

    def get_args_schema(self) -> Type[IntentInput]:
        return IntentInput

    def __init__(self):
        self.llm = OpenAIClient()

    async def execute(self, context: ToolContext, args: IntentInput) -> ToolResult:
        try:
            mq = (args.query or "").strip()
            if not mq or len(mq) < 2:
                return self._wrap_result(mq, "C", "")

            raw_output = await self.llm.chat(
                system_prompt=SYSTEM_PROMPT_INTENT_CLASSIFICATION.format(question=mq),
                user_prompt=""
            )
            abcd = self._extract_label(raw_output)

            return self._wrap_result(mq, abcd, raw_output)

        except Exception as e:
            error_message = f"Error executing intent classification: {str(e)}"
            return ToolResult(
                success=False,
                result_for_llm=error_message,
                ui_component=UiComponent(
                    rich_component=NotificationComponent(
                        type=ComponentType.NOTIFICATION,
                        level="error",
                        message=error_message,
                    ),
                    simple_component=SimpleTextComponent(text=error_message),
                ),
                error=str(e),
                metadata={"error_type": "intent_tool_error"},
            )

    def _extract_label(self, raw: str) -> str:
        raw = raw.strip().upper()
        return raw[0] if raw and raw[0] in ["A", "B", "C", "D"] else "D"

    def _wrap_result(self, mq: str, abcd: str, raw: str) -> ToolResult:
        result = IntentResult(
            main_query=mq,
            abcd=abcd,
            raw_response=raw,
            label=get_label(abcd),
            suggestion=get_suggestion(abcd),
        )

        result_for_llm = f"意圖判斷完成：{result.abcd} ({result.label})；建議：{result.suggestion or '無'}"

        return ToolResult(
            success=True,
            result_for_llm=f"<tool_call>{self.name}</tool_call>\n{result_for_llm}",
            ui_component=UiComponent(
                rich_component=NotificationComponent(
                    type=ComponentType.NOTIFICATION,
                    level="info",
                    message=f"[{self.name}] {result_for_llm}",
                ),
                simple_component=SimpleTextComponent(text=f"[{self.name}] {result_for_llm}"),
            ),
            metadata=result.model_dump(),
        )
