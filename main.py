# main.py
import uvicorn
from app.main import app
from app.utils.logger import logger

if __name__ == "__main__":
    logger.info("🚀 Iniciando servidor UCDB Chat")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)