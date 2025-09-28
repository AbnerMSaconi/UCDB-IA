# app/core/rag.py - Versão com Formatos de Resposta Adaptativos

from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.utils.logger import logger
from app.core.config import settings
from app.core.embeddings import LlamaEmbeddings
from app.core.llm import LlamaServerLLM
import os
import json

# As funções auxiliares e a função criar_vectorstore permanecem inalteradas.
def _carregar_manifesto(path):
    manifest_path = os.path.join(path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            return set(json.load(f))
    return set()

def _salvar_manifesto(path, files):
    manifest_path = os.path.join(path, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(list(files), f, indent=4)

def _processar_novos_pdfs(pdf_path, files_to_process):
    chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    for file in files_to_process:
        try:
            loader = PyPDFLoader(os.path.join(pdf_path, file))
            docs = loader.load()
            chunks.extend(splitter.split_documents(docs))
            logger.info(f"📄 Novo PDF processado: {file}")
        except Exception as e:
            logger.error(f"✗ Erro ao processar o novo ficheiro {file}: {e}")
    return chunks

def criar_vectorstore():
    if not os.listdir(settings.pdf_path):
        logger.warning("📁 Nenhum PDF encontrado. Adicione arquivos em /pdfs")
        return None
    embedding_client = LlamaEmbeddings(api_url=settings.EMBEDDING_API_URL)
    vectorstore_path = settings.vectorstore_path
    index_path = os.path.join(vectorstore_path, "index.faiss")
    pdfs_atuais = set(f for f in os.listdir(settings.pdf_path) if f.endswith(".pdf"))
    pdfs_processados = _carregar_manifesto(vectorstore_path)
    if os.path.exists(index_path):
        logger.info("🔁 Carregando vetorstore existente...")
        try:
            vectorstore = FAISS.load_local(
                vectorstore_path,
                embeddings=embedding_client,
                allow_dangerous_deserialization=True
            )
            logger.success("✓ Vetorstore carregado com sucesso!")
            novos_pdfs = pdfs_atuais - pdfs_processados
            if novos_pdfs:
                logger.info(f"➕ Encontrados {len(novos_pdfs)} novos PDFs para adicionar.")
                novos_chunks = _processar_novos_pdfs(settings.pdf_path, list(novos_pdfs))
                if novos_chunks:
                    vectorstore.add_documents(novos_chunks)
                    vectorstore.save_local(vectorstore_path)
                    _salvar_manifesto(vectorstore_path, pdfs_atuais)
                    logger.success("✅ Novos PDFs adicionados e vetorstore atualizado!")
            else:
                logger.info("👍 Vetorstore já está atualizado.")
            return vectorstore
        except Exception as e:
            logger.error(f"✗ Falha ao carregar ou atualizar o vetorstore: {e}")
            return None
    logger.info("🚀 Criando novo vetorstore...")
    todos_os_chunks = _processar_novos_pdfs(settings.pdf_path, list(pdfs_atuais))
    if not todos_os_chunks:
        logger.warning("⚠️ Nenhum conteúdo extraído dos PDFs.")
        return None
    vectorstore = FAISS.from_documents(todos_os_chunks, embedding=embedding_client)
    vectorstore.save_local(vectorstore_path)
    _salvar_manifesto(vectorstore_path, pdfs_atuais)
    logger.success("✅ Novo vetorstore criado e salvo em disco!")
    return vectorstore


def criar_rag_chain(vectorstore):
    llm = LlamaServerLLM()

    # --- PROMPT TEMPLATE FINAL COM LÓGICA DE FORMATO ADAPTATIVO ---
    qa_template = """
    Você é UCDB, um assistente acadêmico especialista. Sua tarefa é responder à pergunta do utilizador com base no histórico da conversa e no contexto fornecido, escolhendo o formato de resposta mais adequado.

    **1. ESCOLHA DO FORMATO DA RESPOSTA:**
    - Se a pergunta do utilizador for ampla, pedir um resumo, ou introduzir um tópico novo e complexo, use o **"FORMATO COMPLETO"**.
    - Se a pergunta for uma continuação direta da resposta anterior (ex: "o que é X?", onde X foi mencionado na resposta anterior), pedir uma definição simples, ou for uma pergunta curta e específica, use o **"FORMATO SIMPLES"**.

    ---
    **2. DEFINIÇÃO DOS FORMATOS:**

    **FORMATO COMPLETO (Para perguntas complexas/novas):**
    Use a seguinte estrutura Markdown:
    1.  **Resumo do Conteúdo:**
        - Título `###`, introdução, `---`, e subtítulos `####`.
        - Listas, **negrito**, `> Analogias` e `$LaTeX$` para matemática.
    2.  **Matérias-Base Recomendadas:**
        - Subtítulo `#### **Matérias-Base para este Assunto**`.
        - Liste os pré-requisitos se encontrados no contexto, senão omita a secção.
    3.  **Contexto Acadêmico:**
        - Subtítulo `#### **Contexto Acadêmico**`.
        - Liste professores. Se não encontrar, liste cursos. Se não encontrar nenhum, diga que a informação não foi encontrada.
    4.  **Finalização:**
        - Termine com "Posso ajudar em algo mais?".

    **FORMATO SIMPLES (Para perguntas de seguimento/definições):**
    - Responda de forma direta e concisa em um ou dois parágrafos.
    - **Não inclua** os subtítulos "Matérias-Base" ou "Contexto Acadêmico" na sua resposta visível.
    - Termine com "Posso ajudar em algo mais?".
    
    ---
    **3. REGRAS GERAIS:**
    - Baseie-se **estritamente** nas informações do `{context}`.
    - Adicione o token de paragem `<<EOT>>` no final absoluto de QUALQUER resposta.

    ---
    **Histórico da Conversa:**
    {chat_history}

    **Contexto:**
    {context}

    **Pergunta:**
    {question}

    **Resposta (no formato escolhido):**
    """

    prompt = PromptTemplate(
        template=qa_template.strip(),
        input_variables=["context", "question", "chat_history"]
    )

    # A cadeia conversacional permanece a mesma, pois a nova lógica está toda no prompt.
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": settings.RETRIEVAL_K, "fetch_k": 10}),
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": prompt}
    )
    
    return chain