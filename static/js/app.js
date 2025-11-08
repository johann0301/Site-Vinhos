// Espera o HTML todo carregar antes de rodar o JS
document.addEventListener('DOMContentLoaded', () => {

    // 1. Encontra o formulário e o contêiner de resultados na página
    // (Vamos adicionar esses IDs no HTML na Etapa 3)
    const form = document.getElementById('form-recomendacao');
    const container = document.getElementById('container-resultados');

    // 2. Se não encontrar o formulário nesta página, não faz nada.
    // Isso evita erros em outras páginas (como /catalog)
    if (!form) {
        return;
    }

    // 3. Adiciona um "ouvinte" para o evento de 'submit' (clique no botão)
    form.addEventListener('submit', (event) => {
        // 4. IMPEDE o comportamento padrão do formulário (recarregar a página)
        event.preventDefault();

        // 5. Pega os dados do formulário e cria os parâmetros da URL
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);

        // 6. Mostra um feedback de "Carregando..."
        container.innerHTML = '<p>Buscando os melhores vinhos para você...</p>';

        // 7. A MÁGICA: Chama a API que criamos no Flask
        fetch(`/api/recomendar?${params.toString()}`)
            .then(response => response.json()) // Converte a resposta em JSON
            .then(vinhos => {
                // 8. Envia os dados JSON para a função que constrói o HTML
                renderizarVinhos(vinhos);
            })
            .catch(error => {
                // 9. Em caso de erro
                console.error('Erro ao buscar vinhos:', error);
                container.innerHTML = '<p>Erro ao buscar recomendações. Tente novamente.</p>';
            });
    });

    // 10. Função que constrói o HTML dos cards
    function renderizarVinhos(vinhos) {
        // Limpa a mensagem de "Carregando..."
        container.innerHTML = '';

        // 11. Verifica se a API retornou algum vinho
        if (vinhos.length === 0) {
            container.innerHTML = '<p>Nenhum vinho encontrado com esses critérios. Tente uma busca mais ampla.</p>';
            return;
        }

        // 12. Adiciona um título aos resultados
        container.innerHTML = `<p>Encontramos ${vinhos.length} vinhos para você:</p>`;

        // 13. Cria o grid (o mesmo do /catalog)
        const grid = document.createElement('div');
        grid.className = 'catalogo-grid';

        // 14. Loop: Para cada vinho no JSON, cria um card HTML
        vinhos.forEach(vinho => {
            // Usamos "template literals" (crases ``) para construir o HTML
            // Esta é a "tradução" do seu _vinho_card.html para JavaScript
            const cardHTML = `
                <div class="vinho-card">
                    <div class="card-header">
                        <h3>${vinho.name} (${vinho.vintage})</h3>
                        <p>
                            <strong>Tipo:</strong> ${vinho.type} |
                            <strong>País:</strong> ${vinho.country}
                        </p>
                    </div>
                    <div class="card-body">
                        <p><strong>Uvas:</strong> ${vinho.grape_varieties}</p>
                        <p><em>${vinho.description || ''}</em></p>
                    </div>
                    <div class="card-footer">
                        <div class="vinho-nota">
                            <span class="nota-valor">${vinho.average_rating.toFixed(1)}</span>
                            <span class="nota-avaliacoes">(${vinho.reviews_count} avaliações)</span>
                        </div>
                    </div>
                </div>
            `;
            // Adiciona o novo card ao grid
            grid.innerHTML += cardHTML;
        });

        // 15. Adiciona o grid completo ao contêiner
        container.appendChild(grid);
    }

});