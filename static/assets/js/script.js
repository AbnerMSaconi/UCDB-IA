// static/assets/js/script.js - Versão com Mensagem de Boas-Vindas Dinâmica

document.addEventListener('DOMContentLoaded', () => {
    // --- Elementos do DOM ---
    const chat = document.getElementById('chat');
    const messageInput = document.getElementById('message');
    const sendButton = document.getElementById('send');

    /**
     * Mostra a mensagem inicial de boas-vindas.
     */
    async function showWelcomeMessage() {
        showTypingIndicator(); // Mostra o indicador enquanto carrega as áreas
        try {
            const response = await fetch('/knowledge-areas');
            if (!response.ok) {
                throw new Error('Não foi possível obter as áreas de conhecimento.');
            }
            const data = await response.json();
            const areas = data.areas;

            let welcomeText = "Olá, sou o **UCDB-IA**, um assistente de estudos acadêmicos.";

            if (areas && areas.length > 0) {
                welcomeText += "\n\nAtualmente, tenho domínio sobre as seguintes áreas de conhecimento:\n\n";
                const areaList = areas.map(area => `- ${area}`).join('\n');
                welcomeText += areaList;
            } else {
                welcomeText += "\n\nNo momento, não tenho nenhum documento em minha base de conhecimento. Por favor, adicione arquivos PDF na pasta `/pdfs` e reinicie o sistema para que eu possa aprender sobre eles.";
            }
            
            welcomeText += "\n\nComo posso ajudar?";
            
            hideTypingIndicator();
            addMessage('ai', welcomeText);

        } catch (error) {
            hideTypingIndicator();
            console.error("Erro ao carregar mensagem de boas-vindas:", error);
            addMessage('ai', "Olá, sou o **UCDB-IA**. Não consegui carregar minha base de conhecimento, mas estou pronto para ajudar como puder.");
        }
    }


    // --- Funções Auxiliares (O restante das funções permanece o mesmo) ---

    /**
     * Adiciona uma mensagem à interface do chat.
     * @param {string} role - O autor da mensagem ('user' ou 'ai').
     * @param {string} content - O conteúdo HTML ou de texto da mensagem.
     * @returns {HTMLElement} O elemento da mensagem criado.
     */
    function addMessage(role, content = '') {
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message ${role}`;

        if (role === 'ai') {
            messageWrapper.innerHTML = `
                <div class="ai-header">🤖 UCDB</div>
                <div class="content"></div>
                <div class="sources-container" style="display: none;"></div>
            `;
            if (content) {
                // Usamos marked.parse para renderizar o Markdown da mensagem de boas-vindas
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

        addMessage('user', text);
        messageInput.value = '';
        messageInput.style.height = 'auto';
        sendButton.disabled = true;

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
                            
                            // <-- ALTERAÇÃO IMPORTANTE AQUI -->
                            // Pede ao MathJax para procurar e renderizar a matemática no elemento atualizado
                            MathJax.typesetPromise([aiContentDiv]).catch((err) => console.log('Erro ao renderizar MathJax:', err));
                            
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

    sendButton.addEventListener('click', handleSendMessage);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = `${Math.min(messageInput.scrollHeight, 150)}px`;
    });

    // --- Inicialização ---
    showWelcomeMessage(); // Chama a nova função para exibir a mensagem de boas-vindas
    messageInput.focus();
});