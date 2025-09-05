# app/api/routes.py
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

# Estado global
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
        logger.success("✅ Sistema RAG inicializado!")
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
            yield ' {"type": "error", "content": "Mensagem vazia"}\n\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    rag_chain = get_rag_chain()
    if not rag_chain:
        async def error():
            yield ' {"type": "error", "content": "Sistema RAG não está disponível. Verifique os PDFs e o LLM."}\n\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    msg = body.message.strip().lower().rstrip('?').rstrip('!')
    cumprimentos = ["ola", "olá", "oi", "bom dia", "hello"]

    async def event_stream():
        try:
            yield ' {"type": "start"}\n\n'

            if msg in cumprimentos:
                resposta = "Olá! Como posso ajudar você hoje? 😊"
            else:
                logger.info(f"💬 Pergunta: {body.message}")
                result = rag_chain.invoke({"query": body.message})
                raw = result.get("result", "").strip()

                # Limpeza
                if "Resposta:" in raw:
                    raw = raw.split("Resposta:")[-1].strip()
                linhas = [l for l in raw.split('\n') if not l.startswith(("Okay,", "Parsing"))]
                resposta = '\n'.join(linhas).strip()
                if not resposta:
                    resposta = "Desculpe, não consegui gerar uma resposta."

                logger.info(f"📝 Resposta: {resposta[:100]}...")

            buffer = ""
            for char in resposta:
                buffer += char
                yield f'data: {{"type": "chunk", "content": {json.dumps(buffer)}}}\n\n'
                await asyncio.sleep(0.005)

            yield ' {"type": "complete"}\n\n'

            session_id = request.cookies.get("session_id") or str(uuid.uuid4())
            history = request.session.setdefault("history", {})
            session_hist = history.setdefault(session_id, [])
            session_hist.append({"role": "user", "content": body.message})
            session_hist.append({"role": "ai", "content": resposta})
            history[session_id] = session_hist[-6:]

        except Exception as e:
            logger.error(f"❌ Erro no stream: {e}")
            yield f' {{"type": "error", "content": "Erro: {str(e)}"}}\n\n'

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    response.set_cookie("session_id", str(uuid.uuid4()), httponly=True, samesite="strict")
    return response