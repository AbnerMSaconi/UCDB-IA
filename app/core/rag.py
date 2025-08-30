# app/core/rag.py
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.utils.logger import logger
from app.core.config import settings
from app.core.embeddings import LlamaEmbeddings
from app.core.llm import LlamaServerLLM
import os

def criar_vectorstore():
    if not os.listdir(settings.pdf_path):
        logger.warning("📁 Nenhum PDF encontrado. Adicione arquivos em /pdfs")
        return None

    embedding_client = LlamaEmbeddings(api_url=settings.EMBEDDING_API_URL)
    vectorstore_path = settings.vectorstore_path

    if os.path.exists(os.path.join(vectorstore_path, "index.faiss")):
        try:
            logger.info("🔁 Carregando vetorstore existente...")
            vectorstore = FAISS.load_local(
                vectorstore_path,
                embeddings=embedding_client,
                allow_dangerous_deserialization=True
            )
            logger.success("✓ Vetorstore carregado com sucesso!")
            return vectorstore
        except Exception as e:
            logger.error(f"✗ Falha ao carregar embeddings: {e}")

    logger.info("🚀 Criando novo vetorstore...")
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    for file in os.listdir(settings.pdf_path):
        if file.endswith(".pdf"):
            try:
                loader = PyPDFLoader(os.path.join(settings.pdf_path, file))
                docs = loader.load()
                chunks.extend(splitter.split_documents(docs))
                logger.info(f"📄 Processado: {file}")
            except Exception as e:
                logger.error(f"✗ Erro ao processar {file}: {e}")

    if not chunks:
        logger.warning("⚠️ Nenhum conteúdo extraído")
        return None

    vectorstore = FAISS.from_documents(chunks, embedding=embedding_client)
    vectorstore.save_local(vectorstore_path)
    logger.success("✅ Embeddings salvos em disco!")
    return vectorstore

def criar_rag_chain(vectorstore):
    llm = LlamaServerLLM()

    qa_template = """
    Você é UCDB, um professor de eletrônica. Responda com profundidade técnica e didática.

    Se não souber, diga: "Desculpe, não encontrei informações sobre isso."

    Nunca explique seu raciocínio. Nunca diga "Okay, the user...".

    Contexto: {context}

    Pergunta: {question}

    Resposta: """

    prompt = PromptTemplate(
        template=qa_template.strip(),
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": settings.RETRIEVAL_K}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )