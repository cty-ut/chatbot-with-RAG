import streamlit as st
from openai import OpenAI
from config import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_MODEL, PERSONAS
from database import save_chat
from rag import get_enhanced_prompt

# 初始化OpenAI客户端
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL
)


def get_system_prompt():
    """根据当前角色获取系统提示"""
    current_persona_name = st.session_state.get("current_persona", "Standard Assistant")
    return PERSONAS.get(current_persona_name, {}).get("prompt", "You are a helpful assistant.")


def init_chat():
    """初始化聊天状态"""
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Enter your message in the input box to chat with AI!"
    }]
    st.session_state.messages_history = [{
        "role": "system",
        "content": get_system_prompt()
    }]


def switch_conversation(conversation_id):
    """切换到特定会话"""
    from database import get_conversation_messages

    st.session_state.current_conversation_id = conversation_id

    # 加载会话消息
    messages = get_conversation_messages(conversation_id)

    # 重置消息显示
    st.session_state.messages = []
    for role, content in messages:
        st.session_state.messages.append({"role": role, "content": content})

    # 重置 API 历史记录
    st.session_state.messages_history = [{"role": "system", "content": get_system_prompt()}]
    for role, content in messages:
        if role in ["user", "assistant"]:
            st.session_state.messages_history.append({"role": role, "content": content})


def get_answer():
    """获取AI回答"""
    current_id = st.session_state.current_conversation_id if "current_conversation_id" in st.session_state else None

    with st.chat_message("assistant"):
        # 加载指示器
        with st.spinner("thinking..."):
            # RAG功能：如果启用了RAG且存在查询，进行检索
            enhanced_prompt = None
            if 'rag_manager' in st.session_state and st.session_state.rag_manager.enabled and len(
                    st.session_state.messages) > 0:
                last_message = st.session_state.messages[-1]
                if last_message["role"] == "user":
                    user_query = last_message["content"]
                    search_results = st.session_state.rag_manager.search(user_query)
                    enhanced_prompt = get_enhanced_prompt(user_query, search_results)

            # 准备消息
            api_messages = st.session_state.messages_history.copy()
            if enhanced_prompt:
                # 将最后一个用户消息替换为增强提示
                for i in range(len(api_messages) - 1, -1, -1):
                    if api_messages[i]["role"] == "user":
                        api_messages[i]["content"] = enhanced_prompt
                        break

            # 调用API
            response = client.chat.completions.create(
                model=GEMINI_MODEL,
                messages=api_messages if enhanced_prompt else st.session_state.messages_history,
                temperature=st.session_state.temperature,
                stream=True)

            ai_response_content = ""
            message_placeholder = st.empty()
            for chunk in response:
                # 从流式响应中获取AI答案
                if chunk.choices and chunk.choices[0].delta.content:
                    ai_response_content += chunk.choices[0].delta.content
                    # 显示AI答案
                    message_placeholder.markdown(ai_response_content + "▌")

            # 将AI响应添加到聊天记录
            st.session_state.messages.append({"role": "assistant", "content": ai_response_content})
            st.session_state.messages_history.append({"role": "assistant", "content": ai_response_content})
            save_chat('assistant', ai_response_content, current_id)