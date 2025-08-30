# UCDB Chat 🧠💬  
> Sistema de chat inteligente baseado em **RAG (Retrieval-Augmented Generation)**, **FastAPI**, **llama.cpp** e o modelo **Qwen3-14B**.  

Permite fazer perguntas sobre **documentos PDF** carregados, retornando respostas formatadas em **Markdown**, geradas em tempo real por um LLM local.  

---

## 📂 Estrutura do Projeto
```
ucdb-chat/
├── app/
│   ├── core/
│   │   ├── config.py       # Configurações globais
│   │   ├── llm.py          # Integração com llama-server
│   │   ├── embeddings.py   # Geração de embeddings
│   │   └── rag.py          # Sistema RAG com LangChain
│   ├── api/
│   │   ├── routes.py       # Rotas FastAPI
│   │   └── schemas.py      # Modelos Pydantic
│   └── utils/
│       └── logger.py       # Sistema de logging
├── static/                 # Frontend (HTML, CSS, JS)
│   ├── index.html
│   └── assets/
│       ├── css/style.css
│       ├── js/script.js
│       └── lib/marked.min.js
├── pdfs/                   # PDFs adicionados pelo usuário
├── embeddings/             # Vetores gerados automaticamente (FAISS)
├── logs/                   # Arquivos de log
├── .env.example
├── requirements.txt
├── main.py                 # Ponto de entrada
└── README.md
```

---

## ⚙️ Requisitos
- **Python 3.10+**
- Modelo **Qwen3-14B** no formato `.gguf`
- **llama-server** (via [llama.cpp](https://github.com/ggerganov/llama.cpp))
- (Opcional) `nomic-embed-text-v1.5` para embeddings

---

## 🚀 Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/ucdb-chat.git
cd ucdb-chat

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scriptsctivate      # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie as pastas necessárias
mkdir pdfs embeddings logs

# 5. Coloque seus PDFs em /pdfs
```

---

## ▶️ Como Executar

1. **Inicie o LLM** (em outro terminal) na porta **8080**  
2. **Inicie o servidor de embeddings** (opcional) na porta **8081**  
3. **Inicie o UCDB Chat**  

```bash
python main.py
```

Acesse em: **http://localhost:8000**

---

## 📚 Documentação dos Módulos

### 🔧 `app/core/config.py`
- Define as configurações principais:  
  - `APP_NAME`, `LLM_BASE_URL`, `EMBEDDING_API_URL`, `MAX_TOKENS`, `TEMPERATURE`, etc.  
- Caminhos: `vectorstore_path`, `pdf_path`, `static_path`.  

### 🔧 `app/core/embeddings.py`
- Classe `LlamaEmbeddings`  
  - `embed_documents(texts)` → gera embeddings para documentos  
  - `embed_query(text)` → gera embedding para uma consulta  

### 🔧 `app/core/llm.py`
- Classe `LlamaServerLLM`  
  - Integração com `llama-server` em `:8080`  
  - Método `_call(prompt)` envia o prompt e retorna a resposta  

### 🔧 `app/core/rag.py`
- `criar_vectorstore()` → Carrega PDFs, divide em chunks, gera embeddings e armazena no FAISS  
- `criar_rag_chain(vectorstore)` → Cria pipeline RAG com LangChain  

### 🔧 `app/api/schemas.py`
- Modelo `ChatRequest`:  
  ```python
  message: str
  ```

### 🔧 `app/api/routes.py`
- **GET /** → retorna `index.html`  
- **POST /chat** → recebe mensagem e retorna resposta via SSE  

### 🔧 `app/utils/logger.py`
- Configuração avançada de logs com **loguru**  

### 🔧 `app/main.py`
- Criação da instância FastAPI  
- Monta middlewares, rotas e arquivos estáticos  

---

## 💻 Frontend (static/)
- `index.html` → página principal do chat  
- `script.js` → streaming de respostas, markdown renderizado com `marked.js`  
- `style.css` → design responsivo, temas modernos  

---

## 🔑 Variáveis de Ambiente (`.env.example`)
```ini
APP_NAME=UCDB Chat
DEBUG=true
MAX_TOKENS=2048
TEMPERATURE=0.8
```

Renomeie para `.env` antes de usar.  

---

## 🧪 Testes

### Testar RAG isolado
```bash
python -c "
from app.core.rag import criar_vectorstore, criar_rag_chain
vectorstore = criar_vectorstore()
chain = criar_rag_chain(vectorstore)
print(chain({'query': 'O que é um transistor?'}))
"
```

### Testar LLM diretamente
```bash
curl http://localhost:8080/v1/completions   -H "Content-Type: application/json"   -d '{"prompt":"Explique transistores.","max_tokens":512}'
```

---

## 🐛 Solução de Problemas
- **Erro: `BaseSettings` não encontrado** → `pip install pydantic-settings`  
- **RAG não inicializa** → verifique se há PDFs em `/pdfs`  
- **LLM não responde** → teste com `curl http://localhost:8080/v1/models`  
- **Resposta vazia** → aumente `max_tokens` ou ajuste `stop` tokens  
- **Embeddings não gerados** → verifique `EMBEDDING_API_URL`  

---

## 📦 Dependências Principais
- `fastapi`, `uvicorn` → servidor web  
- `langchain`, `langchain-community` → RAG  
- `pydantic-settings` → configurações  
- `pypdf` → leitura de PDFs  
- `loguru` → logging  

---

## 🤝 Contribuição
1. Fork o projeto  
2. Crie sua branch (`git checkout -b feature/nova-funcao`)  
3. Commit suas mudanças (`git commit -m 'Adiciona nova função'`)  
4. Push (`git push origin feature/nova-funcao`)  
5. Abra um Pull Request  

---

## 📄 Licença
MIT  