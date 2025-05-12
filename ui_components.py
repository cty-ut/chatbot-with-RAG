import streamlit as st
from config import PERSONAS, TEMPLATES
from database import create_conversation, get_conversations, update_conversation_title, delete_conversation, connect_db
from chat import switch_conversation, get_system_prompt
from file_processor import process_document_for_rag, process_general_file, process_image_file
import time

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # "关于" 部分
        st.title("💡 About This Chatbot")

        # 居中图片
        st.markdown("""
        <center>
        <img src='https://i.imgur.com/Qv2SO8o.png' width='120'/>
        </center>
        """, unsafe_allow_html=True)

        # 列表项
        st.markdown(""" 
        - 🤖 **Model**: gemini-2.0-flash

        - 📌 **Features**: Multi-conversation, RAG knowledge base, Templates, AI personas

        - 🚀 **Technology**: OpenAI API + Streamlit + FAISS
        """)

        # 添加一些间距
        st.markdown("<br>" * 1, unsafe_allow_html=True)

        # 在底部添加选项卡
        # 在一行中创建选项卡按钮
        col1, col2, col3, col4, col5 = st.columns(5)

        if col1.button("💬", help="Conversations", use_container_width=True):
            st.session_state.active_tab = "conversations"
            st.rerun()

        if col2.button("🎭", help="Templates", use_container_width=True):
            st.session_state.active_tab = "templates"
            st.rerun()

        if col3.button("👤", help="Persona", use_container_width=True):
            st.session_state.active_tab = "persona"
            st.rerun()

        if col4.button("⚙️", help="Settings", use_container_width=True):
            st.session_state.active_tab = "settings"
            st.rerun()

        if col5.button("📚", help="Knowledge Base", use_container_width=True):
            st.session_state.active_tab = "rag"
            st.rerun()

        # 显示活动选项卡内容
        st.markdown("---")

        # 根据当前活动选项卡渲染对应的内容
        if st.session_state.active_tab == "conversations":
            render_conversations_tab()
        elif st.session_state.active_tab == "templates":
            render_templates_tab()
        elif st.session_state.active_tab == "persona":
            render_persona_tab()
        elif st.session_state.active_tab == "settings":
            render_settings_tab()
        elif st.session_state.active_tab == "rag":
            render_rag_tab()


def render_conversations_tab():
    """渲染会话选项卡"""
    st.subheader("Conversations")

    # 新建会话表单
    with st.form(key="new_conversation_form", clear_on_submit=True):
        st.text_input("Title", value="New Conversation", max_chars=50, key="new_conv_title")
        submit_button = st.form_submit_button("Create", use_container_width=True)

        if submit_button:
            new_title_val = st.session_state.new_conv_title
            if new_title_val:
                new_id_val = create_conversation(new_title_val)
                if new_id_val:
                    # 切换到新会话
                    st.session_state.current_conversation_id = new_id_val
                    st.session_state.messages = []
                    st.session_state.messages_history = [{"role": "system", "content": get_system_prompt()}]
                    st.rerun()

    # 会话列表
    conversations_list_ui = get_conversations()

    if not conversations_list_ui:
        st.info("No conversations yet.")
    else:
        for conv_item in conversations_list_ui:
            conv_id, title_val, created_at, updated_at = conv_item

            # 这是当前会话吗？
            is_current_conv = conv_id == st.session_state.current_conversation_id

            # 使用列创建会话项
            col_item1, col_item2, col_item3 = st.columns([4, 1, 1])

            # 标题显示（如果需要则缩短）
            title_display_val = title_val if len(title_val) <= 20 else title_val[:17] + "..."

            # 会话标题按钮
            if col_item1.button(f"{title_display_val}", key=f"conv_{conv_id}",
                                use_container_width=True, disabled=is_current_conv):
                switch_conversation(conv_id)
                st.rerun()

            # 编辑/删除按钮
            if col_item2.button("✏️", key=f"edit_{conv_id}"):
                st.session_state.editing_conversation = conv_id
                st.session_state.editing_title = title_val
                st.rerun()

            if col_item3.button("🗑️", key=f"del_{conv_id}"):
                if delete_conversation(conv_id):
                    # 如果删除了当前会话，则切换到另一个
                    if conv_id == st.session_state.current_conversation_id:
                        remaining_convs = [c for c in conversations_list_ui if c[0] != conv_id]
                        if remaining_convs:
                            st.session_state.current_conversation_id = remaining_convs[0][0]
                        else:
                            # 如果没有剩余会话，则创建一个新会话
                            new_id_default = create_conversation("Default Conversation")
                            st.session_state.current_conversation_id = new_id_default

                        # 重置消息
                        st.session_state.messages = []
                        st.session_state.messages_history = [{"role": "system", "content": get_system_prompt()}]

                    st.rerun()

            # 如果需要，显示编辑表单
            if "editing_conversation" in st.session_state and st.session_state.editing_conversation == conv_id:
                with st.form(key=f"edit_form_{conv_id}"):
                    new_title_input = st.text_input("New Title", value=st.session_state.editing_title, max_chars=50,
                                                    key=f"edit_title_{conv_id}")

                    col_edit1, col_edit2 = st.columns(2)
                    update_button = col_edit1.form_submit_button("Save")
                    cancel_button = col_edit2.form_submit_button("Cancel")

                    if update_button and new_title_input:
                        update_conversation_title(conv_id, new_title_input)
                        del st.session_state.editing_conversation
                        del st.session_state.editing_title
                        st.rerun()

                    if cancel_button:
                        del st.session_state.editing_conversation
                        del st.session_state.editing_title
                        st.rerun()


def render_templates_tab():
    """渲染模板选项卡"""
    from database import save_chat

    st.subheader("Templates")

    # 模板选择
    selected_template_key = st.selectbox(
        "Select template",
        options=list(TEMPLATES.keys()),
        format_func=lambda x: f"{TEMPLATES[x]['icon']} {x}"
    )

    current_template = TEMPLATES[selected_template_key]
    generated_prompt = ""  # 初始化提示

    # 模板表单
    with st.form(key=f"template_form"):
        if selected_template_key == "Article":
            topic_input = st.text_input("Topic", value="Artificial Intelligence")
            aspects_input = st.text_input("Aspects", value="definition, applications, challenges")
            word_count_input = st.text_input("Word count", value="1000")
            generated_prompt = current_template["prompt"].format(topic=topic_input, aspects=aspects_input,
                                                                 word_count=word_count_input)

        elif selected_template_key == "Code":
            language_input = st.text_input("Language", value="Python")
            code_input = st.text_area("Code", value="# Paste code here", height=100)
            generated_prompt = current_template["prompt"].format(language=language_input, code=code_input)

        elif selected_template_key == "Summary":
            content_input = st.text_area("Content", value="Paste content to summarize", height=100)
            generated_prompt = current_template["prompt"].format(content=content_input)

        # 应用模板按钮
        if st.form_submit_button("Apply Template", use_container_width=True):
            # 添加到聊天
            st.session_state.messages.append({"role": "user", "content": generated_prompt})
            st.session_state.messages_history.append({"role": "user", "content": generated_prompt})

            # 保存到数据库
            save_chat("user", generated_prompt, st.session_state.current_conversation_id)

            # 设置标志以在重新运行后触发 get_answer()
            st.session_state.get_template_answer = True

            # 重新运行以显示新消息并获取回复
            st.rerun()


def render_persona_tab():
    """渲染角色选项卡"""
    from database import save_chat
    from chat import get_system_prompt

    st.subheader("AI Persona")

    # 显示当前角色
    current_persona_val = st.session_state.current_persona
    st.info(f"Current: {PERSONAS[current_persona_val]['icon']} {current_persona_val}")

    # 选择角色
    selected_persona_key = st.selectbox(
        "Select AI Persona",
        options=list(PERSONAS.keys()),
        index=list(PERSONAS.keys()).index(current_persona_val),
        format_func=lambda x: f"{PERSONAS[x]['icon']} {x}"
    )

    st.caption(f"{PERSONAS[selected_persona_key]['description']}")

    # 应用角色按钮
    if st.button("Apply Persona", use_container_width=True):
        # 更新角色
        st.session_state.current_persona = selected_persona_key

        # 更新系统提示
        if len(st.session_state.messages_history) > 0 and st.session_state.messages_history[0]["role"] == "system":
            st.session_state.messages_history[0]["content"] = get_system_prompt()
        else:
            st.session_state.messages_history.insert(0, {"role": "system", "content": get_system_prompt()})

        # 添加系统通知
        notification_message = f"I've switched to {selected_persona_key} mode. How can I help you?"
        st.session_state.messages.append({
            "role": "assistant",
            "content": notification_message
        })

        # 将通知消息保存到数据库
        save_chat("assistant", notification_message,
                  st.session_state.current_conversation_id)

        st.rerun()


def render_settings_tab():
    """渲染设置选项卡"""
    st.subheader("Settings")

    # 创造力调节滑块
    st.markdown("### Creativity Regulation")
    st.session_state.temperature = st.slider(
        'Temperature',
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.temperature,
        step=0.1,
        help='Adjust the slider to control the creativity of the AI, higher values make AI more creative!'
    )

    # 清除按钮
    if st.button("🧹 Clear Chat", use_container_width=True):
        # 清除当前会话消息
        db_conn_clear = connect_db()
        cursor_clear = None
        try:
            cursor_clear = db_conn_clear.cursor()
            cursor_clear.execute(
                "DELETE FROM chat_history WHERE conversation_id = %s",
                (st.session_state.current_conversation_id,)
            )
            db_conn_clear.commit()
        except Exception as e:
            st.error(f"Clear failed: {e}")
        finally:
            if cursor_clear:
                cursor_clear.close()
            if db_conn_clear.is_connected():
                db_conn_clear.close()

        # 重置会话状态
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Enter your message in the input box to chat with AI!"
        }]
        st.session_state.messages_history = [{"role": "system", "content": get_system_prompt()}]
        st.rerun()


def render_rag_tab():
    """渲染RAG选项卡"""
    st.subheader("Knowledge Base")

    # 标志，用于判断是否需要在文件处理后rerun
    needs_rerun_after_rag_processing = False

    # 文档上传
    st.markdown("### Upload Documents")
    # 为 file_uploader 提供一个唯一的 key
    uploaded_file_for_rag = st.file_uploader(
        "Upload PDF, DOCX, PPTX or TXT files for Knowledge Base",
        type=["pdf", "docx", "pptx", "txt"],
        key="rag_file_uploader_sidebar"
    )

    # 处理上传文件
    if uploaded_file_for_rag:
        # 简单地用 session state 记录上一个处理的文件名，避免因 streamlit 保持 uploader 状态而重复处理
        if "last_uploaded_rag_filename" not in st.session_state or \
                st.session_state.last_uploaded_rag_filename != uploaded_file_for_rag.name:

            with st.spinner(f"Processing {uploaded_file_for_rag.name} for Knowledge Base..."):
                # 记录当前文件名，以便下次比较
                st.session_state.last_uploaded_rag_filename = uploaded_file_for_rag.name

                initial_rag_empty_status = st.session_state.rag_manager.is_empty()  # 处理前状态
                processing_result = process_document_for_rag(uploaded_file_for_rag)
                st.success(processing_result)

                # 检查处理后RAG状态是否真的改变了（从空变为非空）
                current_rag_empty_status = st.session_state.rag_manager.is_empty()  # 处理后状态
                if initial_rag_empty_status and not current_rag_empty_status:
                    needs_rerun_after_rag_processing = True  # 设置标志

    # RAG状态显示和控制
    is_rag_empty_now = st.session_state.rag_manager.is_empty()
    is_rag_enabled_now = st.session_state.rag_manager.enabled

    if is_rag_empty_now:
        st.info("Knowledge base is empty. Please upload documents first.")
        # 为 toggle 提供唯一的 key
        st.toggle("Enable RAG", value=False, disabled=True, key="rag_toggle_disabled_sb")
    else:
        # 为 toggle 提供唯一的 key
        rag_toggle_button_state = st.toggle("Enable RAG", value=is_rag_enabled_now, key="rag_toggle_enabled_sb")
        if rag_toggle_button_state != is_rag_enabled_now:
            st.session_state.rag_manager.toggle_rag(rag_toggle_button_state)
            status_message = "enabled" if rag_toggle_button_state else "disabled"
            st.success(f"RAG has been {status_message}.")
            needs_rerun_after_rag_processing = True  # 切换后也需要rerun

    # 清空知识库按钮
    if not is_rag_empty_now:
        # 为 button 提供唯一的 key
        if st.button("Clear Knowledge Base", use_container_width=True, key="clear_rag_button_sb"):
            st.session_state.rag_manager.clear()
            st.session_state.rag_manager.toggle_rag(False)
            # 清空后，重置 last_uploaded_rag_filename，允许重新上传同名文件
            if "last_uploaded_rag_filename" in st.session_state:
                del st.session_state.last_uploaded_rag_filename
            st.success("Knowledge base has been cleared.")
            needs_rerun_after_rag_processing = True  # 清空后也需要rerun

    # 在所有RAG选项卡UI元素渲染完毕后，检查是否需要rerun
    if needs_rerun_after_rag_processing:
        st.rerun()


def render_main_content():
    """渲染主要内容区域"""
    from database import save_chat
    from chat import get_answer

    st.title("🤖 C-bot")

    # 显示对话的历史列表
    for message_item in st.session_state.messages:
        # 聊天窗口
        with st.chat_message(message_item["role"]):
            st.markdown(message_item["content"])

    # 用户输入框
    user_input_text = st.chat_input("Type your message here...")

    # 处理用户输入
    if user_input_text:
        # 显示用户输入的内容到聊天窗口
        with st.chat_message("user"):
            st.write(user_input_text)
        # 把用户的消息添加到会话历史中
        st.session_state.messages.append({"role": "user", "content": user_input_text})
        st.session_state.messages_history.append({"role": "user", "content": user_input_text})
        save_chat('user', user_input_text)
        get_answer()

    # 检查是否需要为模板获取答案
    if "get_template_answer" in st.session_state and st.session_state.get_template_answer:
        get_answer()
        st.session_state.get_template_answer = False

    # 通用文件上传器
    general_uploaded_file = st.file_uploader('Upload file (for direct analysis, not Knowledge Base)',
                                             type=["docx", "pdf", "xlsx", "txt", "pptx", "jpg", "png",
                                                   "mp3", "wav", "m4a", "ogg"],
                                             key="general_file_uploader")

    # 处理上传的文件
    if general_uploaded_file and general_uploaded_file.name != st.session_state.get("uploaded_file_name", None):
        # 检查文件类型并提供适当的状态信息
        file_extension = general_uploaded_file.name.split('.')[-1].lower()

        # 添加音频文件处理的UI反馈
        if file_extension in ["mp3", "wav", "m4a", "ogg"]:
            with st.status("处理音频文件...", expanded=True) as status:
                st.write("⏳ 上传音频文件...")
                st.write("🔊 准备音频数据...")
                # 创建处理进度条
                progress_bar = st.progress(0)
                for i in range(1, 101):
                    # 增加延迟以更好地展示进度
                    if i == 25:
                        st.write("🎯 正在转录音频内容...")
                    elif i == 50:
                        st.write("📝 分析音频内容...")
                    elif i == 75:
                        st.write("🧠 生成理解结果...")
                    # 更新进度条
                    progress_bar.progress(i)
                    if i < 100:  # 不要让最后一步太快
                        time.sleep(0.02)

                # 处理文件
                extracted_text_general = process_general_file(general_uploaded_file)
                st.write("✅ 音频处理完成!")
                status.update(label="音频处理完成!", state="complete")
        else:
            # 其他类型文件的处理
            extracted_text_general = process_general_file(general_uploaded_file)

        if extracted_text_general:
            # 将文件内容保存到会话状态
            st.session_state.uploaded_file_text = extracted_text_general
            st.session_state.uploaded_file_name = general_uploaded_file.name  # 记录文件名

            # 将内容添加到聊天记录
            st.session_state.messages.append({"role": "user", "content": extracted_text_general})
            st.session_state.messages_history.append({"role": "user", "content": extracted_text_general})

            # 保存到数据库
            save_chat('user', extracted_text_general, st.session_state.current_conversation_id)

            # 获取AI答案
            get_answer()