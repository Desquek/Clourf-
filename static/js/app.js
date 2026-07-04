// ========================================
// MENU LATERAL
// ========================================

function toggleMenu() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.overlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
    }
}

// Fechar menu ao clicar fora
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.overlay');
    const menuBtn = document.querySelector('.menu-btn');
    
    if (sidebar && sidebar.classList.contains('open')) {
        if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
            sidebar.classList.remove('open');
            overlay.classList.remove('show');
        }
    }
});

// ========================================
// FECHAR ALERTAS AUTOMATICAMENTE
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 4000);
    });
});

// ========================================
// CONFIRMAR AÇÕES PERIGOSAS
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.btn-danger');
    deleteButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja realizar esta ação?')) {
                e.preventDefault();
            }
        });
    });
});

// ========================================
// PRÉ-VISUALIZAÇÃO DE IMAGEM (UPLOAD)
// ========================================

function previewImage(input, previewId) {
    const preview = document.getElementById(previewId);
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// ========================================
// PESQUISA RÁPIDA (AJAX)
// ========================================

let searchTimeout;

function searchQuick(query) {
    clearTimeout(searchTimeout);
    
    if (query.length < 2) {
        document.getElementById('search-results').innerHTML = '';
        return;
    }
    
    searchTimeout = setTimeout(function() {
        fetch(`/pesquisa-rapida?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                const resultsContainer = document.getElementById('search-results');
                if (data.resultados && data.resultados.length > 0) {
                    resultsContainer.innerHTML = data.resultados.map(item => `
                        <a href="/problema/${item.id}" class="search-result-item">
                            <strong>${item.titulo}</strong>
                            <span class="search-result-categoria">${item.categoria}</span>
                            <span class="search-result-autor">${item.autor}</span>
                        </a>
                    `).join('');
                } else {
                    resultsContainer.innerHTML = '<div class="search-result-empty">Nenhum resultado encontrado</div>';
                }
            })
            .catch(error => {
                console.error('Erro na pesquisa:', error);
            });
    }, 300);
}

// ========================================
// INICIALIZAR COMPONENTES
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Foco no campo de pesquisa
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                this.form.submit();
            }
        });
    }
});