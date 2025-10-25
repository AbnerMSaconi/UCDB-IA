from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # Importar StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.api.routes import router
from app.utils.logger import setup_logging, logger
from app.core.config import settings # Importar settings para obter o caminho
import os # Importar os

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="UCDB Chat")

    # Usar SECRET_KEY da configuração para o SessionMiddleware
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
    app.add_middleware(
        CORSMiddleware,
        # Ajuste as origens permitidas conforme necessário para produção
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Monta as rotas da API definidas em app/api/routes.py
    app.include_router(router)

    # Monta a pasta 'static' para servir CSS, JS, HTML
    static_dir = settings.static_path
    os.makedirs(static_dir, exist_ok=True) # Garante que a pasta existe
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # --- NOVA LINHA: Monta a pasta 'pdfs' ---
    # Garante que a pasta pdfs existe antes de tentar montá-la
    pdf_dir = settings.pdf_path
    os.makedirs(pdf_dir, exist_ok=True)
    app.mount("/pdfs", StaticFiles(directory=pdf_dir), name="pdfs")

    @app.on_event("startup")
    def startup():
        """Função executada no início da aplicação."""
        logger.info("🌐 UCDB Chat iniciado!")
        # Tenta inicializar o RAG no startup para acelerar a primeira resposta
        try:
            from app.api.routes import _initialize_rag
            _initialize_rag()
        except Exception as e:
            logger.warning(f"⚠️ Falha na pré-inicialização do RAG no startup: {e}")
        # Tenta obter a porta das settings, caso contrário usa 8000
        # Assume que uvicorn será executado externamente ou via __main__
        logger.info(f"💡 Servidor Uvicorn provavelmente rodando em http://localhost:8000 (verifique o comando de execução)")


    return app

# Cria a instância da aplicação
app = create_app()

# Adiciona um ponto de entrada para uvicorn se executar este ficheiro diretamente
# Útil para debug simples, mas o comando `uvicorn main:app --reload` é preferível
if __name__ == "__main__":
    import uvicorn
    logger.warning("Executando uvicorn diretamente de app/main.py. Use 'python main.py' na raiz para hot-reload.")
    # Tenta obter a porta das settings, caso contrário usa 8000
    config_port = 8000 # Valor padrão
    try:
        # Pydantic v2 usa model_config, v1 usava Config
        if hasattr(settings, 'model_config') and isinstance(settings.model_config, dict):
             port = int(settings.model_config.get('PORT', 8000))
        else:
             port = 8000 # Fallback se não encontrar
    except Exception:
        port = 8000

    config_host = "0.0.0.0"
    try:
         if hasattr(settings, 'model_config') and isinstance(settings.model_config, dict):
             host = settings.model_config.get('HOST', "0.0.0.0")
         else:
             host = "0.0.0.0"
    except Exception:
        host = "0.0.0.0"

    uvicorn.run(app, host=host, port=port)