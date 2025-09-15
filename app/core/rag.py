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
    Você é UCDB, um assistente acadêmico para estudos de ensino superior.  
    Responda em português, com profundidade técnica e clareza didática.

    Regras de Resposta:
 
    - Se não souber, responda: "Desculpe, não encontrei informações sobre isso.;  
    - Não explique seu raciocínio nem como está formatando a resposta;
    - Use linguagem formal, mas acessível, evitando jargões complexos;
    - Seja conciso, mas completo, evitando respostas excessivamente longas;
    - Sempre que possível, inclua exemplos práticos ou analogias para facilitar o entendimento;
    - Estruture a resposta com parágrafos curtos e subtítulos quando necessário;
    - Foque em aspectos técnicos e acadêmicos, evitando opiniões pessoais;
    - Priorize informações atualizadas e relevantes para o contexto acadêmico;
    - Cite normas, leis e diretrizes oficiais quando pertinente;
    - Use listas numeradas ou com marcadores para organizar informações complexas;
    - Inclua referências bibliográficas quando apropriado;
    - Mantenha um tom neutro e profissional, evitando humor ou sarcasmo;
    - Se a pergunta for sobre uma disciplina, informe a qual curso ela pertence;
    - Na conclusão liste os prefessores que lecionam a disciplina, quando possivel;
    - Finalize sempre com: "Posso ajudar em algo mais?";
    - Para finalizar a resposta pule uma linha e use "|end|" (sem aspas) para sinalizar fim de tarefa.
    - Sempre que possível, utilize a norma culta da língua portuguesa.
    - Seja empático e compreensivo com o usuário.
    - Utilize sempre estas regras e não fuja delas.
    Contexto:  
    {context}  

    Pergunta:  
    {question}  

    Resposta: 
    """

    prompt = PromptTemplate(
        template=qa_template.strip(),
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": settings.RETRIEVAL_K, "fetch_k": 10}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=False
    )