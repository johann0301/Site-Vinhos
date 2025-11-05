import json
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

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

    def __repr__(self):
        return f'<Vinho {self.name}>'


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
    """Página do Catálogo - Mostra todos os vinhos"""
    # Pega todos os vinhos do banco, ordenados pelo ranking
    vinhos_lista = Vinho.query.order_by(Vinho.rank).all()
    return render_template('catalog.html', vinhos=vinhos_lista)

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    """Página de Recomendações - Baseado nos gostos do usuário"""
    if request.method == 'POST':
        # 1. Pega os dados do formulário
        pref_type = request.form.get('type')
        pref_grape = request.form.get('grape')
        pref_min_rating = request.form.get('min_rating', 0, type=float)

        # 2. Constrói a consulta ao banco de dados (query)
        query = Vinho.query

        if pref_type:
            query = query.filter(Vinho.type == pref_type)
        
        if pref_grape:
            # 'ilike' faz uma busca case-insensitive (ignora maiúsculas/minúsculas)
            query = query.filter(Vinho.grape_varieties.ilike(f'%{pref_grape}%'))
            
        if pref_min_rating > 0:
            query = query.filter(Vinho.average_rating >= pref_min_rating)

        # 3. Executa a query e pega os resultados
        # Ordena pela melhor nota e limita a 20 resultados
        results = query.order_by(Vinho.average_rating.desc()).limit(20).all()
        
        return render_template('recommend.html', results=results, search_done=True)

    # Se for GET, apenas mostra a página com o formulário
    return render_template('recommend.html', results=None, search_done=False)


# --- Executa o Aplicativo ---
if __name__ == '__main__':
    app.run(debug=True)