# UCDB Chat - Sistema de Chat com RAG e Qwen3-14B

> 🚀 Chat inteligente baseado em documentos, usando RAG, FastAPI, llama.cpp e Qwen3-14B.

Este sistema permite fazer perguntas sobre documentos PDFs carregados, com respostas ricas, formatadas em Markdown e geradas em tempo real por um modelo de linguagem local (Qwen3-14B).

---

## 📁 Estrutura do Projeto
---
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
│       ├── logger.py       # Sistema de logging
├── static/                 # Frontend (HTML, CSS, JS)
│   ├── index.html
│   └── assets/
│       ├── css/style.css
│       ├── js/script.js
│       └── lib/marked.min.js
├── pdfs/                   # ← Adicione seus PDFs aqui
├── embeddings/             # ← Gerado automaticamente (FAISS)
├── logs/                   # ← Logs do sistema
├── .env.example
├── .gitignore
├── main.py                 # Ponto de entrada
├── requirements.txt
└── README.md
---

## 🛠️ Requisitos

- Python 3.10+
- Modelo Qwen3-14B (formato `.gguf`)
- `llama-server` (do projeto `llama.cpp`)
- `nomic-embed-text-v1.5` (opcional, para embeddings)

---

## 🔧 Instalação

---
# 1. Clone o repositório
git clone https://github.com/seu-usuario/ucdb-chat.git
cd ucdb-chat

# 2. Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie as pastas necessárias
mkdir pdfs embeddings logs

# 5. Coloque seus PDFs técnicos em /pdfs
# Ex: transistores.pdf, eletronica_basica.pdf

##🚀 Como Executar 
#1. Inicie o LLM (em outro terminal) na porta 8080

#2. Inicie o servidor de embeddings (opcional) na porta 8081

#3. Inicie o UCDB Chat
    python main.py
Acesse: http://localhost:8000 

---
##📚 Documentação dos Módulos
---
##📄 app/core/config.py 

#Função: Define todas as configurações do sistema. 
#Variáveis: 

    APP_NAME: Nome do app
    LLM_BASE_URL: URL do llama-server (http://localhost:8080/v1)
    EMBEDDING_API_URL: URL do servidor de embeddings
    MAX_TOKENS: 2048 (respostas longas)
    TEMPERATURE: 0.8 (criatividade)
    CHUNK_SIZE: 812 (tamanho dos pedaços de texto)
    RETRIEVAL_K: 4 (número de chunks recuperados)
     

#Propriedades: 

    .vectorstore_path: Caminho para embeddings/
    .pdf_path: Caminho para pdfs/
    .static_path: Caminho para static/
     

 
#📄 app/core/embeddings.py 

#Classe: LlamaEmbeddings 

#Gera embeddings usando o llama-server em :8081/embedding. 
#Métodos: 

    embed_documents(texts): Gera embeddings para múltiplos textos
    embed_query(text): Gera embedding para uma consulta
     

 
#📄 app/core/llm.py 

#Classe: LlamaServerLLM 

#Integração com o llama-server em :8080. 
#Métodos: 

    _call(prompt): Envia prompt ao LLM e retorna resposta
    Usa requests para POST em /completions
    Parâmetros: max_tokens, temperature, stop, etc.
     

 
#📄 app/core/rag.py 

#Funções: 
criar_vectorstore() 

    Carrega PDFs com PyPDFLoader
    Divide em chunks com RecursiveCharacterTextSplitter
    Gera embeddings e salva em embeddings/ com FAISS
    Retorna vectorstore (FAISS)
     

criar_rag_chain(vectorstore) 

    Cria RetrievalQA com LangChain
    Usa prompt com {context} e {question}
    Retorna chain pronta para perguntas
     

 
📄 app/api/schemas.py 

Modelo: ChatRequest 

    message: str: Mensagem do usuário
     

Usado para validação de entrada na rota /chat. 
 
📄 app/api/routes.py 

Rotas FastAPI: 
GET / 

    Retorna index.html
     

POST /chat 

    Recebe mensagem do usuário
    Usa RAG para gerar resposta
    Streaming caractere por caractere com SSE
    Formato:  {"type": "chunk", "content": "Olá..."}
     

 
📄 app/utils/logger.py 

Função: setup_logging() 

    Configura loguru com cores e formato
    Intercepta logs do logging padrão
    Níveis: INFO, SUCCESS, WARNING, ERROR, CRITICAL
     

 
📄 app/main.py 

Função: create_app() 

    Cria instância do FastAPI
    Adiciona middlewares (CORS, sessão)
    Monta rotas e arquivos estáticos
    Inicia logger
     

 
📄 main.py 

Ponto de entrada: 

    Importa app de app.main
    Inicia Uvicorn
    Porta: 8000
    Reload: ativado em dev
     

 
🖥️ Frontend (static/) 
index.html 

    Página principal com chat
    Carrega CSS e JS
    Usa EventSource para SSE
     

script.js 

    Streaming de respostas
    Renderiza Markdown com marked.js
    Auto-resize do textarea
    Indicador de digitação
     

style.css 

    Design moderno com gradientes
    Responsivo
    Estilos para código, blocos, etc.
     

 
⚙️ Variáveis de Ambiente (.env.example) 