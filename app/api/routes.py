# app/api/routes.py - Versão com Gestão de Histórico de Conversa

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from app.api.schemas import ChatRequest
from app.core.config import settings
from app.utils.logger import logger
import os
import json
import uuid
import asyncio

router = APIRouter()

# O estado global e a inicialização do RAG permanecem os mesmos
_vectorstore = None
_rag_chain = None
_initialized = False
_initialization_failed = False

def _initialize_rag():
    global _vectorstore, _rag_chain, _initialized, _initialization_failed
    if _initialized or _initialization_failed:
        return _initialized

    try:
        from app.core.rag import criar_vectorstore, criar_rag_chain
        logger.info("🚀 Inicializando sistema RAG...")

        _vectorstore = criar_vectorstore()
  
        if not _vectorstore:
            logger.warning("⚠️ Nenhum documento encontrado")
            _initialization_failed = True
            return False

        _rag_chain = criar_rag_chain(_vectorstore)
        logger.success("✅ Sistema RAG conversacional inicializado!")
        _initialized = True
        return True

    except Exception as e:
   
        logger.critical(f"❌ Falha ao inicializar RAG: {e}")
        _initialization_failed = True
        return False

def get_rag_chain():
    if not _initialize_rag():
        return None
    return _rag_chain

@router.get("/")
async def index():
    return FileResponse(os.path.join(settings.static_path, "index.html"))

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    if not body.message.strip():
        async def error():
            yield 'data: {"type": "error", "content": "Mensagem vazia"}\n\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    rag_chain = get_rag_chain()
    if not rag_chain:
        async def error():
            yield 'data: {"type": "error", "content": "Sistema RAG não está disponível. Verifique os PDFs e o LLM."}\n\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    async def event_stream():
        try:
            # Recupera o histórico da sessão
            session_id = request.cookies.get("session_id") or str(uuid.uuid4())
            history = request.session.setdefault("history", {})
            session_hist = history.setdefault(session_id, [])

            # Converte o histórico para o formato esperado pela LangChain: [(human_msg, ai_msg), ...]
            chat_history_tuples = []
            for i in range(0, len(session_hist), 2):
                if i + 1 < len(session_hist) and session_hist[i]["role"] == "user" and session_hist[i+1]["role"] == "ai":
                    chat_history_tuples.append(
                        (session_hist[i]["content"], session_hist[i+1]["content"])
                    )

            yield 'data: {"type": "start"}\n\n'
            resposta_final = ""
            fontes = []
            
            logger.info(f"💬 Pergunta: '{body.message}' com histórico de {len(chat_history_tuples)} turnos.")
            
            # A chamada para a cadeia agora inclui 'question' e 'chat_history'
            result = await asyncio.to_thread(
                rag_chain.invoke, 
                {"question": body.message, "chat_history": chat_history_tuples}
            )
            
            # A chave da resposta da ConversationalRetrievalChain é 'answer'
            raw = result.get("answer", "").strip()

            if "<<EOT>>" in raw:
                raw = raw.split("<<EOT>>")[0].strip()

            resposta_final = raw if raw else "Desculpe, não consegui gerar uma resposta."
            logger.info(f"📝 Resposta Limpa: {resposta_final[:100]}...")

            # Lógica para extrair fontes (permanece igual)
            source_docs = result.get("source_documents", [])
            if source_docs:
                unique_sources = {}
                for doc in source_docs:
                    source_name = os.path.basename(doc.metadata.get("source", "Desconhecido"))
                    page_num = doc.metadata.get("page", "?")
                    if source_name not in unique_sources:
                        unique_sources[source_name] = set()
                    unique_sources[source_name].add(str(page_num + 1))
                fontes = [f"{name} (pág. {', '.join(sorted(pages))})" for name, pages in unique_sources.items()]
                logger.debug(f"Fontes formatadas para enviar: {fontes}")

            # Salva o turno atual no histórico da sessão
            session_hist.append({"role": "user", "content": body.message})
            session_hist.append({"role": "ai", "content": resposta_final})
            history[session_id] = session_hist[-10:] # Aumentado para 5 turnos de conversa

            # Streaming da resposta para o frontend (permanece igual)
            buffer = ""
            for char in resposta_final:
                buffer += char
                yield f'data: {json.dumps({"type": "chunk", "content": buffer})}\n\n'
                await asyncio.sleep(0.005)

            if fontes:
                yield f'data: {json.dumps({"type": "sources", "content": fontes})}\n\n'

            yield 'data: {"type": "complete"}\n\n'

        except Exception as e:
            logger.error(f"❌ Erro no stream: {e}", exc_info=True)
            yield f'data: {json.dumps({"type": "error", "content": f"Ocorreu um erro no servidor: {str(e)}"})}\n\n'

    # A gestão de cookies permanece a mesma
    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", str(uuid.uuid4()), httponly=True, samesite="strict")
    return response