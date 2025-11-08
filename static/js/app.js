// Espera o HTML todo carregar antes de rodar o JS
document.addEventListener('DOMContentLoaded', () => {

    // --- LÓGICA DO FORMULÁRIO DE RECOMENDAÇÃO ---
    const form = document.getElementById('form-recomendacao');
    const container = document.getElementById('container-resultados');

    // Só executa o código do formulário se ele estiver na página
    if (form && container) {
        
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);
            container.innerHTML = '<p>Buscando os melhores vinhos para você...</p>';

            fetch(`/api/recomendar?${params.toString()}`)
                .then(response => response.json()) 
                .then(vinhos => {
                    renderizarVinhos(vinhos);
                })
                .catch(error => {
                    console.error('Erro ao buscar vinhos:', error);
                    container.innerHTML = '<p>Erro ao buscar recomendações. Tente novamente.</p>';
                });
        });

        function renderizarVinhos(vinhos) {
            container.innerHTML = '';
            if (vinhos.length === 0) {
                container.innerHTML = '<p>Nenhum vinho encontrado com esses critérios. Tente uma busca mais ampla.</p>';
                return;
            }
            container.innerHTML = `<p>Encontramos ${vinhos.length} vinhos para você:</p>`;
            const grid = document.createElement('div');
            grid.className = 'catalogo-grid';

            vinhos.forEach(vinho => {
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
                grid.innerHTML += cardHTML;
            });
            container.appendChild(grid);
        }
    } // Fim da lógica do formulário

    
    // --- CÓDIGO DO DASHBOARD ---
    
    const ctx = document.getElementById('graficoTipos');

    if (ctx) {
        fetch('/api/dashboard-data')
            .then(response => response.json())
            .then(data => {
                
                console.log(data); 
                const dadosDoGrafico = data.graficoTipos;

                // --- A CORREÇÃO ESTÁ AQUI ---
                // Antes de criar um novo gráfico, verificamos se já existe um.
                // Isso corrige o erro "Canvas is already in use".
                const existingChart = Chart.getChart(ctx);
                if (existingChart) {
                    existingChart.destroy();
                }
                // --- FIM DA CORREÇÃO ---

                // Cria o gráfico
                new Chart(ctx, {
                    type: 'doughnut', 
                    data: {
                        labels: dadosDoGrafico.labels, 
                        datasets: [{
                            label: 'Qtd. de Vinhos',
                            data: dadosDoGrafico.data, 
                            backgroundColor: [
                                '#5C001F', 
                                '#E0B4B4',
                                '#F8F0E3',
                                '#8A9A5B',
                                '#D4AF37'
                            ],
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true, 
                        plugins: {
                            legend: {
                                position: 'top', 
                            }
                        }
                    }
                });
            })
            .catch(error => {
                // Agora o log de erro será mais específico
                console.error('Erro ao processar o gráfico:', error);
                ctx.parentElement.innerHTML = '<p>Erro ao carregar o gráfico.</p>';
            });
    } // Fim da lógica do dashboard

}); // Fim do DOMContentLoaded