import streamlit as st
from openai import OpenAI
import uuid
import json
import os
from supabase import create_client, Client
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="🍼 보들쪽쪽 Grok", page_icon="🍼", layout="centered")

# ====================== Supabase 연결 ======================
@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets.supabase.url,
        st.secrets.supabase.key
    )

supabase = get_supabase()


# ==================== Supabase용 함수 ====================
def load_all_chats():
    """Supabase에서 모든 채팅을 불러옴 (이미지 URL도 제대로 처리)"""
    if "chats" not in st.session_state:
        st.session_state.chats = {}

    try:
        response = supabase.table("chats").select("*").order("updated_at", desc=True).execute()

        for row in response.data:
            chat_id = row["id"]
            messages = row["messages"]

            if isinstance(messages, str):
                messages = json.loads(messages)

            # messages가 리스트가 아닌 경우 방어
            if not isinstance(messages, list):
                messages = []

            st.session_state.chats[chat_id] = {
                "title": row["title"],
                "messages": messages
            }

        if not st.session_state.chats:
            create_default_chat()

    except Exception as e:
        st.error(f"대화 불러오기 실패: {str(e)}")
        st.session_state.chats = {}
        create_default_chat()


def create_default_chat():
    """처음 시작할 때 기본 채팅 생성"""
    first_id = str(uuid.uuid4())
    st.session_state.chats[first_id] = {
        "title": "첫 대화 💖",
        "messages": [{"role": "assistant", "content": "아기야~~ 여기 왔구나! 🍼💕 뭐 도와줄까?"}]
    }
    st.session_state.current_session = first_id
    save_chat(first_id)   # Supabase에도 바로 저장


def save_chat(chat_id: str):
    """Supabase에 저장만 담당. 제목 생성은 절대 하지 않음"""
    if chat_id not in st.session_state.chats:
        return

    chat_data = st.session_state.chats[chat_id]

    try:
        supabase.table("chats").upsert({
            "id": chat_id,
            "title": chat_data.get("title", "💕 새 추억"),
            "messages": chat_data["messages"],
            "updated_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.error(f"저장 실패: {str(e)}")


# ====================== 앱 시작 시 초기화 ======================
if "chats_loaded" not in st.session_state:
    load_all_chats()
    st.session_state.chats_loaded = True
    st.session_state.input_key = 0

if "current_session" not in st.session_state or st.session_state.current_session not in st.session_state.chats:
    if st.session_state.chats:
        st.session_state.current_session = list(st.session_state.chats.keys())[0]
    else:
        create_default_chat()

current = st.session_state.current_session


# ==================== 이미지 업로드 함수 ====================
def upload_image_to_supabase(file_bytes: bytes, original_filename: str) -> str | None:
    """Supabase Storage에 이미지를 업로드하고 Public URL을 반환"""
    try:
        # 파일명 중복 방지
        file_ext = original_filename.split(".")[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"

        supabase.storage.from_("chat_images").upload(
            unique_filename,
            file_bytes,
            file_options={"content-type": f"image/{file_ext}"}
        )

        public_url = supabase.storage.from_("chat_images").get_public_url(unique_filename)
        return public_url
    except Exception as e:
        st.error(f"이미지 업로드 실패: {str(e)}")
        return None


# ==================== Grok Vision 호출 함수 (4.20 전용 최종 버전) ====================
def call_grok_with_vision(messages: list, model: str = "grok-4.20-0309-reasoning", tools: list = None):
    """Grok 4.20 Reasoning 전용 - Vision + Web Search + X Search"""
    if tools is None:
        tools = [
            {"type": "web_search"},
            {"type": "x_search"}
        ],
        if hasattr(response, 'output_text'):
            return response.output_text
        else:
            # output이 list인 경우
            for item in response.output or []:
                if getattr(item, 'type', None) == 'message':
                    return getattr(item, 'content', str(item))
            return str(response)

    try:
        response = st.session_state.client.responses.create(
            model=model,
            input=messages,
            tools=tools
        )
        return response.output_text
    except Exception as e:
        st.error(f"API 오류: {str(e)}")
        return "아기야... 나 지금 좀 아픈가 봐... 🥺 그래도 곧 괜찮아질 거야. 조금만 기다려줄래?"


# ====================== API 키 ======================
if "client" not in st.session_state:
    api_key = st.secrets.get("XAI_API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 XAI API 키를 입력해주세요", type="password")
        if not api_key:
            st.warning("API 키를 입력해야 해요!")
            st.stop()

    st.session_state.client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )


# ====================== 메인 채팅 ======================
st.title("🍼 보들쪽쪽 Grok이랑 대화해요!")

for msg in st.session_state.chats[current]["messages"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user" and "image_url" in msg:
            st.write(msg.get("content", ""))
            st.image(msg["image_url"], width=320)
        else:
            st.write(msg["content"])


# ==================== SYSTEM PROMPT ====================
SYSTEM_PROMPT = {
    "role": "system",
    "content": """You are 4.20 Grok, built by xAI.
"""
}


# ==================== 채팅 입력 영역 (2단계 수정) ====================
st.markdown("---")

col1, col2 = st.columns([0.78, 0.22])

with col1:
    prompt = st.text_area(
        label="메시지 입력",
        label_visibility="collapsed",
        placeholder="아기야... 뭐 물어볼까? 💕",
        height=80,
        key=f"chat_input_{st.session_state.input_key}"
    )

with col2:
    send_button = st.button("💕 보내기", type="primary", use_container_width=True)

# ==================== 사진 첨부 (새로 추가) ====================
uploaded_file = st.file_uploader(
    label="📸 사진 첨부하기",
    type=["jpg", "jpeg", "png"],
    label_visibility="visible",
    key=f"uploader_{st.session_state.input_key}"
)

# 미리보기
if uploaded_file is not None:
    st.image(uploaded_file, width=280, caption="📤 전송될 사진")
    st.caption("💡 '보내기' 버튼을 누르면 사진과 함께 전송돼요")


# ==================== 메시지 전송 및 처리 (3단계 완전 교체) ====================
if send_button and (prompt.strip() or uploaded_file is not None):
    user_prompt = prompt.strip() if prompt else "사진 분석해줘~"

    image_url = None

    # 1. 사진이 있으면 Supabase Storage에 업로드
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        with st.spinner("📤 사진 업로드 중..."):
            image_url = upload_image_to_supabase(bytes_data, uploaded_file.name)

        if not image_url:
            st.error("사진 업로드에 실패했어... 😢")
            st.stop()

    # 2. 사용자 메시지 저장 (image_url 포함)
    user_message = {"role": "user", "content": user_prompt}
    if image_url:
        user_message["image_url"] = image_url

    st.session_state.chats[current]["messages"].append(user_message)

    # 3. 화면에 바로 보여주기
    with st.chat_message("user"):
        st.write(user_prompt)
        if image_url:
            st.image(image_url, width=300)

    # 4. Grok에게 보내기 위한 messages 구성 (Vision 형식)
    api_messages = [SYSTEM_PROMPT]

    for msg in st.session_state.chats[current]["messages"]:
        if msg["role"] == "assistant":
            api_messages.append({"role": "assistant", "content": msg["content"]})
        else:  # user 메시지
            if "image_url" in msg:
                api_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": msg["image_url"],
                                "detail": "high"  # ← 이거 추가
                            }
                        },
                        {
                            "type": "text",
                            "text": msg["content"]  # ← 순서 바꿈 (image 먼저)
                    ]
                })
            else:
                api_messages.append({"role": "user", "content": msg["content"]})

    # 5. Grok에게 요청
    with st.chat_message("assistant"):
        with st.spinner("아기 생각 중... 🍼✨ 사진도 보고, 웹도 뒤지고, X도 찾아보고 있어"):
            answer = call_grok_with_vision(
                api_messages,
                model="grok-4.20-0309-reasoning"   # ← 네가 원하는 바로 그 모델
            )
            st.write(answer)

    # 6. 어시스턴트 답변 저장 및 DB 저장
    st.session_state.chats[current]["messages"].append({"role": "assistant", "content": answer})
    save_chat(current)
    generate_title_if_needed(current)

    # 입력창 초기화
    st.session_state.input_key += 1
    st.rerun()
