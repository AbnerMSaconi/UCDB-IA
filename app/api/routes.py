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
            yield 'data: {"type": "error", "content": "Mensagem vazia"}\n\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    rag_chain = get_rag_chain()
    if not rag_chain:
        async def error():
            yield 'data: {"type": "error", "content": "Sistema RAG não está disponível. Verifique os PDFs e o LLM."}\n\n'
        return StreamingResponse(error(), media_type="text/event-stream")

    msg = body.message.strip().lower().rstrip('?').rstrip('!')
    cumprimentos = ["ola", "olá", "oi", "bom dia", "hello"]

    async def event_stream():
        try:
            yield 'data: {"type": "start"}\n\n'
            resposta_final = ""
            fontes = []

            if msg in cumprimentos:
                resposta_final = "Olá! Como posso ajudar você hoje? 😊"
            else:
                logger.info(f"💬 Pergunta: {body.message}")
                result = await asyncio.to_thread(rag_chain.invoke, {"query": body.message})
                
                logger.debug(f"Resultado completo do RAG: {result}")

                raw = result.get("result", "").strip()

                # Limpeza - LINHAS CORRIGIDAS AQUI
                if "Resposta:" in raw:
                    raw = raw.split("Resposta:")[-1].strip()
                linhas = [l for l in raw.split('\n') if not l.startswith(("Okay,", "Parsing"))]
                resposta_final = '\n'.join(linhas).strip()
                if not resposta_final:
                    resposta_final = "Desculpe, não consegui gerar uma resposta."

                logger.info(f"📝 Resposta: {resposta_final[:100]}...")

                # Extrair fontes
                source_docs = result.get("source_documents", [])
                if source_docs:
                    logger.info(f"📚 Encontradas {len(source_docs)} fontes.")
                    unique_sources = {}
                    for doc in source_docs:
                        source_name = os.path.basename(doc.metadata.get("source", "Desconhecido"))
                        page_num = doc.metadata.get("page", "?")
                        if source_name not in unique_sources:
                            unique_sources[source_name] = set()
                        unique_sources[source_name].add(str(page_num + 1))
                    
                    fontes = [f"{name} (pág. {', '.join(sorted(pages))})" for name, pages in unique_sources.items()]
                    logger.debug(f"Fontes formatadas para enviar: {fontes}")


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

    return StreamingResponse(event_stream(), media_type="text/event-stream")