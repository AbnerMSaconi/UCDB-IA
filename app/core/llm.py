# app/core/llm.py
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
            
            # Garanta que o LLM está acessível
            try:
                health = requests.get(f"{settings.LLM_BASE_URL}/models", timeout=5)
                if health.status_code != 200:
                    logger.critical("🛑 LLM não está saudável")
                    raise Exception("LLM não respondeu em /models")
            except Exception as e:
                logger.critical(f"🛑 LLM não acessível: {e}")
                raise Exception("LLM não está rodando em http://localhost:8080")

            response = requests.post(
                f"{settings.LLM_BASE_URL}/completions",
                json={
                    "prompt": prompt,
                    "temperature": settings.TEMPERATURE,
                    "max_tokens": settings.MAX_TOKENS,  # 2048
                    "top_p": settings.TOP_P,
                    "repeat_penalty": settings.REPETITION_PENALTY,
                    "stop": stop or ["Pergunta:", "Resposta:", "Okay,"],
                    "stream": False,
                    "top_k": 40,           # Adicione
                    "min_p": 0.05,         # Adicione
                    "typical_p": 1.0,      # Adicione
                    "frequency_penalty": 0.2,
                    "presence_penalty": 0.2
                },
                timeout=1200
            )

            if response.status_code != 200:
                logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                raise Exception(f"Erro HTTP: {response.status_code}")

            data = response.json()
            
            # Verifique se há tokens gerados
            if "choices" not in data or len(data["choices"]) == 0:
                logger.error("❌ Resposta sem 'choices'")
                return "Erro: resposta vazia do LLM"

            text = data["choices"][0]["text"].strip()
            
            if not text:
                logger.warning("⚠️ LLM retornou texto vazio")
                return "Desculpe, o modelo não gerou uma resposta."

            logger.info(f"← Resposta recebida ({len(text)} chars)")
            return text

        except requests.exceptions.ConnectionError:
            logger.critical("🛑 LLM não acessível. Verifique se está rodando em http://localhost:8080")
            raise Exception("LLM não está respondendo")
        except Exception as e:
            logger.error(f"❌ Erro no LLM: {e}")
            raise Exception(f"Erro ao chamar LLM: {str(e)}")

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {"endpoint": settings.LLM_BASE_URL}