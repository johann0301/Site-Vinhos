import json
from flask import Flask, render_template, request , jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import re

def gerar_nome_imagem(nome, vintage):
    # transforma o nome em algo seguro para usar como arquivo
    nome_formatado = re.sub(r'[^a-zA-Z0-9]+', '_', nome).lower()
    return f"{nome_formatado}_{vintage}.jpg"

# --- Configuração do Aplicativo ---
app = Flask(__name__)
# Usando SQLite para este exemplo (fácil de começar)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vinhos.db'
# Para usar PostgreSQL (como você mencionou no passado), comente a linha acima e descomente a linha abaixo:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://USUARIO:SENHA@localhost:5432/NOME_DO_BANCO'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.jinja_env.globals['gerar_nome_imagem'] = gerar_nome_imagem


# --- Modelo do Banco de Dados (Tabela Vinho) ---
# Esta classe define a tabela no banco de dados.
# Ela é baseada na estrutura do seu JSON.
class Vinho(db.Model):
    # ---- COLUNAS DA TABELA ----
    # GARANTA QUE TODAS ESTÃO INDENTADAS CORRETAMENTE
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.Integer)
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100))
    region = db.Column(db.String(100))
    # Armazenamos a lista de uvas como uma string separada por vírgula
    grape_varieties = db.Column(db.String(300))
    vintage = db.Column(db.Integer)
    type = db.Column(db.String(50))
    alcohol_abv = db.Column(db.Float)
    volume_ml = db.Column(db.Integer)
    description = db.Column(db.Text)
    # Pegamos os dados aninhados do 'buyer_rating'
    average_rating = db.Column(db.Float)
    reviews_count = db.Column(db.Integer)
    
    # ---- MÉTODOS DA CLASSE ----
    # ELES DEVEM ESTAR NO MESMO NÍVEL DE INDENTAÇÃO DAS COLUNAS
    
    def __repr__(self):
        return f'<Vinho {self.name}>'

    def to_dict(self):
        """Converte o objeto Vinho em um dicionário."""
        return {
            'id': self.id,
            'rank': self.rank,
            'name': self.name,
            'country': self.country,
            'region': self.region,
            'grape_varieties': self.grape_varieties,
            'vintage': self.vintage,
            'type': self.type,
            'average_rating': self.average_rating,
            'reviews_count': self.reviews_count,
            'description': self.description
        }

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    data = db.Column(db.DateTime, server_default=func.now())
    vinho_id = db.Column(db.Integer, db.ForeignKey('vinho.id'), nullable=False)

    vinho = db.relationship("Vinho", backref=db.backref("comentarios", lazy=True))

    def __repr__(self):
        return f"<Comentario {self.texto[:15]}>"


# --- Comando para Carregar o JSON no Banco de Dados ---
# Para executar: abra o terminal e digite: flask init-db
@app.cli.command('init-db')
def init_db_command():
    """Limpa os dados existentes e cria novas tabelas com dados do vinhos.json."""
    db.drop_all()
    db.create_all()

    # Carrega os dados do seu arquivo JSON
    try:
        with open('vinhos.json', 'r', encoding='utf-8') as f:
            vinhos_data = json.load(f)
    except FileNotFoundError:
        print("Erro: Arquivo 'vinhos.json' não encontrado.")
        return
    except json.JSONDecodeError:
        print("Erro: Falha ao decodificar 'vinhos.json'. Verifique o formato.")
        return

    # Acessamos a lista de vinhos que está DENTRO da chave "wines"
    lista_de_vinhos = vinhos_data['wines']
    
    for vinho_json in lista_de_vinhos:
    # --- FIM DA CORREÇÃO ---

        # Converte a lista de uvas em uma string
        # (O .get() é importante caso a chave 'grape_varieties' não exista em algum vinho)
        grape_str = ", ".join(vinho_json.get('grape_varieties', []))
        
        # Pega as informações de avaliação (tratando se não existir)
        rating_info = vinho_json.get('buyer_rating', {})
        avg_rating = rating_info.get('average')
        rev_count = rating_info.get('reviews_count')

        novo_vinho = Vinho(
            rank=vinho_json.get('rank'),
            name=vinho_json.get('name'),
            country=vinho_json.get('country'),
            region=vinho_json.get('region'),
            grape_varieties=grape_str,
            vintage=vinho_json.get('vintage'),
            type=vinho_json.get('type'),
            alcohol_abv=vinho_json.get('alcohol_abv'),
            volume_ml=vinho_json.get('volume_ml'),
            description=vinho_json.get('description'),
            average_rating=avg_rating,
            reviews_count=rev_count
        )
        db.session.add(novo_vinho)

    # Salva todas as mudanças no banco
    db.session.commit()
    print(f'Banco de dados inicializado com {len(vinhos_data)} vinhos!')


# --- Rotas do Site (Páginas) ---

@app.route('/')
def index():
    """Página Inicial"""
    return render_template('index.html')

@app.route('/catalog')
def catalog():
    """Página do Catálogo - Agora com paginação!"""
    
    # 1. Pega o número da página da URL (ex: /catalog?page=2)
    # O padrão é 1, e o 'type=int' garante que é um número.
    page = request.args.get('page', 1, type=int)
    
    # 2. Em vez de .all(), usamos .paginate()
    # Vamos mostrar 12 vinhos por página
    pagination = Vinho.query.order_by(Vinho.rank).paginate(
        page=page, 
        per_page=12, 
        error_out=False
    )
    
    # 3. 'pagination.items' contém os 12 vinhos da página atual
    # Passamos o objeto 'pagination' inteiro para o template
    return render_template('catalog.html', pagination=pagination)

@app.route('/recommend')
def recommend():
    """Página de Recomendações - Apenas serve o HTML. A busca é via JS."""

    # Pega a lista de países para preencher o <select>
    countries_db = db.session.query(Vinho.country).distinct().all()
    countries = sorted([c[0] for c in countries_db if c[0]])

    # Apenas renderiza a página. Sem 'results', sem 'search_done'.
    return render_template('recommend.html', countries=countries)

@app.route('/api/recomendar')
def api_recomendar():
    """Rota da API que retorna vinhos em formato JSON."""

    # 1. Pega os dados dos parâmetros da URL (ex: /api/recomendar?type=Tinto)
    # Usamos request.args para requisições GET
    pref_type = request.args.get('type')
    pref_grape = request.args.get('grape')
    pref_min_rating = request.args.get('min_rating', 0, type=float)
    pref_country = request.args.get('country')

    # 2. Constrói a consulta (exatamente como antes)
    query = Vinho.query

    if pref_type:
        query = query.filter(Vinho.type == pref_type)

    if pref_grape:
        query = query.filter(Vinho.grape_varieties.ilike(f'%{pref_grape}%'))

    if pref_min_rating > 0:
        query = query.filter(Vinho.average_rating >= pref_min_rating)

    if pref_country:
        query = query.filter(Vinho.country == pref_country)

    # 3. Executa a query
    results = query.order_by(Vinho.average_rating.desc()).limit(20).all()

    # 4. Converte os resultados para dicionários e retorna como JSON
    # Esta é a grande mudança!
    results_list = [vinho.to_dict() for vinho in results]
    return jsonify(results_list)



# --- Rota da API para o Dashboard ---

@app.route('/api/dashboard-data')
def api_dashboard_data():
    """
    Rota da API que agrega dados do banco para os gráficos,
    agora aceitando filtros de 'pais' e 'qualidade'.
    """
    
    try:
        # --- 1. LER OS FILTROS DA URL ---
        pais_filtro = request.args.get('pais')
        qualidade_filtro = request.args.get('qualidade', 0, type=float) # Padrão 0 (sem filtro)

        # --- 2. CRIAR A QUERY BASE ---
        # Esta é a base para TODAS as nossas consultas
        query_base = Vinho.query
        
        if pais_filtro:
            query_base = query_base.filter(Vinho.country == pais_filtro)
        
        if qualidade_filtro > 0:
            query_base = query_base.filter(Vinho.average_rating >= qualidade_filtro)

        
        # --- 3. CALCULAR OS DADOS USANDO A QUERY BASE ---

        # A. Gráfico de Tipos de Vinho (Pizza/Rosca)
        # Usamos 'with_entities' para selecionar colunas específicas da query_base
        dados_tipos = query_base.with_entities(
                Vinho.type, 
                func.count(Vinho.id)
            ).filter(Vinho.type.isnot(None)).group_by(Vinho.type).all()
        
        chart_data_tipos = {
            'labels': [row[0] for row in dados_tipos if row[0]],
            'data': [row[1] for row in dados_tipos if row[0]]
        }

        # B. Total de Vinhos (KPI)
        total_vinhos = query_base.count()
        
        # C. Total de Países Únicos (KPI)
        # Se um país foi filtrado, o total será 1. Senão, conta os distintos.
        if pais_filtro:
            total_paises = 1 if total_vinhos > 0 else 0 # Se o filtro não retornar vinhos, é 0
        else:
            # Conta países distintos *dentro* do filtro de qualidade
            total_paises = query_base.with_entities(Vinho.country).distinct().count()
        
        # D. Tipo Dominante (KPI)
        tipo_dominante = "N/A"
        if dados_tipos:
            tipo_dominante = max(dados_tipos, key=lambda row: row[1])[0]
        elif total_vinhos > 0: # Se há vinhos mas nenhum tem "tipo" (raro)
            tipo_dominante = "Indefinido"

        # E. Monta o dicionário dos KPIs
        dados_kpi = {
            "totalVinhos": total_vinhos,
            "totalPaises": total_paises,
            "tipoDominante": tipo_dominante
        }
        
        # --- 4. RETORNAR OS DADOS FILTRADOS ---
        return jsonify({
            'graficoTipos': chart_data_tipos,
            'kpiCards': dados_kpi
        })

    except Exception as e:
        print(f"Erro ao gerar dados do dashboard: {e}")
        return jsonify({"error": "Falha ao processar dados"}), 500
    

@app.route('/dashboard')
def dashboard():
    """Página do Dashboard - Mostra os gráficos"""
    # Pega a lista de países para preencher o <select>
    # (Exatamente como na página de Recomendações)
    countries_db = db.session.query(Vinho.country).distinct().all()
    countries = sorted([c[0] for c in countries_db if c[0]])
    return render_template('dashboard.html', countries=countries)

# Mantenha este mapeamento no topo do arquivo (ou próximo às rotas)
COUNTRY_CODE_MAP = {
    "Argentina": "ARG",
    "Nova Zelândia": "NZL",
    "EUA": "USA",
    "França": "FRA",
    "Espanha": "ESP",
    "Itália": "ITA",
    "Austrália": "AUS",
    "Chile": "CHL",
    "Portugal": "PRT",
    "Alemanha": "DEU",
    "Brasil": "BRA" 
    # Adicione outros países conforme necessário!
}


def get_wine_country_counts():
    """
    Calcula a contagem de vinhos por país usando o banco de dados
    e a formata para DataMaps.
    """
    # 1. Faz a query para contar os vinhos por país
    # O filtro "if Vinho.country.isnot(None)" garante que só contamos países definidos
    country_db_counts = db.session.query(
        Vinho.country,
        func.count(Vinho.id).label('count')
    ).filter(
        Vinho.country.isnot(None)
    ).group_by(
        Vinho.country
    ).all()
    
    # Dicionário para armazenar a contagem por código ISO (para o DataMaps)
    iso_counts = {}
    
    # 2. Mapeia os nomes em português para os códigos ISO
    for country_pt, count in country_db_counts:
        country_code = COUNTRY_CODE_MAP.get(country_pt, None)
        if country_code:
            iso_counts[country_code] = count
        # Se o país não estiver no mapeamento, ele será ignorado no mapa.

    # 3. Prepara o objeto no formato esperado pelo DataMaps
    formatted_data = {}
    max_wines = max(iso_counts.values()) if iso_counts else 1

    # Definimos 5 níveis de cor
    num_levels = 5
    # Garante que não dividimos por zero, usando 1 como divisor mínimo
    level_size = max_wines // num_levels
    level_divisor = level_size if level_size >= 1 else 1 

    for code, count in iso_counts.items():
        # Lógica para atribuir um nível de cor de 1 a 5
        level = min(num_levels, (count // level_divisor) + 1)
        
        formatted_data[code] = {
            'numberOfWines': count,
            'fillKey': f'vinho_count_{level}'
        }

    return formatted_data, max_wines


@app.route('/api/mapa-vinhos')
def api_mapa_vinhos():
    """Nova rota para fornecer dados de contagem de vinhos por país para o mapa."""
    try:
        data, max_wines = get_wine_country_counts()
        return jsonify({
            'countryData': data,
            'maxWines': max_wines
        })
    except Exception as e:
        # Retorna um erro 500 para o frontend em caso de falha no banco/lógica
        print(f"Erro na API /api/mapa-vinhos: {e}")
        return jsonify({"error": "Falha ao processar dados do mapa"}), 500

import baixar_imagens

@app.route("/vinho/<int:id>", methods=["GET", "POST"])
def detalhes_vinho(id):
    vinho = Vinho.query.get_or_404(id)

    if request.method == "POST":
        texto = request.form["comentario"]
        novo = Comentario(texto=texto, vinho_id=vinho.id)
        db.session.add(novo)
        db.session.commit()

    return render_template("detalhes_vinho.html", vinho=vinho)

@app.route("/vinho/<int:id>/comentario", methods=["POST"])
def adicionar_comentario(id):
    vinho = Vinho.query.get_or_404(id)

    texto = request.form.get("comentario")

    if texto:
        comentario = Comentario(
            vinho_id=id,
            texto=texto,
            data=datetime.now()
        )
        db.session.add(comentario)
        db.session.commit()

    return redirect(url_for("detalhes_vinho", id=id))


# --- Executa o Aplicativo ---
if __name__ == '__main__':
    app.run(debug=True)