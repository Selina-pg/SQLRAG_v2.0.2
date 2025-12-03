import uuid
import os
from datetime import datetime
from vanna import ToolContext
from vanna.core.user import User

from tool.semantic import SemanticAnalysisTool, SemanticAnalysisInput, SemanticResult, build_semantic_reply
from tool.intent import IntentClassifierTool, IntentInput, IntentResult

class Workflow:
    """
    Workflow 負責全局決策：
    1. 呼叫 semantic tool
    2. 如果有 main_query → 呼叫 intent tool
    3. 如果沒有 main_query → 使用 build_semantic_reply
    4. 把工具呼叫與回覆存進 agent_memory (只存文字)
    """
    def __init__(self, agent):
        self.agent = agent
        self.semantic_tool = SemanticAnalysisTool()
        self.intent_tool = IntentClassifierTool()
        # 註冊工具到 Agent
        self.agent.tool_registry.register_local_tool(self.semantic_tool, access_groups=["admin"])
        self.agent.tool_registry.register_local_tool(self.intent_tool, access_groups=["admin"])
        # 準備本地記憶日誌檔案路徑
        self._memory_log_path = os.path.join("data", "memory", "demo_conversation.log")
        os.makedirs(os.path.dirname(self._memory_log_path), exist_ok=True)

    async def run(self, user_input: str, user: User) -> str:
        """
        執行工作流程並回傳字串結果。

        為了方便觀察工具呼叫，這裡會在回覆中插入輕量級 trace 標記：
        - <tool_call name="SemanticAnalysisTool"> ... </tool_call>
        - <tool_call name="IntentClassifierTool"> ... </tool_call>
        """

        trace_chunks = []

        # 建立 ToolContext，讓記憶系統知道這次對話
        context = ToolContext(
            user=user,
            conversation_id="demo_conversation",
            request_id=str(uuid.uuid4()),
            agent_memory=self.agent.agent_memory,
        )
        conversation_id = context.conversation_id
        request_id = context.request_id

        # Step 1: 呼叫 semantic tool
        args = SemanticAnalysisInput(text=user_input)
        tool_result = await self.semantic_tool.execute(None, args)

        # 在回覆中嵌入工具呼叫 trace
        trace_chunks.append(
            f"<tool_call name=\"SemanticAnalysisTool\">success={tool_result.success}; msg={tool_result.result_for_llm}</tool_call>"
        )

        # 存文字記憶（工具呼叫結果）
        # await self.agent.agent_memory.save_text_memory(
        #     context=context,
        #     content=trace_chunks[-1],
        # )
        # self._log_memory(conversation_id, request_id, user, trace_chunks[-1])

        if not tool_result.success:
            # await self.agent.agent_memory.save_text_memory(
            #     context=context,
            #     content=tool_result.result_for_llm,
            # )
            # self._log_memory(conversation_id, request_id, user, tool_result.result_for_llm)
            tail = self._tail_log(10)
            return "\n".join(trace_chunks + [tool_result.result_for_llm, "\n[最近記憶紀錄]\n" + tail])

        # 轉成 SemanticResult
        semantic_result = SemanticResult(**tool_result.metadata["semantic_result"])

        # Step 2: 如果有 main_query → 呼叫 intent tool
        if semantic_result.main_query:
            intent_args = IntentInput(query=semantic_result.main_query)
            intent_result = await self.intent_tool.execute(None, intent_args)

            trace_chunks.append(
                f"<tool_call name=\"IntentClassifierTool\">success={intent_result.success}; msg={intent_result.result_for_llm}</tool_call>"
            )

            # 存文字記憶（工具呼叫結果）
            # await self.agent.agent_memory.save_text_memory(
            #     context=context,
            #     content=trace_chunks[-1],
            # )
            # self._log_memory(conversation_id, request_id, user, trace_chunks[-1])

            if not intent_result.success:
                # await self.agent.agent_memory.save_text_memory(
                #     context=context,
                #     content=intent_result.result_for_llm,
                # )
                # self._log_memory(conversation_id, request_id, user, intent_result.result_for_llm)
                tail = self._tail_log(10)
                return "\n".join(trace_chunks + [intent_result.result_for_llm, "\n[最近記憶紀錄]\n" + tail])            
            
            # 轉成 IntentResult
            ir = IntentResult(**intent_result.metadata)
            final_msg = f"意圖判斷結果：{ir.abcd} ({ir.label}) → 建議：{ir.suggestion or '無'}"

            # 存文字記憶（最終回覆）
            # await self.agent.agent_memory.save_text_memory(
            #     context=context,
            #     content=final_msg,
            # )
            # self._log_memory(conversation_id, request_id, user, final_msg)
            tail = self._tail_log(10)
            return "\n".join(trace_chunks + [final_msg, "\n[最近記憶紀錄]\n" + tail])

        # Step 3: 如果沒有 main_query → 使用 build_semantic_reply
        final_msg = build_semantic_reply(semantic_result)

        # await self.agent.agent_memory.save_text_memory(
        #     context=context,
        #     content=final_msg,
        # )
        # self._log_memory(conversation_id, request_id, user, final_msg)
        tail = self._tail_log(10)
        return "\n".join(trace_chunks + [final_msg, "\n[最近記憶紀錄]\n" + tail])

    # 將保存的文字記憶額外寫入本地檔案，便於驗證
    # def _log_memory(self, conversation_id: str, request_id: str, user: User, content: str) -> None:
    #     try:
    #         ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         user_id = getattr(user, "id", "unknown")
    #         line = f"[{ts}] conversation={conversation_id} | request={request_id} | user={user_id} | {content}\n"
    #         with open(self._memory_log_path, "a", encoding="utf-8") as f:
    #             f.write(line)
    #     except Exception:
    #         pass

    # 讀取本地記憶日誌最後 n 行
    def _tail_log(self, n: int = 10) -> str:
        try:
            if not os.path.exists(self._memory_log_path):
                return "(log 檔案不存在)"
            with open(self._memory_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                return "(log 目前為空)"
            return "".join(lines[-n:])
        except Exception as e:
            return f"(讀取 log 失敗: {e})"
