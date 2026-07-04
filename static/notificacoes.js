// ========================================
// ATUALIZAR CONTADOR DE NOTIFICAÇÕES
// ========================================

function updateNotificationCount() {
    fetch('/notificacoes/contagem')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Erro ao atualizar notificações:', error);
        });
}

// Atualizar a cada 30 segundos
if (document.getElementById('notification-badge')) {
    setInterval(updateNotificationCount, 30000);
}