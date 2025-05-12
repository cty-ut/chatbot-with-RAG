# C-bot: AI聊天机器人

基于Streamlit和Google Gemini API构建的多功能聊天机器人，具有RAG知识库增强、多模态文件处理和对话管理功能。

## 功能特点

- 🤖 使用Google Gemini AI模型
- 💬 多会话管理与历史记录
- 📚 RAG知识库增强问答
- 📝 多种AI角色与模板
- 📊 多模态文件处理（文档、图像、音频）

## 部署说明

1. 克隆仓库
2. 创建`.env`文件并填写配置（参考`.env.example`）
3. 安装依赖: `pip install -r requirements.txt`
4. 运行应用: `streamlit run app.py`

## 数据库配置

本应用需要MySQL数据库支持。请确保创建了相应的数据库和表结构。