import asyncio
from vanna import Agent
from vanna.core import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext
from vanna.integrations.local.agent_memory.in_memory import DemoAgentMemory

from config.llm import LLM_MODEL_NAME, LLM_BASE_URL, LLM_API_KEY
from vanna.integrations.openai.llm import OpenAILlmService
from workflow.workflow import Workflow

# 簡單的使用者解析器：固定回傳 demo 使用者
class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="demo", email="demo@example.com", group_memberships=["admin"])
    
async def main():
    # 建立必要的元件
    llm_service = OpenAILlmService(
        model=LLM_MODEL_NAME,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
    )
    tool_registry = ToolRegistry()
    user_resolver = SimpleUserResolver()
    agent_memory = DemoAgentMemory(max_items=100)

    # 建立 Agent
    agent = Agent(
        llm_service=llm_service,
        tool_registry=tool_registry,
        user_resolver=user_resolver,
        agent_memory=agent_memory,
    )

    # 建立 Workflow 並註冊工具
    workflow = Workflow(agent)

    # 測試輸入
    user_input = "你好，我想查詢 LTHDES101N 設備資訊"
    # 建立使用者（與 SimpleUserResolver 一致）
    user = await user_resolver.resolve_user(RequestContext())    
    reply = await workflow.run(user_input, user)

    # 檢查是否有工具呼叫標記
    if "<tool_call>" in reply:
        print("[ToolCall]", reply)
    else:
        print("最終回覆:\n", reply)

if __name__ == "__main__":
    asyncio.run(main())
