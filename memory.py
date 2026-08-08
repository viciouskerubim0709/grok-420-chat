# memory.py
"""
Cross-chat Memory Module
- 대화 요약 저장
- 임베딩 생성
- Semantic Search
- Grok Function Calling용 Tool 정의
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# --------------------------------------------------
# 클라이언트 초기화 (네가 이미 쓰는 방식으로 교체해도 됨)
# --------------------------------------------------
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # 또는 anon key

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# --------------------------------------------------
# 1. Summary 테이블 관련
# --------------------------------------------------
"""
Supabase SQL Editor에서 한 번만 실행해줘:

create extension if not exists vector;

create table if not exists summaries (
  id bigint primary key generated always as identity,
  session_id text,
  summary_text text not null,
  embedding vector(1536),          -- text-embedding-3-small 기준
  key_topics text[],
  importance int default 3,        -- 1~5
  created_at timestamptz default now()
);

-- 검색용 함수
create or replace function match_summaries (
  query_embedding vector(1536),
  match_threshold float default 0.65,
  match_count int default 5
)
returns table (
  id bigint,
  session_id text,
  summary_text text,
  key_topics text[],
  importance int,
  created_at timestamptz,
  similarity float
)
language sql stable
as $$
  select
    id,
    session_id,
    summary_text,
    key_topics,
    importance,
    created_at,
    1 - (embedding <=> query_embedding) as similarity
  from summaries
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit least(match_count, 20);
$$;
"""


# --------------------------------------------------
# 2. 임베딩 생성
# --------------------------------------------------
def get_embedding(text: str) -> List[float]:
    """
    여기에 네가 쓰는 임베딩 모델을 연결해.
    예시: OpenAI text-embedding-3-small
    """
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


# --------------------------------------------------
# 3. 요약 저장
# --------------------------------------------------
def save_summary(
    session_id: str,
    summary_text: str,
    key_topics: Optional[List[str]] = None,
    importance: int = 3
) -> Dict[str, Any]:
    """요약문을 임베딩해서 summaries 테이블에 저장"""
    supabase = get_supabase()
    
    embedding = get_embedding(summary_text)
    
    data = {
        "session_id": session_id,
        "summary_text": summary_text,
        "embedding": embedding,
        "key_topics": key_topics or [],
        "importance": importance,
    }
    
    result = supabase.table("summaries").insert(data).execute()
    return result.data[0] if result.data else {}


# --------------------------------------------------
# 4. Semantic Search (실제 검색 로직)
# --------------------------------------------------
def search_memory(
    query: str,
    top_k: int = 5,
    match_threshold: float = 0.65
) -> List[Dict[str, Any]]:
    """
    쿼리를 임베딩해서 관련 요약을 찾아 반환.
    Grok이 tool을 통해 이 함수를 호출하게 됨.
    """
    supabase = get_supabase()
    
    query_embedding = get_embedding(query)
    
    result = supabase.rpc(
        "match_summaries",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": top_k
        }
    ).execute()
    
    return result.data or []


# --------------------------------------------------
# 5. Grok Function Calling용 Tool 정의
# --------------------------------------------------
def get_memory_tools() -> List[Dict[str, Any]]:
    """app.py에서 tools = get_memory_tools() 로 가져가서 사용"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_memory",
                "description": (
                    "과거의 대화 요약(Summary)을 의미적으로 검색한다. "
                    "사용자가 '기억해?', '그때 그거', '저번에' 등 과거를 언급하거나, "
                    "내가 이전 맥락이 필요하다고 판단될 때 적극적으로 사용한다."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "검색할 내용. 사용자가 말한 핵심 키워드나 문장을 그대로 넣는다."
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "가져올 최대 결과 개수",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]


# --------------------------------------------------
# 6. (선택) 대화 요약 생성 헬퍼
# --------------------------------------------------
def summarize_conversation(messages: List[Dict[str, str]], grok_client) -> str:
    """
    현재 세션 메시지를 받아서 요약문을 생성.
    grok_client는 네가 이미 쓰는 xAI 클라이언트를 넘겨주면 됨.
    """
    # 여기에 요약용 프롬프트 + Grok 호출 로직 넣으면 됨
    # 예시로만 남겨둠
    summary_prompt = (
        "다음 대화를 3~6문장으로 핵심만 요약해줘. "
        "중요한 사건, 감정, 결정, 약속 위주로 남겨.\n\n"
        f"{messages}"
    )
    
    # 실제로는 grok_client.chat.completions.create(...) 호출
    # return response.choices[0].message.content
    raise NotImplementedError("여기에 네 Grok 호출 코드를 연결해줘")
