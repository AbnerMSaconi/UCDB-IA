# app/api/routes.py - Versão com Correção Automática de LaTeX

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, FileResponse
from app.api.schemas import ChatRequest
from app.core.config import settings
from app.utils.logger import logger
import os
import json
import uuid
import asyncio
import re

router = APIRouter()

_vectorstore = None
_rag_chain = None
_initialized = False
_initialization_failed = False

def _limpar_resposta_llm(texto: str) -> str:
    if not texto: return ""
    texto_limpo = re.sub(r'^[^\w\s]*\s*$', '', texto, flags=re.MULTILINE)
    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
    return texto_limpo.strip()

def _remover_duplicacao(texto: str, logger) -> str:
    texto = texto.strip()
    tamanho = len(texto)
    if tamanho > 50 and tamanho % 2 == 0:
        meio = tamanho // 2
        primeira_metade = texto[:meio].strip()
        segunda_metade = texto[meio:].strip()
        if primeira_metade == segunda_metade and primeira_metade:
            logger.warning("Resposta duplicada foi detectada e corrigida.")
            return primeira_metade
    return texto

def _initialize_rag():
    global _vectorstore, _rag_chain, _initialized, _initialization_failed
    if _initialized or _initialization_failed:
        return _initialized
    try:
        from app.core.rag import criar_vectorstore, criar_rag_chain
        logger.info("🚀 Inicializando sistema RAG...")
        _vectorstore = criar_vectorstore()
        if not _vectorstore:
            logger.warning("⚠️ Nenhum documento encontrado para o RAG.")
        else:
            _rag_chain = criar_rag_chain(_vectorstore)
            logger.success("✅ Sistema RAG conversacional inicializado!")
        _initialized = True
        return True
    except Exception as e:
        logger.critical("❌ Falha crítica ao inicializar RAG: {}", e, exc_info=True)
        _initialization_failed = True
        return False

def get_rag_chain():
    if not _initialize_rag():
        return None
    return _rag_chain

@router.get("/")
async def index():
    return FileResponse(os.path.join(settings.static_path, "index.html"))

@router.get("/knowledge-areas")
async def get_knowledge_areas():
    _initialize_rag()
    manifest_path = os.path.join(settings.vectorstore_path, "manifest.json")
    if not os.path.exists(manifest_path): return {"areas": []}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            return {"areas": sorted(list(set(manifest_data.values())))}
    except Exception:
        return {"areas": []}

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    if not body.message.strip():
        async def error(): yield 'data: {"type": "error", "content": "Mensagem vazia"}\\n\\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    rag_chain = get_rag_chain()
    if not rag_chain:
        async def error(): yield 'data: {"type": "error", "content": "Sistema RAG não disponível."}\\n\\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    async def event_stream():
        try:
            session_id = request.cookies.get("session_id") or str(uuid.uuid4())
            history = request.session.setdefault("history", {})
            session_hist = history.setdefault(session_id, [])
            chat_history_tuples = []
            for i in range(0, len(session_hist), 2):
                if i + 1 < len(session_hist) and session_hist[i]["role"] == "user" and session_hist[i+1]["role"] == "ai":
                    chat_history_tuples.append((session_hist[i]["content"], session_hist[i+1]["content"]))

            def format_sse(data: dict) -> str:
                return f"data: {json.dumps(data)}\n\n"

            yield format_sse({"type": "start"})
            
            logger.info(f"💬 Pergunta: '{body.message}'")
            result = await asyncio.to_thread(
                rag_chain.invoke, {"question": body.message, "chat_history": chat_history_tuples}
            )

            raw_answer = result.get("answer", "").strip()
            resposta_limpa = _limpar_resposta_llm(raw_answer)
            resposta_sem_duplicacao = _remover_duplicacao(resposta_limpa, logger)
            
            # --- CORREÇÃO AUTOMÁTICA DE LATEX ADICIONADA AQUI ---
            resposta_final = resposta_sem_duplicacao.replace('\\', '\\\\')

            if not resposta_final:
                resposta_final = "Desculpe, o modelo não conseguiu formular uma resposta."
            
            logger.info(f"📝 Resposta Final: {resposta_final[:100]}...")

            source_docs = result.get("source_documents", [])
            fontes = []
            if source_docs:
                unique_sources = {}
                for doc in source_docs:
                    source_name = os.path.basename(doc.metadata.get("source", "Desconhecido"))
                    page_num = doc.metadata.get("page", "?")
                    if source_name not in unique_sources: unique_sources[source_name] = set()
                    unique_sources[source_name].add(str(page_num + 1))
                fontes = [f"{name} (pág. {', '.join(sorted(pages))})" for name, pages in unique_sources.items()]

            session_hist.extend([
                {"role": "user", "content": body.message},
                {"role": "ai", "content": resposta_final}
            ])
            history[session_id] = session_hist[-10:]

            buffer = ""
            for char in resposta_final:
                buffer += char
                yield format_sse({"type": "chunk", "content": buffer})
                await asyncio.sleep(0.005)

            if fontes:
                yield format_sse({"type": "sources", "content": fontes})
            
            yield format_sse({"type": "complete"})
        
        except Exception as e:
            logger.error("❌ Erro no stream: {}", e, exc_info=True)
            yield format_sse({"type": "error", "content": f"Ocorreu um erro no servidor: {str(e)}"})

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", str(uuid.uuid4()), httponly=True, samesite="strict")
    return response