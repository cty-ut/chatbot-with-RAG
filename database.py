import streamlit as st
import mysql.connector
from mysql.connector import pooling
from config import DB_CONFIG


# 创建数据库连接池
def init_db_pool():
    if 'db_connection_pool' not in st.session_state:
        try:
            # 初始化连接池
            pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="chatbot_pool",
                pool_size=5,  # 连接池大小，可根据需求调整
                **DB_CONFIG
            )
            st.session_state.db_connection_pool = pool
            print("Database connection pool initialized successfully")
        except Exception as e:
            print(f"Error initializing connection pool: {e}")
            # 如果连接池初始化失败，回退到原始连接方法
            st.session_state.db_connection_pool = None


# 连接到MySQL - 使用连接池
def connect_db():
    # 确保连接池已初始化
    if 'db_connection_pool' not in st.session_state:
        init_db_pool()

    # 如果连接池存在，从池中获取连接
    if st.session_state.db_connection_pool:
        try:
            return st.session_state.db_connection_pool.get_connection()
        except Exception as e:
            print(f"Error getting connection from pool: {e}")

    # 原始连接方法作为后备
    return mysql.connector.connect(**DB_CONFIG)


# 保存聊天功能，支持会话
def save_chat(role, content, conversation_id=None):
    """将聊天记录保存到特定会话"""
    # 如果未提供会话ID，则使用会话状态中的当前会话ID
    if conversation_id is None:
        if "current_conversation_id" not in st.session_state:
            # 如果没有当前会话，则创建一个新会话
            conversation_id = create_conversation("Default Conversation")
            st.session_state.current_conversation_id = conversation_id
        else:
            conversation_id = st.session_state.current_conversation_id
    cursor = None
    db_conn = connect_db()
    try:
        cursor = db_conn.cursor()
        sql = "INSERT INTO chat_history (role, content, conversation_id) VALUES (%s, %s, %s)"
        cursor.execute(sql, (role, content, conversation_id))
        db_conn.commit()

        # 更新会话的 updated_at 时间戳
        cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s", (conversation_id,))
        db_conn.commit()
        return True
    except Exception as e:
        print(f"Failed to save chat: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()


# 获取聊天记录
def get_chat_history():
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        cursor.execute("SELECT role, content FROM chat_history ORDER BY id DESC LIMIT 10")
        chats = cursor.fetchall()
        return chats[::-1]  # 反转以正确顺序显示
    except Exception as e:
        print(f"Failed to get chat history: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()


# 会话管理功能
def create_conversation(title="New Conversation"):
    """创建一个新会话并返回会话ID"""
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        sql = "INSERT INTO conversations (title) VALUES (%s)"
        cursor.execute(sql, (title,))
        conversation_id = cursor.lastrowid
        db_conn.commit()
        return conversation_id
    except Exception as e:
        print(f"Failed to create conversation: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()


def get_conversations():
    """获取所有会话列表"""
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT id, title, created_at, updated_at 
            FROM conversations 
            ORDER BY updated_at DESC
        """)
        return cursor.fetchall()
    except Exception as e:
        print(f"Failed to get conversations: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()


def get_conversation_messages(conversation_id):
    """从特定会话获取所有消息"""
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT role, content 
            FROM chat_history 
            WHERE conversation_id = %s 
            ORDER BY id
        """, (conversation_id,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Failed to get conversation messages: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()


def update_conversation_title(conversation_id, new_title):
    """更新会话标题"""
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        cursor.execute("""
            UPDATE conversations 
            SET title = %s 
            WHERE id = %s
        """, (new_title, conversation_id))
        db_conn.commit()
        return True
    except Exception as e:
        print(f"Failed to update conversation title: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()


def delete_conversation(conversation_id):
    """删除一个会话及其所有消息"""
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        # 由于外键约束，删除会话将删除其所有消息
        cursor.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
        db_conn.commit()
        return True
    except Exception as e:
        print(f"Failed to delete conversation: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_conn.is_connected():
            db_conn.close()