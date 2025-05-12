import streamlit as st
import numpy as np
import faiss
from openai import OpenAI
from config import GEMINI_API_KEY, GEMINI_BASE_URL, GEMINI_EMBEDDING_DIM, GEMINI_EMBEDDING_MODEL


class RAGManager:
    def __init__(self, api_client=None):
        # 如果没有提供API客户端，创建Gemini客户端
        if api_client is None:
            self.client = OpenAI(
                api_key= GEMINI_API_KEY,  # 替换为您的实际Gemini API密钥
                base_url= GEMINI_BASE_URL
            )
        else:
            self.client = api_client

        # 存储文档内容和索引
        self.documents = []
        self.document_metadata = []
        self.vector_index = None
        self.enabled = False
        self.embedding_dim = GEMINI_EMBEDDING_DIM  # Gemini text-embedding-004模型的维度，可能需要调整
        self.embedding_model = GEMINI_EMBEDDING_MODEL  # Gemini的嵌入模型

    def add_document(self, text, metadata):
        # 文本分块
        chunks = self._chunk_text(text)
        for i, chunk in enumerate(chunks):
            self.documents.append(chunk)
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = i  # 为每个块添加块ID元数据
            self.document_metadata.append(chunk_metadata)
        # 重建索引
        self._build_index()

    def _chunk_text(self, text, chunk_size=1000, overlap=200):
        # 简单的文本分块 (按词分块)
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks if chunks else [text]  # 确保至少有一个块

    def _get_embedding(self, text):
        """使用Gemini API获取嵌入向量"""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            st.error(f"Error getting embedding: {e}")  # 获取嵌入时出错
            # 返回一个全零向量作为后备
            return [0.0] * self.embedding_dim

    def _build_index(self):
        if not self.documents:
            self.vector_index = None
            return

        # 生成文档向量
        embeddings = []
        for doc_text in self.documents:
            # 对每个文档生成嵌入
            embedding = self._get_embedding(doc_text)
            embeddings.append(embedding)

        embeddings_array = np.array(embeddings).astype('float32')

        # 创建FAISS索引
        self.vector_index = faiss.IndexFlatL2(self.embedding_dim)
        # 添加向量到索引
        self.vector_index.add(embeddings_array)

    def search(self, query, top_k=3):
        if not self.vector_index or not self.enabled:
            return []

        # 编码查询
        query_vector = np.array([self._get_embedding(query)]).astype('float32')

        # 搜索最近的向量
        distances, indices = self.vector_index.search(query_vector, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.documents):  # 检查索引边界
                results.append({
                    "text": self.documents[idx],
                    "metadata": self.document_metadata[idx],
                    "score": float(distances[0][i])
                })
        return results

    def toggle_rag(self, enabled):
        self.enabled = enabled

    def clear(self):
        self.documents = []
        self.document_metadata = []
        self.vector_index = None

    def is_empty(self):
        return len(self.documents) == 0


def get_enhanced_prompt(user_query, search_results):
    """根据RAG搜索结果创建增强提示"""
    if not search_results:
        return None

    context_items = []
    source_references_for_prompt = []

    for i, result in enumerate(search_results):
        doc_name = result["metadata"].get("name", "Document")
        source_tag = f"Source Document {i + 1}"

        page_num_str = result["metadata"].get("page", "")
        chunk_id_str = result["metadata"].get("chunk_id", "")

        location_info = ""
        if page_num_str:
            location_info = f" (Page {page_num_str})"
        elif chunk_id_str != "":
            location_info = f" (Chunk {chunk_id_str})"

        # 为上下文中的每个块添加明确的来源标识
        context_item_text = f"--- Begin Content from {source_tag} ({doc_name}{location_info}) ---\n"
        context_item_text += result['text'] + "\n"
        context_item_text += f"--- End Content from {source_tag} ({doc_name}{location_info}) ---\n\n"
        context_items.append(context_item_text)

        # 准备在提示中列出的来源
        source_references_for_prompt.append(f"{source_tag}: refers to content from '{doc_name}'{location_info}.")

    context_text = "".join(context_items)
    source_listing_for_prompt = "\nAvailable sources for citation:\n" + "\n".join(source_references_for_prompt)

    enhanced_prompt = (
        f"You are a helpful assistant. Please answer the user's question based on the provided document excerpts. "
        f"The document excerpts are clearly marked with source tags (e.g., 'Source Document 1', 'Source Document 2', etc.).\n"
        f"{source_listing_for_prompt}\n\n"
        f"When you use information from these excerpts, you MUST cite the source using its tag, for example: 'According to {source_tag.split(' ')[0]} {source_tag.split(' ')[1]} {source_tag.split(' ')[2]}, ...' or 'As stated in {source_tag}, ...'.\n"
        f"If the provided excerpts do not contain the answer, or if you are using your general knowledge, explicitly state that the information is from your general knowledge and not from the provided documents.\n\n"
        f"Here are the document excerpts:\n{context_text}\n"
        f"User's question: {user_query}\n"
        f"Your answer:"
    )

    return enhanced_prompt