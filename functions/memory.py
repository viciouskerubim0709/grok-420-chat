tools = [
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "과거의 대화 요약(Summary)을 의미적으로 검색한다. 사용자가 과거 일을 물어보거나, 내가 기억이 필요하다고 판단될 때 사용한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "검색할 내용 (사용자가 말한 핵심 키워드나 문장)"
                    },
                    "top_k": {
                        "type": "integer",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    }
]
