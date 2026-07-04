// ========================================
// SCROLL PARA ÚLTIMA MENSAGEM
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const messagesContainer = document.getElementById('mensagens');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});

// ========================================
// ENVIAR MENSAGEM COM ENTER
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.querySelector('.conversa-enviar input');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.form.submit();
            }
        });
    }
});