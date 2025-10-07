-----

# UCDB Chat 🧠💬

Bem-vindo ao UCDB Chat, um assistente de estudos académico inteligente, projetado para responder a perguntas complexas com base num conjunto de documentos PDF fornecidos. Este projeto utiliza uma arquitetura **RAG (Retrieval-Augmented Generation)** para combinar o poder de um Modelo de Linguagem Grande (LLM) local com a informação específica dos seus documentos.

## ✨ Funcionalidades Principais

  * **Arquitetura RAG:** As respostas são baseadas em factos extraídos diretamente dos seus documentos, minimizando alucinações.
  * **LLM Local:** Executa um Modelo de Linguagem Grande (LLM) localmente usando `llama.cpp`, garantindo total privacidade e controlo.
  * **Interface Web Intuitiva:** Um frontend de chat simples e limpo que exibe as respostas em tempo real (*streaming*).
  * **Suporte a Markdown e LaTeX:** As respostas são formatadas com Markdown e suportam fórmulas matemáticas via MathJax.
  * **Identificação de Fontes:** Cada resposta inclui referências aos documentos e páginas de onde a informação foi extraída.
  * **Histórico de Conversa:** O assistente "lembra-se" das perguntas anteriores na mesma sessão para fornecer respostas contextuais.

## ⚙️ Tecnologias Utilizadas

  * **Backend:** FastAPI, Uvicorn, LangChain, Pydantic
  * **Base de Dados Vetorial:** FAISS
  * **Frontend:** HTML5, CSS3, JavaScript (com `marked.js` e `MathJax`)
  * **Servidor de Inferência:** LLaMA.cpp

## 📂 Estrutura do Projeto
\n---\n\n## 📦 Backend\n\n### `main.py` (raiz)\nResponsável por inicializar o servidor FastAPI.\n\n**Funções principais:**\n- Importa `app.main` e executa a aplicação.\n- Configura CORS e rota raiz.\n\n**Exemplo de execução:**\n```bash\npython main.py\n```\n\n---\n\n### `app/main.py`\nArquivo central da aplicação.\n\n**Funções e componentes:**\n- Cria instância do FastAPI.\n- Inclui as rotas definidas em `app/api/routes.py`.\n- Carrega configurações globais (porta, host, etc.).\n- Inicializa logs.\n\n---\n\n### `app/api/routes.py`\nDefine as rotas da API (endpoints) utilizadas pelo frontend.\n\n**Principais rotas:**\n| Método | Rota     | Função              | Descrição                                      |\n|--------|----------|---------------------|------------------------------------------------|\n| GET    | `/`      | `root()`            | Retorna status inicial da API.                 |\n| POST   | `/ask`   | `ask_question()`    | Processa pergunta via RAG e retorna resposta.  |\n| POST   | `/upload`| `upload_pdf()`      | Recebe PDFs e atualiza o índice vetorial.      |\n\n**Fluxo interno:**\n- Recebe JSON do frontend.\n- Chama `rag.query(question)` para gerar resposta.\n- Retorna objeto contendo a resposta e fontes relevantes.\n\n---\n\n### `app/api/schemas.py`\nDefine os modelos de dados utilizados pela API via Pydantic.\n\n**Classes principais:**\n```python\nclass QueryRequest(BaseModel):\n    question: str\n\nclass QueryResponse(BaseModel):\n    answer: str\n    sources: list[str]\n\nclass UploadResponse(BaseModel):\n    message: str\n```\nEsses modelos garantem tipagem forte e validação automática das requisições.\n\n---\n\n### `app/api/models.py`\nEstrutura para futuras expansões de persistência de dados, como:\n- Histórico de conversas\n- Referência de documentos indexados\n- Configurações de sessão\n\n---\n\n### `app/core/config.py`\nGerencia todas as configurações globais do sistema.\n\n**Principais parâmetros:**\n- `TEMPERATURE`: controle da criatividade do modelo\n- `RETRIEVAL_K`: quantidade de trechos recuperados\n- `EMBEDDING_URL`: endereço do servidor de embeddings\n- `LLM_URL`: endereço do modelo LLaMA local\n- `LOG_DIR`: diretório de logs\n\nAs variáveis são carregadas via `.env` ou valores padrão.\n\n---\n\n### `app/core/embeddings.py`\nImplementa a geração e o gerenciamento de embeddings para os documentos.\n\n**Funções principais:**\n```python\ndef embed_text(text: str) -> np.ndarray:\n    """\n    Envia o texto para o servidor de embeddings e retorna o vetor gerado.\n    """\n\ndef index_documents(pdf_folder: str):\n    """\n    Extrai texto dos PDFs, cria embeddings e salva na base FAISS.\n    """\n\ndef retrieve_similar(query_vector, k=5):\n    """\n    Busca os vetores mais próximos no índice FAISS com base na consulta.\n    """\n```\n**Fluxo:**\n- Extrai texto dos PDFs\n- Divide em chunks\n- Cria embeddings via servidor local\n- Salva os vetores em FAISS (`.index`)\n- Usa busca vetorial durante a consulta\n\n---\n\n### `app/core/llm.py`\nGerencia a comunicação com o modelo de linguagem LLaMA via servidor REST local.\n\n**Função principal:**\n```python\ndef generate(prompt: str) -> str:\n    """\n    Envia prompt ao servidor LLaMA e retorna a resposta gerada.\n    """\n```\n**Mecanismos de controle:**\n- `temperature`\n- `top_p`\n- `max_tokens`\n- `repetition_penalty`\n\n---\n\n### `app/core/rag.py`\nNúcleo do sistema RAG (Retrieval-Augmented Generation).\n\n**Função principal:**\n```python\ndef query(question: str) -> dict:\n    """\n    Executa o pipeline completo:\n    1. Gera embedding da pergunta.\n    2. Busca trechos relevantes na base FAISS.\n    3. Constrói prompt contextualizado.\n    4. Chama o modelo LLaMA.\n    5. Retorna a resposta e fontes.\n    """\n```\n**Estrutura:**\n- Combina módulos `embeddings.py` e `llm.py`\n- Usa logs e streaming\n- Garante contexto atualizado conforme PDFs enviados\n\n---\n\n### `app/utils/logger.py`\nGerencia o sistema de logs do projeto.\n\n```python\ndef get_logger(name):\n    """\n    Retorna um logger configurado para o módulo solicitado.\n    """\n```\nCada módulo cria seu próprio logger, salvando registros no diretório `logs/` com timestamp.\n\n---\n\n### `app/utils/streaming.py`\nResponsável pelo streaming de respostas (envio em tempo real ao frontend).\n\nPermite que a resposta do LLaMA seja exibida enquanto é gerada, simulando comportamento de chat contínuo.\n\n---\n\n## 💻 Frontend\n\nLocalizado em `static/`.\n\n### `index.html`\nEstrutura da interface principal do chat.\n\n**Elementos principais:**\n- Caixa de chat com mensagens do usuário e da IA\n- Campo de texto e botão “Enviar”\n- Componente para upload de PDFs\n- Conecta-se à API via JavaScript (`fetch`)\n\n---\n\n### `assets/css/style.css`\nDefine o estilo da interface:\n- Layout responsivo\n- Cores neutras (tema acadêmico)\n- Estilo de bolhas de chat\n- Animações leves de digitação\n\n---\n\n### `assets/js/script.js`\nGerencia toda a lógica de interação do frontend.\n\n**Funções principais:**\n```javascript\nasync function sendMessage() {\n  // Lê a mensagem do usuário\n  // Exibe no chat\n  // Envia via POST /ask\n  // Exibe a resposta retornada pela API\n}\n\nasync function uploadPDF(file) {\n  // Envia arquivo para /upload\n  // Atualiza índice FAISS no servidor\n}\n```\n**Outros comportamentos:**\n- Scroll automático do chat\n- Exibição de mensagens do sistema\n- Renderização de Markdown e LaTeX\n

```
ucdb-ia/
├── app/
│   ├── api/
│   │   ├── routes.py       # Endpoints da API (FastAPI)
│   │   └── schemas.py      # Modelos de dados (Pydantic)
│   ├── core/
│   │   ├── config.py       # Configurações globais da aplicação
│   │   ├── embeddings.py   # Integração com o modelo de embedding
│   │   ├── llm.py          # Integração com o servidor do LLM
│   │   └── rag.py          # Lógica principal do RAG
│   └── utils/
│       └── logger.py       # Configuração do sistema de logs
├── embeddings/             # (Gerado automaticamente) Base de dados vetorial FAISS
├── logs/                   # (Gerado automaticamente) Ficheiros de log
├── pdfs/                   # Coloque os seus PDFs aqui
├── static/                 # Ficheiros do frontend
│   ├── assets/
│   │   ├── css/style.css
│   │   └── js/script.js
│   └── index.html
├── .env.example            # Exemplo de ficheiro de configuração
├── main.py                 # Ponto de entrada para iniciar o servidor web
└── requirements.txt        # Dependências Python
```

-----

## 🚀 Tutorial de Instalação e Execução

Siga estes passos para configurar e executar o projeto localmente.

### Pré-requisitos

Antes de começar, garanta que tem o seguinte software instalado:

1.  **Python 3.10+**
2.  **LLaMA.cpp:** Siga o [guia oficial](https://github.com/ggerganov/llama.cpp) para compilar o projeto. O essencial é ter o executável `server` pronto a usar.

### Passo 1: Configuração do Projeto

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/ucdb-ia.git
    cd ucdb-ia
    ```

2.  **Crie e ative um ambiente virtual:**

    ```bash
    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Instale as dependências Python:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Crie as pastas necessárias:**

    ```bash
    mkdir pdfs
    ```

    *As pastas `embeddings` e `logs` serão criadas automaticamente na primeira execução.*

5.  **Adicione os seus documentos:**
    Coloque todos os ficheiros `.pdf` que servirão como base de conhecimento dentro da pasta `pdfs/`.

6.  **Configure as variáveis de ambiente:**
    Copie o ficheiro de exemplo e renomeie-o para `.env`.

    ```bash
    cp .env.example .env
    ```

    *Não são necessárias alterações no ficheiro `.env` se você seguir os comandos abaixo.*

### Passo 2: Execução dos Servidores

Para que o chat funcione, precisamos de três componentes a serem executados em **três terminais separados**.

#### Terminal 1: Servidor de Embedding

Este servidor é responsável por converter texto em vetores numéricos.

```bash
# Inicie o servidor de embedding na porta 8081
# (substitua pelo nome do seu modelo de embedding, se for diferente)
llama-server -m seu-modelo-de-embedding.gguf -e -ngl 100 --port 8081
```

#### Terminal 2: Servidor do LLM (O Cérebro)

Este é o modelo principal que irá gerar as respostas. Recomenda-se o **Llama-3-8B** para um bom equilíbrio entre performance e qualidade no seu hardware.

```bash
# Inicie o servidor do LLM na porta 8080
# Substitua pelo caminho do seu modelo .gguf
llama-server -m ./Meta-Llama-3-8B-Instruct.Q4_K_M.gguf -c 8192 -ngl 100 --flash-attn
```

  * `-c 8192`: Define o tamanho do contexto para 8192 tokens, permitindo respostas mais longas.
  * `-ngl 100`: Descarrega o máximo de camadas para a GPU, garantindo a máxima velocidade.

#### Terminal 3: Aplicação UCDB Chat

Este é o servidor web da aplicação.

```bash
# Certifique-se de que o seu ambiente virtual (venv) está ativo
python main.py
```

### Passo 3: Aceder à Aplicação

Após iniciar os três servidores, abra o seu navegador e aceda a:

**http://localhost:8000**

Na primeira execução, o sistema irá processar e indexar todos os PDFs. Este processo pode demorar alguns minutos, dependendo do número de documentos. Você pode acompanhar o progresso nos logs do terminal onde a aplicação Python está a ser executada. Após a conclusão, o chat estará pronto a ser usado\!

-----

## 🔧 Configuração Avançada

Pode ajustar o comportamento do LLM editando o ficheiro `app/core/config.py`.

  * `REPETITION_PENALTY`: Aumente este valor (ex: `1.2`) se notar que o modelo está a repetir-se.
  * `TEMPERATURE`: Aumente para respostas mais criativas, diminua (ex: `0.5`) para respostas mais factuais e diretas.
  * `RETRIEVAL_K`: O número de *chunks* de texto a serem recuperados dos documentos para cada pergunta. Um valor entre 4 e 6 é geralmente ideal.

## 🤝 Contribuição

Contribuições são bem-vindas\! Se encontrar um bug ou tiver uma sugestão, por favor, abra uma *issue* no repositório.

## 📄 Licença

Este projeto está licenciado sob a **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

![CC BY-NC 4.0](https://i.creativecommons.org/l/by-nc/4.0/88x31.png)

Isto significa que você é livre para partilhar e adaptar este trabalho para **fins não comerciais**, desde que dê o crédito apropriado aos criadores originais.

**Uso Comercial:**
O uso deste software em projetos ou produtos comerciais é estritamente proibido sob esta licença. Para obter uma licença comercial, por favor, entre em contacto com a equipa de desenvolvimento.
