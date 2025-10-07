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


### Diretório `app/` - O Coração da Aplicação

#### `app/main.py`
Este ficheiro é responsável por criar e configurar a instância principal da aplicação FastAPI.

`create_app() -> FastAPI:`
- Responsabilidade: Inicializa a aplicação.
- Ações:
  - Chama `setup_logging()` para configurar o sistema de logs.
  - Cria a instância do FastAPI.
  - Adiciona `SessionMiddleware` para gerir sessões de utilizador e o histórico de conversas.
  - Adiciona `CORSMiddleware` para permitir que o frontend (a correr em `localhost:8000`) se comunique com o backend.
  - Inclui as rotas definidas em `app.api.routes`.
  - Configura o diretório `static/` para servir os ficheiros do frontend (HTML, CSS, JS).

`startup()`:
- Responsabilidade: Executa uma ação quando a aplicação arranca.
- Ações: Regista uma mensagem informativa no log a indicar que o servidor foi iniciado.

#### `app/core/config.py`
Este ficheiro centraliza todas as configurações da aplicação usando a biblioteca Pydantic.

`class Settings(BaseSettings):`
- Responsabilidade: Define e carrega todas as variáveis de configuração a partir de um ficheiro `.env` ou de valores padrão.
- Parâmetros Principais:
  - `LLM_BASE_URL`: O endereço do servidor `llama-server`.
  - `MAX_TOKENS`: O número máximo de tokens que o LLM pode gerar numa única resposta.
  - `TEMPERATURE`, `TOP_P`, `REPETITION_PENALTY`: Parâmetros que controlam a criatividade, diversidade e o nível de repetição das respostas do LLM.
  - `CHUNK_SIZE`, `CHUNK_OVERLAP`: Define o tamanho dos pedaços de texto e a sobreposição entre eles durante a indexação dos PDFs.
- Propriedades (`@property`):
  - `vectorstore_path`, `pdf_path`, `static_path`: Funções que geram os caminhos absolutos para os diretórios importantes, garantindo que as pastas são criadas se não existirem.

#### `app/core/llm.py`
Este ficheiro contém a classe que se integra com o servidor `llama.cpp`.

`class LlamaServerLLM(LLM):`
- Responsabilidade: Implementa a interface da LangChain para um LLM, permitindo que a nossa aplicação se comunique com o `llama-server`.

`_call(...) -> str:`
- Ações:
  - Define a lista de `stop_tokens`, que são palavras ou símbolos que indicam ao LLM para parar de gerar texto.
  - Envia um pedido POST para o endpoint `/completions` do `llama-server`, contendo o prompt e todos os parâmetros de geração definidos no `config.py`.
  - Processa a resposta JSON, extrai o texto gerado e retorna-o.

#### `app/core/embeddings.py`
Semelhante ao `llm.py`, este ficheiro integra-se com o servidor `llama.cpp` para gerar embeddings.

`class LlamaEmbeddings(Embeddings):`
- Responsabilidade: Implementa a interface da LangChain para um modelo de embedding.
- `embed_documents(...)`: Recebe uma lista de textos e faz um pedido ao servidor de embeddings para converter cada texto num vetor.
- `embed_query(...)`: Recebe uma única string (a pergunta do utilizador) e converte-a num vetor.

#### `app/core/rag.py`
Este é o ficheiro mais importante, onde toda a lógica do RAG é implementada.

`_gerar_titulo_para_documento(...)`:
- Responsabilidade: Usa o LLM para ler o início de um novo PDF e gerar um título descritivo que represente a sua área de conhecimento.

`_carregar_manifesto(...)` e `_salvar_manifesto(...)`:
- Responsabilidade: Funções auxiliares para ler e escrever no ficheiro `manifest.json`, que armazena a relação entre os nomes dos ficheiros PDF e os seus títulos gerados.

`_processar_novos_pdfs(...)`:
- Responsabilidade: Carrega novos PDFs, gera os seus títulos e divide o seu conteúdo em chunks.

`criar_vectorstore()`:
- Responsabilidade: Orquestra a criação ou atualização da base de dados vetorial FAISS.
- Ações:
  - Verifica se existem novos PDFs na pasta `/pdfs` que ainda não foram processados.
  - Se a base de dados já existe, carrega-a e adiciona apenas os novos documentos.
  - Se não existe, processa todos os PDFs, gera os seus embeddings e salva a nova base de dados na pasta `/embeddings`.

`criar_rag_chain(...)`:
- Responsabilidade: Cria e configura o `ConversationalRetrievalChain` da LangChain.
- Ações:
  - Define o `qa_template`, que é o prompt detalhado com todas as instruções para o LLM.
  - Instancia o `LlamaServerLLM`.
  - Configura o retriever para usar a base de dados FAISS.
  - Monta e retorna a chain completa, pronta a ser usada.

#### `app/api/routes.py`
Define os endpoints da API que o frontend utiliza.

`_initialize_rag()`:
- Responsabilidade: Função de inicialização que garante que o sistema RAG (a base de dados vetorial e a chain) é carregado apenas uma vez quando a aplicação arranca.

`@router.get("/")`:
- Responsabilidade: Serve a página principal da aplicação (`index.html`).

`@router.get("/knowledge-areas")`:
- Responsabilidade: Fornece ao frontend a lista de áreas de conhecimento (os títulos dos PDFs processados) a partir do ficheiro `manifest.json`.

`@router.post("/chat")`:
- Responsabilidade: É o endpoint principal que lida com a conversa do chat.
- Ações:
  - Recebe a mensagem do utilizador.
  - Recupera o histórico da conversa da sessão do utilizador.
  - Chama a `rag_chain` com a pergunta e o histórico.
  - Aplica funções de limpeza (`_limpar_resposta_llm`, `_remover_duplicacao`) para corrigir possíveis erros na resposta do LLM.
  - Envia a resposta final e as fontes para o frontend através de `StreamingResponse`.

#### `app/utils/logger.py`
Configura um sistema de logging robusto com a biblioteca Loguru.

`setup_logging()`:
- Responsabilidade: Define o formato, o nível (DEBUG, INFO, ERROR) e o destino dos logs (a consola e ficheiros no diretório `logs/`).

### Diretório `static/` - A Interface do Utilizador

`index.html`: A estrutura base da página do chat, que inclui a área de mensagens e o campo de introdução de texto.

`assets/css/style.css`: Contém todo o estilo visual da aplicação, definindo as cores, fontes e o layout dos elementos.

`assets/js/script.js`: Contém toda a lógica do frontend.
- `showWelcomeMessage()`: Ao carregar a página, faz um pedido ao endpoint `/knowledge-areas` e exibe a mensagem de boas-vindas com a lista de tópicos.
- `handleSendMessage()`: É chamada quando o utilizador clica em "Enviar". Envia a pergunta para o endpoint `/chat` e processa a resposta em stream, atualizando a interface à medida que o texto chega.
- Utiliza a biblioteca `marked.js` para converter o Markdown recebido do backend em HTML e o `MathJax` para renderizar fórmulas matemáticas.


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
llama-server -m seu-modelo-de-embedding.gguf --embeddings -ngl 100 --port 8081
# Caso queira reservar VRAM 
llama-server -m seu-modelo-de-embedding.gguf --embeddings -ngl 0 --port 8081
# Não é necessário processar os PDFs instantâneamente.
```

#### Terminal 2: Servidor do LLM (O Cérebro)

Este é o modelo principal que irá gerar as respostas. Recomenda-se o **Llama-3-8B** para um bom equilíbrio entre performance e qualidade no seu hardware.

```bash
# Inicie o servidor do LLM na porta 8080
# Substitua pelo caminho do seu modelo .gguf
llama-server -m ./Meta-Llama-3-8B-Instruct.Q4_K_M.gguf -c 8192 -ngl 100 -fa 1
```

  * `-c 8192`: Define o tamanho do contexto para 8192 tokens, permitindo respostas mais longas.
  * `-ngl 100`: Descarrega o máximo de camadas para a GPU, garantindo a máxima velocidade.
  * `-fa 1`: FlashAttention, otimização que visa acelerar o processo de inferência e reduzir o consumo de memória da GPU, especialmente com sequências de texto longas.

#### Terminal 3: Aplicação UCDB Chat

Este é o servidor web da aplicação.

```bash
# Certifique-se de que o seu ambiente virtual (venv) está ativo
python main.py
```

### Passo 3: Aceder à Aplicação

Após iniciar os três servidores, abra o seu navegador e aceda a:

**http://localhost:8000**

Na primeira execução, o sistema irá processar e indexar todos os PDFs. Este processo pode demorar alguns minutos, dependendo do número de documentos. Você pode acompanhar o progresso nos logs do terminal onde a aplicação Python está a ser executada. Após a conclusão, o chat estará pronto a ser usado!

-----

## 🔧 Configuração Avançada

Pode ajustar o comportamento do LLM editando o ficheiro `app/core/config.py`.

  * `REPETITION_PENALTY`: Aumente este valor (ex: `1.2`) se notar que o modelo está a repetir-se.
  * `TEMPERATURE`: Aumente para respostas mais criativas, diminua (ex: `0.5`) para respostas mais factuais e diretas.
  * `RETRIEVAL_K`: O número de *chunks* de texto a serem recuperados dos documentos para cada pergunta. Um valor entre 4 e 6 é geralmente ideal.


## 📄 Licença

Este projeto está licenciado sob a **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

![CC BY-NC 4.0](https://i.creativecommons.org/l/by-nc/4.0/88x31.png)

Isto significa que você é livre para partilhar e adaptar este trabalho para **fins não comerciais**, desde que dê o crédito apropriado aos criadores originais.

**Uso Comercial:**
O uso deste software em projetos ou produtos comerciais é estritamente proibido sob esta licença. Para obter uma licença comercial, por favor, entre em contacto com a equipa de desenvolvimento.
