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

Este projeto está licenciado sob a Licença MIT.
