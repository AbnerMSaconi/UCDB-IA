# app/core/llm.py - Versão com Stop Tokens Otimizados para Llama 3

from langchain_core.language_models.llms import LLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from typing import Any, List, Optional
import requests
from app.utils.logger import logger
from app.core.config import settings

class LlamaServerLLM(LLM):
    @property
    def _llm_type(self) -> str:
        return "llama_server"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
 
        try:
            logger.info(f"→ Enviando prompt ({len(prompt)} chars)")
            
            # --- LISTA DE STOP TOKENS CORRIGIDA E OTIMIZADA PARA LLAMA 3 ---
            stop_tokens = stop or [
                "<|eot_id|>",
                "<|end_of_text|>",
                "<|start_header_id|>"
            ]

            response = requests.post(
                f"{settings.LLM_BASE_URL}/completions",
                json={
                    "prompt": prompt,
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS,
                    "top_p": settings.TOP_P,
                    "repeat_penalty": settings.REPETITION_PENALTY,
                    "stop": stop_tokens,
                    "stream": False,
                },
                timeout=120
            )

            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["text"].strip()
            
            if not text:
                logger.warning("⚠️ LLM retornou texto vazio")
                # Retornamos uma string vazia para a API tratar a mensagem de erro padrão
                return ""

            logger.info(f"← Resposta recebida ({len(text)} chars)")
            return text

        except requests.exceptions.RequestException as e:
            logger.critical(f"🛑 LLM não acessível em {settings.LLM_BASE_URL}. Erro: {e}")
            raise Exception("LLM não está respondendo. Verifique se o servidor llama.cpp está em execução.")
        except Exception as e:
            logger.error(f"❌ Erro na chamada ao LLM: {e}")
            raise

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"endpoint": settings.LLM_BASE_URL}