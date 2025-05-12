import streamlit as st
import atexit

from config import PERSONAS
from database import init_db_pool
from rag import RAGManager
from chat import init_chat, client
from ui_components import render_sidebar, render_main_content

# 设置页面标题和布局
st.set_page_config(page_title="C-chatbot", layout="wide")

# 初始化数据库连接池
init_db_pool()

# 初始化 RAG 管理器
if 'rag_manager' not in st.session_state:
    st.session_state.rag_manager = RAGManager(api_client=client)

# 初始化会话状态
if "current_persona" not in st.session_state:
    st.session_state.current_persona = "Standard Assistant"

if "temperature" not in st.session_state:
    st.session_state.temperature = 1.0

if "current_conversation_id" not in st.session_state:
    # 检查现有会话
    from database import get_conversations, create_conversation

    conversations_list = get_conversations()
    if conversations_list:
        st.session_state.current_conversation_id = conversations_list[0][0]  # 使用最新的会话
    else:
        # 创建一个默认会话
        new_id = create_conversation("Default Conversation")
        st.session_state.current_conversation_id = new_id

if "messages" not in st.session_state:
    init_chat()

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "conversations"

# 渲染侧边栏
render_sidebar()

# 渲染主内容区域
render_main_content()


# 关闭数据库连接函数
def close_db_on_exit():
    # 清空RAG知识库
    if 'rag_manager' in st.session_state:
        st.session_state.rag_manager.clear()
        print("RAG knowledge base cleared.")


# 注册退出时自动执行的关闭事件
atexit.register(close_db_on_exit)

# 主应用入口点（如果直接运行此文件）
if __name__ == "__main__":
    pass  # 主要逻辑已在上面执行