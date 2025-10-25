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
import html
from urllib.parse import quote # Importar quote para URLs seguras

router = APIRouter()

# Variáveis globais para RAG
_vectorstore = None
_rag_chain = None
_initialized = False
_initialization_failed = False

# --- Funções Auxiliares ---

def _limpar_resposta_llm(texto: str) -> str:
    """Limpa a resposta do LLM, removendo artefatos e linhas vazias."""
    if not texto: return ""
    texto_limpo = re.sub(r'^[^\w\s]*\s*$', '', texto, flags=re.MULTILINE)
    texto_limpo = re.sub(r'\n{3,}', '\n\n', texto_limpo)
    return texto_limpo.strip()

def _remover_duplicacao(texto: str, logger) -> str:
    """Detecta e remove repetições exatas da resposta."""
    texto = texto.strip()
    tamanho = len(texto)
    if tamanho > 50 and tamanho % 2 == 0:
        meio = tamanho // 2
        primeira_metade = texto[:meio].strip()
        segunda_metade = texto[meio:].strip()
        if primeira_metade == segunda_metade and primeira_metade:
            logger.warning("Resposta duplicada detectada e corrigida.")
            return primeira_metade
    return texto

def _initialize_rag():
    """Inicializa o vectorstore e a RAG chain."""
    global _vectorstore, _rag_chain, _initialized, _initialization_failed
    if _initialized or _initialization_failed: return _initialized
    try:
        from app.core.rag import criar_vectorstore, criar_rag_chain
        logger.info("🚀 Inicializando sistema RAG...")
        _vectorstore = criar_vectorstore()
        if not _vectorstore: logger.warning("⚠️ Nenhum documento RAG encontrado.")
        else:
            _rag_chain = criar_rag_chain(_vectorstore)
            logger.success("✅ Sistema RAG inicializado!")
        _initialized = True
        return True
    except Exception as e:
        logger.critical("❌ Falha crítica ao inicializar RAG: {}", e, exc_info=True)
        _initialization_failed = True
        return False

def get_rag_chain():
    """Retorna a RAG chain inicializada."""
    if not _initialize_rag(): return None
    return _rag_chain

# --- Endpoints da API ---

@router.get("/")
async def index():
    """Serve a página principal (index.html)."""
    # Usa o caminho estático definido nas configurações
    static_file_path = os.path.join(settings.static_path, "index.html")
    if os.path.exists(static_file_path):
        return FileResponse(static_file_path)
    else:
        logger.error(f"Ficheiro index.html não encontrado em: {static_file_path}")
        # Retorna um erro 404 se o ficheiro não existir
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="index.html não encontrado")


@router.get("/knowledge-areas")
async def get_knowledge_areas():
    """Retorna a lista de áreas de conhecimento (títulos dos PDFs)."""
    _initialize_rag()
    manifest_path = os.path.join(settings.vectorstore_path, "manifest.json")
    if not os.path.exists(manifest_path): return {"areas": []}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            return {"areas": sorted(list(set(manifest_data.values())))}
    except Exception as e:
        logger.error("Erro ao ler manifesto: {}", e)
        return {"areas": []}

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Endpoint principal para receber perguntas e enviar respostas via streaming."""
    if not body.message.strip():
        async def empty_error(): yield 'data: {"type": "error", "content": "Mensagem vazia"}\\n\\n'
        return StreamingResponse(empty_error(), media_type="text/event-stream")

    rag_chain = get_rag_chain()
    if not rag_chain:
        async def rag_error(): yield 'data: {"type": "error", "content": "Sistema RAG indisponível."}\\n\\n'
        return StreamingResponse(rag_error(), media_type="text/event-stream")

    async def event_stream():
        """Gera os eventos Server-Sent Events (SSE) para o frontend."""
        def format_sse(data: dict) -> str:
            try:
                payload = json.dumps(data)
                return f"data: {payload}\n\n"
            except TypeError as e:
                logger.error("Erro serialização SSE: {}", e)
                return f"data: {json.dumps({'type': 'error', 'content': 'Erro interno ao formatar resposta.'})}\n\n"

        try:
            # Recupera histórico da sessão
            session_id = request.cookies.get("session_id") or str(uuid.uuid4())
            history = request.session.setdefault("history", {})
            session_hist = history.setdefault(session_id, [])
            chat_history_tuples = []
            for i in range(0, len(session_hist), 2):
                 if i + 1 < len(session_hist) and session_hist[i]["role"] == "user" and session_hist[i+1]["role"] == "ai":
                     # Garante que ambos são strings
                     user_content = str(session_hist[i].get("content", ""))
                     ai_content = str(session_hist[i+1].get("content", ""))
                     chat_history_tuples.append((user_content, ai_content))


            yield format_sse({"type": "start"})
            logger.info(f"💬 Pergunta: '{body.message}'")

            # Invoca a RAG chain
            result = await asyncio.to_thread(
                rag_chain.invoke, {"question": body.message, "chat_history": chat_history_tuples}
            )

            # Processa a resposta
            raw_answer = result.get("answer", "").strip()
            resposta_limpa = _limpar_resposta_llm(raw_answer)
            resposta_sem_duplicacao = _remover_duplicacao(resposta_limpa, logger)
            resposta_final = resposta_sem_duplicacao.replace('\\', '\\\\') # Ajuste LaTeX

            if not resposta_final:
                resposta_final = "Desculpe, não consegui formular uma resposta."
            logger.info(f"📝 Resposta Gerada (início): {resposta_final[:100]}...")

            # Processa os documentos fonte
            source_docs = result.get("source_documents", [])
            fontes_formatadas = []
            source_chunks_content = []

            if source_docs:
                unique_sources = {}
                logger.debug(f"Recuperados {len(source_docs)} trechos.")
                for i, doc in enumerate(source_docs):
                    source_path = doc.metadata.get("source", "Desconhecido")
                    source_name = os.path.basename(source_path)
                    page_meta = doc.metadata.get("page")
                    page_num = (int(page_meta) + 1) if isinstance(page_meta, (int, float, str)) and str(page_meta).isdigit() else "?"

                    if source_name not in unique_sources: unique_sources[source_name] = set()
                    unique_sources[source_name].add(str(page_num))

                    # --- ALTERAÇÃO AQUI: Adiciona URL ---
                    pdf_url = f"/pdfs/{quote(source_name)}" # Cria URL seguro

                    source_chunks_content.append({
                        "id": f"chunk_{i}",
                        "source": f"{source_name} (pág. {page_num})",
                        "content": html.escape(doc.page_content),
                        "url": pdf_url  # Adiciona o URL do PDF
                    })

                fontes_formatadas = [f"{name} (pág. {', '.join(sorted(pages))})" for name, pages in unique_sources.items()]
                logger.debug(f"Fontes formatadas: {fontes_formatadas}")
                logger.debug(f"Enviando {len(source_chunks_content)} trechos com URLs.")

            # Salva histórico
            session_hist.extend([
                {"role": "user", "content": body.message},
                {"role": "ai", "content": resposta_final}
            ])
            history[session_id] = session_hist[-10:]

            # --- Envio dos Eventos SSE com Logging ---
            if source_chunks_content:
                logger.debug("Enviando evento: source_chunks")
                yield format_sse({"type": "source_chunks", "content": source_chunks_content})

            buffer = ""
            logger.debug("Iniciando streaming de 'chunk'")
            for char in resposta_final:
                buffer += char
                yield format_sse({"type": "chunk", "content": buffer})
                await asyncio.sleep(0.005)
            logger.debug("Finalizado streaming de 'chunk'")

            if fontes_formatadas:
                logger.debug("Enviando evento: sources")
                yield format_sse({"type": "sources", "content": fontes_formatadas})

            logger.debug("Enviando evento: complete")
            yield format_sse({"type": "complete"})

        except Exception as e:
            logger.error("❌ Erro no stream: {}", e, exc_info=True)
            yield format_sse({"type": "error", "content": f"Erro no servidor."})

    response = StreamingResponse(event_stream(), media_type="text/event-stream")
    if not request.cookies.get("session_id"):
        response.set_cookie("session_id", str(uuid.uuid4()), httponly=True, samesite="strict", max_age=3600*24*7)
    return response