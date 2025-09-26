// static/assets/js/script.js - Versão Refatorada e Corrigida

document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos do DOM ---
    const chat = document.getElementById('chat');
    const messageInput = document.getElementById('message');
    const sendButton = document.getElementById('send');

    // --- Funções Auxiliares ---

    /**
     * Adiciona uma mensagem à interface do chat.
     * @param {string} role - O autor da mensagem ('user' ou 'ai').
     * @param {string} content - O conteúdo HTML ou de texto da mensagem.
     * @returns {HTMLElement} O elemento da mensagem criado.
     */
    function addMessage(role, content = '') {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message ${role}`;

        // Adiciona o cabeçalho "UCDB" apenas para mensagens da IA
        if (role === 'ai') {
            messageWrapper.innerHTML = `
                <div class="ai-header">🤖 UCDB</div>
                <div class="content"></div>
                <div class="sources-container" style="display: none;"></div>
            `;
            if (content) {
                messageWrapper.querySelector('.content').innerHTML = marked.parse(content);
            }
        } else {
            messageWrapper.innerHTML = `<div class="content"></div>`;
            messageWrapper.querySelector('.content').textContent = content;
        }
        
        chat.appendChild(messageWrapper);
        scrollToBottom();
        return messageWrapper;
    }

    /**
     * Mostra o indicador de "a digitar...".
     * @returns {HTMLElement} O elemento do indicador de digitação.
     */
    function showTypingIndicator() {
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing';
        typingIndicator.className = 'message ai';
        typingIndicator.innerHTML = `
            <div class="ai-header">🤖 UCDB</div>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chat.appendChild(typingIndicator);
        scrollToBottom();
        return typingIndicator;
    }

    /**
     * Remove o indicador de "a digitar...".
     */
    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('typing');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Mantém o chat scrollado para a última mensagem.
     */
    function scrollToBottom() {
        chat.scrollTop = chat.scrollHeight;
    }

    // --- Lógica Principal de Envio de Mensagem ---

    async function handleSendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        // Adiciona a mensagem do utilizador e limpa o input
        addMessage('user', text);
        messageInput.value = '';
        messageInput.style.height = 'auto';
        sendButton.disabled = true;

        // Mostra o indicador de digitação
        const typingIndicator = showTypingIndicator();
        
        let aiMessageElement;
        let responseBuffer = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            if (!response.ok) {
                throw new Error(`Erro de rede: ${response.statusText}`);
            }
            
            // Remove o indicador e prepara o contentor da mensagem da IA
            hideTypingIndicator();
            aiMessageElement = addMessage('ai');
            const aiContentDiv = aiMessageElement.querySelector('.content');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let streamDone = false;
            while (!streamDone) {
                const { done, value } = await reader.read();
                if (done) {
                    streamDone = true;
                    break;
                }

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n').filter(line => line.trim().startsWith('data:'));

                for (const line of lines) {
                    try {
                        const data = JSON.parse(line.slice(5).trim());

                        if (data.type === 'chunk') {
                            responseBuffer = data.content;
                            aiContentDiv.innerHTML = marked.parse(responseBuffer);
                            scrollToBottom();
                        } else if (data.type === 'sources' && data.content.length > 0) {
                            const sourcesContainer = aiMessageElement.querySelector('.sources-container');
                            sourcesContainer.style.display = 'block';
                            let sourcesHTML = '<h6>Fontes:</h6><ul>';
                            data.content.forEach(source => {
                                sourcesHTML += `<li>${source}</li>`;
                            });
                            sourcesHTML += '</ul>';
                            sourcesContainer.innerHTML = sourcesHTML;
                        } else if (data.type === 'error') {
                            aiContentDiv.innerHTML = `<p class="error">❌ Erro: ${data.content}</p>`;
                        }
                    } catch (e) {
                        console.warn('Chunk inválido ignorado:', line);
                    }
                }
            }

        } catch (error) {
            hideTypingIndicator();
            // Se a mensagem da IA já foi criada, mostra o erro nela, senão, cria uma nova.
            if (aiMessageElement) {
                aiMessageElement.querySelector('.content').innerHTML = `<p class="error">❌ Erro na comunicação com o servidor: ${error.message}</p>`;
            } else {
                addMessage('ai', `<p class="error">❌ Erro na comunicação com o servidor: ${error.message}</p>`);
            }
        } finally {
            sendButton.disabled = false;
            messageInput.focus();
            scrollToBottom();
        }
    }

    // --- Event Listeners ---

    // Enviar com o botão
    sendButton.addEventListener('click', handleSendMessage);

    // Enviar com Enter (sem Shift)
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Auto-resize do textarea
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${Math.min(messageInput.scrollHeight, 150)}px`;
    });

    // Foco inicial no input
    messageInput.focus();
});