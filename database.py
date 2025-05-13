import streamlit as st
import psycopg2
from psycopg2 import pool
from config import DB_CONFIG


# 创建数据库连接池
def init_db_pool():
    if 'db_connection_pool' not in st.session_state:
        try:
            # 初始化连接池
            pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                dbname=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"]
            )
            st.session_state.db_connection_pool = pool
            print("Database connection pool initialized successfully")
        except Exception as e:
            print(f"Error initializing connection pool: {e}")
            # 如果连接池初始化失败，回退到原始连接方法
            st.session_state.db_connection_pool = None


# 连接到PostgreSQL - 使用连接池
def connect_db():
    # 确保连接池已初始化
    if 'db_connection_pool' not in st.session_state:
        init_db_pool()

    # 如果连接池存在，从池中获取连接
    if st.session_state.db_connection_pool:
        try:
            return st.session_state.db_connection_pool.getconn()
        except Exception as e:
            print(f"Error getting connection from pool: {e}")

    # 原始连接方法作为后备
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )


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
        db_conn.rollback()
        print(f"Failed to save chat: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_conn and not db_conn.closed:
            st.session_state.db_connection_pool.putconn(db_conn)


# 会话管理功能
def create_conversation(title):
    db_conn = connect_db()
    cursor = db_conn.cursor()
    try:
        # 使用RETURNING子句获取新插入的ID
        cursor.execute(
            "INSERT INTO conversations (title, created_at, updated_at) VALUES (%s, NOW(), NOW()) RETURNING id",
            (title,)
        )
        new_id = cursor.fetchone()[0]  # 使用fetchone获取返回的ID
        db_conn.commit()
        return new_id
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None
    finally:
        cursor.close()
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
        if db_conn and not db_conn.closed:
            st.session_state.db_connection_pool.putconn(db_conn)





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
        db_conn.rollback()
        print(f"Failed to update conversation title: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_conn and not db_conn.closed:
            st.session_state.db_connection_pool.putconn(db_conn)


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
        db_conn.rollback()
        print(f"Failed to delete conversation: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if db_conn and not db_conn.closed:
            st.session_state.db_connection_pool.putconn(db_conn)


# 创建数据库表
def create_tables():
    """创建必要的数据库表"""
    db_conn = connect_db()
    cursor = None
    try:
        cursor = db_conn.cursor()
        
        # 创建会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建聊天历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                role VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        db_conn.commit()
        print("Database tables created successfully")
    except Exception as e:
        db_conn.rollback()
        print(f"Failed to create tables: {e}")
    finally:
        if cursor:
            cursor.close()
        if db_conn and not db_conn.closed:
            st.session_state.db_connection_pool.putconn(db_conn)
