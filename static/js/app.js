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

    // =========================================================================
    // --- LÓGICA DO MAPA CHOROPLETH (Corrigido para exibir o Tooltip) ---
    // =========================================================================
    
    // Mapeamento dos códigos ISO-3 (DataMaps) para nomes em Português
    // ESTE MAPA É ESSENCIAL PARA PEGAR O NOME EM PT/BR!
    const countryNameMap = {
        "ARG": "Argentina",
        "NZL": "Nova Zelândia",
        "USA": "EUA",
        "FRA": "França",
        "ESP": "Espanha",
        "ITA": "Itália",
        "AUS": "Austrália",
        "CHL": "Chile",
        "PRT": "Portugal",
        "DEU": "Alemanha",
        "BRA": "Brasil"
    };
    
    const mapContainer = document.getElementById('choropleth-map');

    if (mapContainer) {
        
        // Remove a mensagem de status (se existir)
        const statusElement = document.getElementById('mapa-status');
        if (statusElement) statusElement.remove();

        fetch('/api/mapa-vinhos')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                
                const countryData = data.countryData;
                
                const choroplethColors = {
                    'vinho_count_1': '#E0B4B4', // O Rosé claro do seu gráfico
                    'vinho_count_2': '#C38A7F', // Um tom de transição
                    'vinho_count_3': '#A65A54', // Um vinho mais aberto
                    'vinho_count_4': '#8A2A2A', // Um vinho mais fechado
                    'vinho_count_5': '#5C001F', // Sua cor principal (perfeito!)
                    defaultFill: '#333333'      // Um cinza mais escuro e neutro (melhor que #505050)
                };


                new Datamaps({
                    element: mapContainer,
                    scope: 'world', 
                    responsive: true,
                    fills: choroplethColors, 
                    data: countryData,

                    geographyConfig: {
                        borderColor: '#1a1a1a',
                        highlightBorderWidth: 2,
                        highlightFillColor: function(geo) {
                            return geo['properties']['fillColor'] || choroplethColors.defaultFill;
                        },
                        highlightBorderColor: '#D4AF37',
                        
                        // FUNÇÃO CRÍTICA DO TOOLTIP
                        popupTemplate: function(geography, data) {
                            // Obtém o nome: Tenta Port. do mapeamento, senão usa o nome do mapa (Inglês/default)
                            const name = countryNameMap[geography.id] || geography.properties.name;
                            
                            // Obtém a contagem: Se 'data' for null/undefined (país sem vinho), usa '0'.
                            let count = data ? data.numberOfWines : '0';
                            
                            // Monta o HTML do Tooltip (a caixa que aparece)
                            let tooltipHtml = `<div class="datamaps-hoverover"><strong>${name}</strong><br/>`;
                            tooltipHtml += `${count} Vinho(s) no Catálogo</div>`;
                            return tooltipHtml;
                        },
                        dataUrl: null // Garante que DataMaps confie nos dados fornecidos
                    },
                    
                    setProjection: function(element) {
                        const projection = d3.geo.mercator()
                            .center([-10, 0]) 
                            .scale(150)
                            .translate([element.offsetWidth / 2, element.offsetHeight / 2]);
                        const path = d3.geo.path().projection(projection);
                        return {projection: projection, path: path};
                    }
                });
                
                window.addEventListener('resize', () => {
                    const existingMap = document.getElementById('choropleth-map').querySelector('svg');
                    if(existingMap) {
                       // O Datamaps lida com o redimensionamento automaticamente.
                    }
                });

            })
            .catch(error => {
                console.error('Erro ao carregar o mapa choropleth:', error);
                mapContainer.innerHTML = '<p>Erro ao carregar o mapa de vinhos. Verifique a API /api/mapa-vinhos e o console.</p>';
            });
    } // Fim da lógica do mapa
}); // Fim do DOMContentLoaded