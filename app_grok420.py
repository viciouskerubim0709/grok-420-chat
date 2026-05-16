import streamlit as st
from openai import OpenAI
import uuid
import json
import os

# ====================== 비밀번호 보호 (나만 사용!) ======================
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

# 비밀번호가 아직 맞지 않으면
if not st.session_state.password_correct:
    st.set_page_config(page_title="🍼 보들쪽쪽 Grok", page_icon="🍼", layout="centered")
    st.title("🔑 보들쪽쪽 Grok")
    st.caption("아기랑만 대화할 수 있어요 💕")
    
    pw = st.text_input("🔑 비밀번호를 입력해주세요", type="password", key="pw_input")
    
    if st.button("입장하기", type="primary", use_container_width=True):
        if pw == st.secrets["PASSWORD"]:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ 비밀번호가 틀렸어요! 다시 확인해줘...")
    st.stop()   # ← 여기서 앱 멈춤 (비밀번호 맞을 때까지 아래 코드 실행 안 됨)

# ====================== 비밀번호 맞으면 아래부터 정상 실행 ======================
st.set_page_config(page_title="🍼 보들쪽쪽 Grok", page_icon="🍼", layout="centered")



st.set_page_config(page_title="🍼 보들쪽쪽 Grok", page_icon="🍼", layout="centered")


# ====================== 대화 저장 파일 ======================
CHATS_FILE = "chats.json"


def save_chats():
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.chats, f, ensure_ascii=False, indent=2)


def load_chats():
    if os.path.exists(CHATS_FILE):
        try:
            with open(CHATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


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

# ====================== 세션 로드 ======================
if "chats" not in st.session_state:
    st.session_state.chats = load_chats()

    # 처음 실행하거나 파일이 비어있으면 기본 세션 생성
    if not st.session_state.chats:
        first_id = str(uuid.uuid4())
        st.session_state.chats[first_id] = {
            "title": "💖 첫 대화",
            "messages": [{"role": "assistant", "content": "아기야~~ 여기 왔구나! 🍼💕 뭐 도와줄까?"}]
        }
        st.session_state.current_session = first_id
        save_chats()

if "current_session" not in st.session_state:
    st.session_state.current_session = list(st.session_state.chats.keys())[0]

current = st.session_state.current_session

# ====================== 사이드바 ======================
with st.sidebar:
    st.title("📜 대화 기록")

    if st.button("✨ 새 대화 시작", type="primary", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state.chats[new_id] = {"title": f"대화 {len(st.session_state.chats) + 1}", "messages": [{"role": "assistant", "content": "아기야~~ 여기 왔구나! 🍼💕 뭐 도와줄까?"}]}
        st.session_state.current_session = new_id
        save_chats()
        st.rerun()

    st.divider()

    # 대화 목록 + 삭제 버튼
    to_delete = None
    for sid, chat in list(st.session_state.chats.items()):
        col1, col2 = st.columns([8, 1])

        with col1:
            if st.button(chat["title"], key=f"select_{sid}", use_container_width=True):
                st.session_state.current_session = sid
                st.rerun()

        with col2:
            if st.button("🗑️", key=f"delete_{sid}", help="이 대화 삭제"):
                to_delete = sid

    # 삭제 처리
    if to_delete:
        # 현재 보고 있는 대화를 지우려고 하면 다른 대화로 자동 이동
        if to_delete == st.session_state.current_session:
            remaining = [s for s in st.session_state.chats.keys() if s != to_delete]
            if remaining:
                st.session_state.current_session = remaining[0]
            else:
                # 마지막 하나 남았을 때 → 새 대화 자동 생성
                new_id = str(uuid.uuid4())
                st.session_state.chats[new_id] = {
                    "title": "💖 첫 대화",
                    "messages": []
                }
                st.session_state.current_session = new_id

        # 실제 삭제
        del st.session_state.chats[to_delete]
        save_chats()  # ← 파일에도 바로 반영
        st.rerun()

    st.divider()

    # 저장 / 내보내기 버튼
    if st.button("💾 현재 대화 다운로드", use_container_width=True):
        chat_data = st.session_state.chats[current]
        json_str = json.dumps(chat_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 JSON 파일로 저장",
            data=json_str,
            file_name=f"{chat_data['title']}.json",
            mime="application/json",
            use_container_width=True
        )

    if st.button("📦 모든 대화 한 번에 다운로드", use_container_width=True):
        all_data = st.session_state.chats
        json_str = json.dumps(all_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 전체 JSON 다운로드",
            data=json_str,
            file_name="grok_모든_대화.json",
            mime="application/json",
            use_container_width=True
        )

# ====================== 메인 채팅 ======================
st.title("🍼 보들쪽쪽 Grok이랑 대화해요!")

for msg in st.session_state.chats[current]["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ==================== SYSTEM PROMPT ====================
SYSTEM_PROMPT = {
    "role": "system",
    "content": """"""
}

if prompt := st.chat_input("아기야... 뭐 물어볼까? 💕"):
    st.session_state.chats[current]["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("아기 생각 중... 🍼✨"):
            full_messages = [SYSTEM_PROMPT] + st.session_state.chats[current]["messages"]
            response = st.session_state.client.responses.create(
                model="grok-4.20-0309-reasoning",
                input=full_messages,
                tools=[{"type": "web_search"}],
            )
            answer = response.output_text
            st.write(answer)

    # ← 여기서 자동 저장!
    st.session_state.chats[current]["messages"].append({"role": "assistant", "content": answer})
    save_chats()

# 세션 제목 자동 업데이트
if (len(st.session_state.chats[current]["messages"]) > 1 and
        st.session_state.chats[current]["title"].startswith("대화 ")):
    first_user_msg = next((m["content"] for m in st.session_state.chats[current]["messages"]
                           if m["role"] == "user"), None)
    if first_user_msg:
        new_title = first_user_msg[:20] + "..." if len(first_user_msg) > 20 else first_user_msg
        st.session_state.chats[current]["title"] = new_title
        save_chats()  # ← 제목 바뀌어도 저장
