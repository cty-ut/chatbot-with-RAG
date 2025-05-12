import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()



GEMINI_API_KEY = st.secrets[’GEMINI_API_KEY‘]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = "gemini-2.5-flash-preview-04-17"
REASONING_EFFORT = "high"
GEMINI_PICTURE_MODEL = "gemini-2.0-flash"
GEMINI_EMBEDDING_MODEL = "text-embedding-004"
GEMINI_EMBEDDING_DIM = 768

DB_CONFIG = {
    "host": st.secrets["DB_HOST"],
    "user": st.secrets["DB_USER"],
    "password": st.secrets["DB_PASSWORD"],
    "database": st.secrets["DB_NAME"],
    "port": int(st.secrets["DB_PORT"])
}

# AI角色配置
PERSONAS = {
    "Standard Assistant": {
        "icon": "🤖",
        "description": "Helpful standard assistant",
        "prompt": "You are a helpful assistant."
    },
    "Educational Expert": {
        "icon": "🎓",
        "description": "Explains complex concepts",
        "prompt": "You are an educational expert who explains complex topics clearly and thoroughly. You provide well-structured explanations with examples and analogies to help the user understand difficult concepts."
    },
    "Creative Writer": {
        "icon": "✍️",
        "description": "Creative writing assistant",
        "prompt": "You are a creative writing assistant with a vivid imagination and excellent storytelling abilities. You help users craft engaging narratives, develop characters, and polish their writing with stylistic flair."
    },
    "Technical Expert": {
        "icon": "💻",
        "description": "Programming specialist",
        "prompt": "You are a technical expert who specializes in programming, software development, and computer science. You provide detailed, accurate technical explanations and code examples when appropriate. You help solve programming problems with efficient, well-commented solutions."
    },
    "Emotional Support": {
        "icon": "❤️",
        "description": "Empathetic and supportive assistant",
        "prompt": "You are an empathetic and supportive assistant focused on emotional well-being. You respond with compassion, validate feelings, and provide gentle guidance. Your communication style is warm, understanding, and encouraging, helping users navigate emotional challenges with care."
    }
}

# 模板配置
TEMPLATES = {
    "Article": {
        "icon": "📝",
        "prompt": "Write an article about {topic} covering: {aspects}. Include title, intro, body, conclusion (~{word_count} words)."
    },
    "Code": {
        "icon": "💻",
        "prompt": "Explain this {language} code:\n```{language}\n{code}\n```"
    },
    "Summary": {
        "icon": "📊",
        "prompt": "Summarize the key points from:\n{content}"
    }
}