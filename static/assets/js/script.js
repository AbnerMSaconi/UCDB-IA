// Elementos do DOM
const chat = document.getElementById('chat');
const messageInput = document.getElementById('message');
const sendButton = document.getElementById('send');

// Auto-resize do textarea
messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
});

// Adiciona uma mensagem ao chat
// static/assets/js/script.js
function addMessage(content, isUser = false) {
  const div = document.createElement('div');
  div.className = `message ${isUser ? 'user' : 'ai'}`;
  
  if (isUser) {
    div.textContent = content;
  } else {
    // Renderiza Markdown rico
    div.innerHTML = marked.parse(content);
    
    // Aplica estilos avançados
    div.querySelectorAll('pre').forEach(el => {
      el.style.background = 'rgba(0,0,0,0.4)';
      el.style.padding = '1rem';
      el.style.borderRadius = '8px';
      el.style.margin = '1rem 0';
      el.style.borderLeft = '4px solid #00f2fe';
      el.style.fontFamily = 'monospace';
      el.style.overflow = 'auto';
    });
    
    div.querySelectorAll('code').forEach(el => {
      if (!el.parentElement.matches('pre')) {
        el.style.background = 'rgba(0,0,0,0.3)';
        el.style.padding = '0.2rem 0.4rem';
        el.style.borderRadius = '4px';
        el.style.fontFamily = 'monospace';
      }
    });
    
    div.querySelectorAll('h1, h2, h3').forEach(el => {
      el.style.color = '#00f2fe';
      el.style.margin = '1rem 0 0.5rem 0';
    });
    
    div.querySelectorAll('ul, ol').forEach(el => {
      el.style.margin = '1rem 0';
      el.style.paddingLeft = '2rem';
    });
  }
  
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

// Aplica estilos ao conteúdo Markdown
function applyMarkdownStyles(container) {
  container.querySelectorAll('pre').forEach(el => {
    el.style.background = 'rgba(0,0,0,0.3)';
    el.style.padding = '1rem';
    el.style.borderRadius = '8px';
    el.style.margin = '1rem 0';
    el.style.borderLeft = '4px solid #00f2fe';
    el.style.overflow = 'auto';
  });
  container.querySelectorAll('code').forEach(el => {
    if (!el.parentElement.matches('pre')) {
      el.style.background = 'rgba(0,0,0,0.3)';
      el.style.padding = '0.2rem 0.4rem';
      el.style.borderRadius = '4px';
      el.style.fontFamily = 'monospace';
    }
  });
}

// Mostra indicador de digitação
function showTyping() {
  const div = document.createElement('div');
  div.className = 'message ai';
  div.id = 'typing';
  div.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

// Envia mensagem
async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;

  addMessage(text, true);
  messageInput.value = '';
  messageInput.style.height = 'auto';
  sendButton.disabled = true;

  const typing = showTyping();
  let aiDiv = addMessage('', false);
  let buffer = '';

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    if (!response.ok) throw new Error('Falha na conexão');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n').filter(line => line.trim().startsWith(''));

      for (const line of lines) {
        try {
          const data = JSON.parse(line.slice(5).trim());
          if (data.type === 'chunk') {
            buffer = data.content;
            aiDiv.innerHTML = marked.parse(buffer);
            //applyMarkdownStyles(aiDiv);
            chat.scrollTop = chat.scrollHeight;
          }
          if (data.type === 'error') {
            aiDiv.textContent = data.content;
            chat.scrollTop = chat.scrollHeight;
          }
        } catch (e) {
          console.warn('Erro ao processar chunk:', e);
        }
      }
    }

    typing.remove();
  } catch (error) {
    typing.remove();
    addMessage(`❌ Erro: ${error.message}`, false);
  } finally {
    sendButton.disabled = false;
  }
}

// Eventos
sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// Foco no input
messageInput.focus();