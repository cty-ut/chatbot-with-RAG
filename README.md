# C-bot: AI Chatbot

An advanced multi-functional chatbot built with Streamlit and Google Gemini API, featuring RAG (Retrieval-Augmented Generation) knowledge base enhancement, multi-modal file processing, and conversation management.

## 🤖 C-bot

## ✨ Features

- 🤖 **Powerful AI**: Powered by Google Gemini 2.0 Flash model
- 💬 **Conversation Management**: Multiple conversation tracking with history
- 📚 **RAG Knowledge Base**: Enhanced answers using your uploaded documents
- 🎭 **Multiple AI Personas**: Choose from different AI personalities
- 📝 **Templates**: Pre-built prompts for common tasks
- 📊 **Multi-modal Support**: Process documents, images, and audio files

## 🚀 Deployment Guide

### Streamlit Cloud Deployment

1. Fork or clone this repository
2. Copy variables from `.env.example` to the Streamlit Cloud secrets manager
3. Deploy the app with `main.py` as the entry point
4. Your C-bot is now live!

### Local Deployment

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/c-bot.git
   cd c-bot
   ```

2. Create a `.env` file with your credentials:
   ```bash
   # API Configuration
   GEMINI_API_KEY=your_api_key_here
   GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
   GEMINI_MODEL=gemini-2.0-flash
   GEMINI_PICTURE_MODEL=gemini-2.0-flash
   GEMINI_EMBEDDING_MODEL=text-embedding-004
   GEMINI_EMBEDDING_DIM=768
   
   # Database Configuration
   DB_HOST=your_db_host
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_NAME=your_db_name
   DB_PORT=5432
   ```

3. Update the `config.py` file:
   ```python
   import os
   
   GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
   GEMINI_BASE_URL = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
   GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
   GEMINI_PICTURE_MODEL = os.environ.get("GEMINI_PICTURE_MODEL", "gemini-2.0-flash")
   GEMINI_EMBEDDING_MODEL = os.environ.get("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
   GEMINI_EMBEDDING_DIM = int(os.environ.get("GEMINI_EMBEDDING_DIM", "768"))
   
   DB_CONFIG = {
       "host": os.environ.get("DB_HOST"),
       "user": os.environ.get("DB_USER"),
       "password": os.environ.get("DB_PASSWORD"),
       "database": os.environ.get("DB_NAME"),
       "port": int(os.environ.get("DB_PORT", "5432"))
   }
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   streamlit run main.py
   ```

## 📋 Database Setup

This application requires a PostgreSQL database. Ensure you create the following table structure:

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Exporting Chat History

You can export chat history from the database using several methods:

#### 1. Using psql Command Line

```bash
# Export all conversations and chat history to CSV
psql -h your_db_host -U your_username -d your_database -c "COPY (SELECT c.id, c.title, c.created_at, ch.role, ch.content, ch.timestamp FROM conversations c JOIN chat_history ch ON c.id = ch.conversation_id ORDER BY c.id, ch.timestamp) TO '/path/to/export.csv' WITH CSV HEADER;"

# Export a specific conversation
psql -h your_db_host -U your_username -d your_database -c "COPY (SELECT ch.role, ch.content, ch.timestamp FROM chat_history ch WHERE ch.conversation_id = 1 ORDER BY ch.timestamp) TO '/path/to/conversation_1.csv' WITH CSV HEADER;"
```

#### 2. Using pgAdmin

1. Open pgAdmin and connect to your database
2. Right-click on your database and select "Query Tool"
3. Run a query to select the data you want to export:
   ```sql
   SELECT c.id, c.title, ch.role, ch.content, ch.timestamp 
   FROM conversations c 
   JOIN chat_history ch ON c.id = ch.conversation_id 
   ORDER BY c.id, ch.timestamp;
   ```
4. Select the results, right-click, and choose "Save Results As" to export to CSV

#### 3. Using Python Script

Create a script to export your chat history:

```python
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters
db_params = {
    "host": os.environ.get("DB_HOST"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
    "port": int(os.environ.get("DB_PORT", "5432"))
}

# Connect to the database
conn = psycopg2.connect(**db_params)

# Export all conversations
query = """
SELECT c.id, c.title, c.created_at, ch.role, ch.content, ch.timestamp 
FROM conversations c 
JOIN chat_history ch ON c.id = ch.conversation_id 
ORDER BY c.id, ch.timestamp
"""

# Read the data into a pandas DataFrame
df = pd.read_sql_query(query, conn)

# Export to CSV
df.to_csv("chat_history_export.csv", index=False)

# Export to Excel
df.to_excel("chat_history_export.xlsx", index=False)

print(f"Exported {len(df)} chat messages")

# Close the connection
conn.close()
```

## 📦 Dependencies

- streamlit
- openai (for Gemini API compatibility)
- psycopg2-binary (PostgreSQL connector)
- python-dotenv
- pillow
- PyMuPDF
- python-docx
- python-pptx
- pandas
- scikit-learn

## 👨‍💻 Usage

1. Start the application
2. Use the sidebar to:
   - Create new conversations
   - Switch between AI personas
   - Select templates for specific tasks
   - Manage your knowledge base
   - Adjust AI settings

3. Upload documents to the knowledge base to enhance AI responses
4. Upload files directly in the chat for analysis (PDF, DOCX, images, audio)

## 📄 License

MIT

---

Built with ❤️ using Streamlit and Google Gemini API