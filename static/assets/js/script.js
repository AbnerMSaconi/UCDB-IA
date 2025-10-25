document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos do DOM ---
    const chat = document.getElementById('chat');
    const messageInput = document.getElementById('message');
    const sendButton = document.getElementById('send');
    const knowledgeSidebar = document.getElementById('knowledge-sidebar');
    const knowledgeList = document.getElementById('knowledge-list');
    const knowledgeToggleButton = document.getElementById('knowledge-toggle-button');
    const closeKnowledgeButton = document.getElementById('close-knowledge-button');
    const sourceChunksSidebar = document.getElementById('source-chunks-sidebar');
    const sourceChunksContent = document.getElementById('source-chunks-content');
    const closeSourcesButton = document.getElementById('close-sources-button');

    let currentSourceChunks = []; // Armazena chunks da resposta atual

    /** Preenche Sidebar Esquerda (Conhecimento) */
    async function populateKnowledgeSidebar() {
        try {
            const response = await fetch('/knowledge-areas');
            if (!response.ok) throw new Error('Falha ao buscar áreas');
            const data = await response.json();
            knowledgeList.innerHTML = '';
            if (data.areas && data.areas.length > 0) {
                data.areas.forEach(area => {
                    const li = document.createElement('li');
                    li.textContent = area;
                    knowledgeList.appendChild(li);
                });
            } else {
                knowledgeList.innerHTML = '<li>Nenhuma área encontrada.</li>';
            }
        } catch (error) {
            console.error("Erro sidebar conhecimento:", error);
            knowledgeList.innerHTML = '<li>Erro ao carregar.</li>';
        }
    }

    /** Alterna Sidebar Esquerda */
    function toggleKnowledgeSidebar() {
        knowledgeSidebar.classList.toggle('sidebar-visible');
        if (sourceChunksSidebar.classList.contains('sidebar-visible')) {
            sourceChunksSidebar.classList.remove('sidebar-visible');
        }
    }

    /** Alterna Sidebar Direita (Fontes/Trechos) */
    function toggleSourcesSidebar() {
        sourceChunksSidebar.classList.toggle('sidebar-visible');
         if (knowledgeSidebar.classList.contains('sidebar-visible')) {
            knowledgeSidebar.classList.remove('sidebar-visible');
        }
    }

    /** Limpa e preenche a Sidebar Direita com os trechos (Atualizada com Links) */
    function displaySourceChunks(chunks) {
        sourceChunksContent.innerHTML = ''; // Limpa
        if (chunks && chunks.length > 0) {
            chunks.forEach(chunk => {
                const chunkDiv = document.createElement('div');
                chunkDiv.className = 'source-chunk';

                // --- ALTERAÇÃO AQUI: Cria o Link ---
                // Cria um link <a> com o URL do PDF, abrindo em nova aba
                // O texto do link continua a ser "Nome.pdf (pág. X)"
                const sourceLink = `<a href="${chunk.url}" target="_blank" rel="noopener noreferrer" title="Abrir ${chunk.source.split(' ')[0]}">${chunk.source}</a>`;

                // Usa o link no cabeçalho do trecho (dentro do <strong>)
                // Usamos innerHTML porque o backend já escapou o HTML do chunk.content
                chunkDiv.innerHTML = `<strong>${sourceLink}</strong><p>${chunk.content.replace(/\n/g, '<br>')}</p>`;
                sourceChunksContent.appendChild(chunkDiv);
            });
        } else {
            sourceChunksContent.innerHTML = '<p class="placeholder">Nenhum trecho específico foi utilizado para esta resposta.</p>';
        }
    }

    // --- Funções Auxiliares (addMessage, show/hideTyping, scrollToBottom) ---
     function addMessage(role, content = '', isLoading = false) {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message ${role}`;
        if (role === 'ai') {
             messageWrapper.innerHTML = `
                <div class="ai-header">🤖 UCDB</div>
                <div class="content"></div>
                `;
             if (isLoading) {
                 messageWrapper.querySelector('.content').innerHTML = '<p>...</p>';
             } else if (content){
                 const contentDiv = messageWrapper.querySelector('.content');
                 contentDiv.innerHTML = marked.parse(content);
                 // Adia MathJax para o final do stream
             }
        } else {
            messageWrapper.innerHTML = `<div class="content"></div>`;
            messageWrapper.querySelector('.content').textContent = content;
        }
        chat.appendChild(messageWrapper);
        scrollToBottom();
        return messageWrapper;
    }

    function showTypingIndicator() {
        if (document.getElementById('typing')) return;
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing';
        typingIndicator.className = 'message ai typing-indicator-wrapper';
        typingIndicator.innerHTML = `<div class="ai-header">🤖 UCDB</div><div class="typing-indicator"><div class="typing-dot"></div> <div class="typing-dot"></div> <div class="typing-dot"></div></div>`;
        chat.appendChild(typingIndicator);
        scrollToBottom();
        return typingIndicator;
    }

    function hideTypingIndicator() {
        const el = document.getElementById('typing');
        if (el) el.remove();
    }

    function scrollToBottom() {
        // Usa requestAnimationFrame para garantir que o scroll ocorra após o DOM update
        requestAnimationFrame(() => {
             // Scroll suave pode ser melhor, mas direto é mais garantido
             // chat.scrollTo({ top: chat.scrollHeight, behavior: 'smooth' });
             chat.scrollTop = chat.scrollHeight;
        });
    }


    // --- Lógica Principal de Envio de Mensagem ---
    async function handleSendMessage() {
        const text = messageInput.value.trim();
        if (!text || sendButton.disabled) return;

        addMessage('user', text);
        messageInput.value = ''; messageInput.style.height = 'auto'; sendButton.disabled = true;
        sourceChunksContent.innerHTML = '<p class="placeholder">Aguardando nova resposta...</p>';
        currentSourceChunks = []; // Reseta chunks

        let aiMessageElement = addMessage('ai', '', true); // Cria bolha de loading
        const aiContentDiv = aiMessageElement.querySelector('.content');

        let responseBuffer = '';
        let sourcesData = null; // Lista formatada para o botão
        let streamComplete = false;
        let mathJaxRendered = false; // Flag para controlar renderização MathJax

        try {
            const response = await fetch('/chat', {
                 method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: text })
            });

            if (!response.ok || !response.body) {
                throw new Error(`Erro de rede: ${response.statusText}`);
            }

            aiContentDiv.innerHTML = ''; // Remove placeholder de loading

            const reader = response.body.getReader(); const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    // Render final do conteúdo principal (Markdown)
                    if (responseBuffer && !aiContentDiv.classList.contains('error-message')) {
                        aiContentDiv.innerHTML = marked.parse(responseBuffer);
                        mathJaxRendered = false; // Sinaliza que MathJax precisa rodar
                    }

                    // Cria o botão "Ver Fontes Detalhadas" se houver fontes E chunks
                    if (sourcesData && sourcesData.length > 0 && currentSourceChunks && currentSourceChunks.length > 0) {
                        const sourcesButton = document.createElement('button');
                        sourcesButton.textContent = 'Ver Fontes Detalhadas';
                        sourcesButton.className = 'show-sources-button';
                        sourcesButton.dataset.chunks = JSON.stringify(currentSourceChunks); // Guarda chunks no botão
                        sourcesButton.onclick = (event) => {
                            try {
                                const chunksToShow = JSON.parse(event.target.dataset.chunks);
                                displaySourceChunks(chunksToShow);
                                toggleSourcesSidebar();
                            } catch (e) { console.error("Erro ao processar chunks:", e); toggleSourcesSidebar(); }
                        };
                        aiMessageElement.appendChild(sourcesButton);
                    }

                    // Renderiza MathJax após todo o conteúdo e botão estarem no DOM
                    if (!mathJaxRendered && responseBuffer && !aiContentDiv.classList.contains('error-message')) {
                         try {
                             console.log("Tentando renderizar MathJax no final...");
                             await MathJax.typesetPromise([aiContentDiv]);
                             console.log("MathJax renderizado com sucesso.");
                             mathJaxRendered = true;
                         } catch (err) { console.error('Erro MathJax final:', err); }
                    }

                    scrollToBottom(); // Garante scroll final
                    break; // Sai do loop
                }

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                     if (line.startsWith('data:')) {
                        try {
                            const data = JSON.parse(line.slice(5).trim());

                            if (data.type === 'source_chunks') {
                                currentSourceChunks = data.content;
                            }
                            else if (data.type === 'chunk') {
                                responseBuffer = data.content;
                                // Atualiza apenas texto bruto + cursor
                                aiContentDiv.textContent = responseBuffer + '█';
                                scrollToBottom(); // Scroll durante o stream
                            }
                            else if (data.type === 'sources') {
                                sourcesData = data.content;
                            }
                            else if (data.type === 'complete') {
                                streamComplete = true;
                                // Remove o cursor após receber 'complete'
                                if (aiContentDiv.textContent.endsWith('█')) {
                                   aiContentDiv.textContent = responseBuffer;
                                }
                            }
                            else if (data.type === 'error') {
                                aiContentDiv.innerHTML = `<p class="error">❌ Erro: ${data.content}</p>`;
                                aiContentDiv.classList.add('error-message');
                                scrollToBottom();
                            }
                        } catch (e) { console.warn('Chunk inválido:', line, e); }
                    }
                }
            } // Fim do while(true)
        } catch (error) {
            const errorMsg = `❌ Erro na comunicação: ${error.message}`;
            if (aiMessageElement) {
                aiContentDiv.innerHTML = `<p class="error">${errorMsg}</p>`;
                aiContentDiv.classList.add('error-message');
            } else { addMessage('ai', `<p class="error">${errorMsg}</p>`); }
            scrollToBottom();
        } finally {
            sendButton.disabled = false;
            messageInput.focus();
        }
    }

    // --- Event Listeners ---
    sendButton.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } });
    messageInput.addEventListener('input', () => { messageInput.style.height = 'auto'; messageInput.style.height = `${Math.min(messageInput.scrollHeight, 150)}px`; });
    knowledgeToggleButton.addEventListener('click', toggleKnowledgeSidebar);
    closeKnowledgeButton.addEventListener('click', toggleKnowledgeSidebar);
    closeSourcesButton.addEventListener('click', toggleSourcesSidebar);

    // --- Inicialização ---
    populateKnowledgeSidebar();
    messageInput.focus();
});