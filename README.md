```bash
SQLRAG_v2.0.2/
├── tool/                    # 工具
│   ├── __init__.py
│   └── semantic/            # 語意分類
│   │   ├── __init__.py
│   │   ├── model.py
│   │   ├── prompts.py
│   │   └── tool.py
│   └── intent/              # 意圖判斷
│       ├── __init__.py
│       ├── model.py
│       ├── prompts.py
│       └── tool.py
│ 
├── services/                # 共用服務
│   ├── __init__.py
│   └── openai_client.py
│ 
├── config/                  # 環境設定與連線資訊
│   ├── __init__.py
│   └── llm.py
│
├── workflow/                # 工作流程
│   └── workflow.py
│
├── main.py                  # 註冊 Agent + Tool
│
└── pyproject.toml
```