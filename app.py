import json
from flask import Flask, render_template, request , jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

# --- Configuração do Aplicativo ---
app = Flask(__name__)
# Usando SQLite para este exemplo (fácil de começar)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vinhos.db'
# Para usar PostgreSQL (como você mencionou no passado), comente a linha acima e descomente a linha abaixo:
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://USUARIO:SENHA@localhost:5432/NOME_DO_BANCO'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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
    Rota da API que agrega dados do banco para os gráficos.
    """
    
    # 1. Gráfico de Tipos de Vinho (Pizza/Rosca)
    # Esta query agrupa os vinhos por 'type' e conta quantos existem em cada grupo.
    try:
        dados_tipos = db.session.query(
            Vinho.type,                             # O que queremos agrupar (ex: "Tinto")
            func.count(Vinho.id).label('count')     # Como queremos agregar (contar os IDs)
        ).group_by(
            Vinho.type                              # O comando de agrupamento
        ).all()                                     # Executa a query
        
        # Converte o resultado (ex: [('Tinto', 120), ('Branco', 85)])
        # em um formato amigável para o Chart.js
        chart_data_tipos = {
            'labels': [row[0] for row in dados_tipos if row[0]], # Pega os nomes (Tinto, Branco...)
            'data': [row[1] for row in dados_tipos if row[0]]    # Pega as contagens (120, 85...)
        }

        # 2. Gráfico de Notas por País (Barras) - (Vamos adicionar em breve)
        # ...
        
        # Por enquanto, retornamos apenas os dados do primeiro gráfico
        return jsonify({
            'graficoTipos': chart_data_tipos
        })

    except Exception as e:
        # Em caso de erro no banco
        print(f"Erro ao gerar dados do dashboard: {e}")
        return jsonify({"error": "Falha ao processar dados"}), 500
    

@app.route('/dashboard')
def dashboard():
    """Página do Dashboard - Mostra os gráficos"""
    return render_template('dashboard.html')


# --- Executa o Aplicativo ---
if __name__ == '__main__':
    app.run(debug=True)