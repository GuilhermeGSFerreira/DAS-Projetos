from flask import Flask, jsonify, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change_this_to_a_random_secret"  # necessary for sessions

# tell flask where templates are (default 'templates' folder)
app.template_folder = 'templates'

# --- CONFIGURAÇÃO DA LIGAÇÃO ---
# A aplicação lê primeiro a variável de ambiente DATABASE_URL, se existir.
# Pode ser assim:
#   export DATABASE_URL="mysql+pymysql://root:minhaSenha@localhost/healthsim_db"
# no Windows PowerShell:
#   setx DATABASE_URL "mysql+pymysql://root:minhaSenha@localhost/healthsim_db"
# Caso contrário usa um valor por defeito que podes editar abaixo.
import os

default_uri = 'mysql+pymysql://root:password_aqui@localhost/healthsim_db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_uri)
# altera `default_uri` ou define DATABASE_URL se precisares de outra base/credenciais

# tentamos ligar ao servidor MySQL e criar a base se não existir; se a
# ligação falhar (por ex. serviço desligado) utilizamos um ficheiro SQLite
# local como fallback para que a aplicação consiga arrancar sem erro.
try:
    import pymysql
    from urllib.parse import urlparse

    parsed = urlparse(app.config['SQLALCHEMY_DATABASE_URI'])
    dbname = parsed.path.lstrip('/')
    host = parsed.hostname
    port = parsed.port or 3306
    user = parsed.username
    password = parsed.password or ''

    # estabelece ligação temporária apenas para criar a base
    conn = pymysql.connect(host=host, user=user, password=password, port=port)
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    conn.commit()
    conn.close()
except Exception as e:
    # falha na ligação (provavelmente MySQL não está em execução); fallback
    print("[WARNING] não foi possível ligar ao MySQL, usando SQLite local:", e)
    sqlite_path = os.path.join(os.path.dirname(__file__), 'fallback.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MAPEAMENTO DAS TABELAS (EXATAMENTE COMO O TEU SQL) ---

class EstadoUtilizador(db.Model):
    __tablename__ = 'ESTADO_UTILIZADOR'
    id = db.Column(db.Integer, primary_key=True)
    descricao_estado = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "descricao_estado": self.descricao_estado
        }

class TipoUtilizador(db.Model):
    __tablename__ = 'TIPO_UTILIZADOR'
    id = db.Column(db.Integer, primary_key=True)
    descricao_tipo = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {"id": self.id, "descricao_tipo": self.descricao_tipo}

class EstadoSimulacao(db.Model):
    __tablename__ = 'ESTADO_SIMULACAO'
    id = db.Column(db.Integer, primary_key=True)
    descricao_estado = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {"id": self.id, "descricao_estado": self.descricao_estado}

class Utilizadores(db.Model):
    __tablename__ = 'UTILIZADORES'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    genero_id = db.Column(db.Integer)
    data_nascimento = db.Column(db.Date)
    img_url = db.Column(db.String(255))
    fk_estado_utilizador_id = db.Column(db.Integer, db.ForeignKey('ESTADO_UTILIZADOR.id'))
    fk_tipo_utilizador_id = db.Column(db.Integer, db.ForeignKey('TIPO_UTILIZADOR.id'))
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    # Relacionamento para facilitar a contagem
    simulacoes = db.relationship('Simulacoes', backref='autor', lazy=True)

    estado = db.relationship('EstadoUtilizador', lazy=True)
    tipo = db.relationship('TipoUtilizador', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "tipo": self.tipo.descricao_tipo if self.tipo else None,
            "estado": self.estado.descricao_estado if self.estado else None
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Simulacoes(db.Model):
    __tablename__ = 'SIMULACOES'
    id = db.Column(db.Integer, primary_key=True)
    fk_utilizador_id = db.Column(db.Integer, db.ForeignKey('UTILIZADORES.id'))
    fk_estado_simulacao_id = db.Column(db.Integer, db.ForeignKey('ESTADO_SIMULACAO.id'))
    nome = db.Column(db.String(100))
    populacao_total = db.Column(db.Integer)
    infetados_iniciais = db.Column(db.Integer)
    taxa_contagio_beta = db.Column(db.Numeric(5,4))
    taxa_recuperacao_gamma = db.Column(db.Numeric(5,4))
    duracao_t = db.Column(db.Integer)
    criado_em = db.Column(db.DateTime, server_default=func.now())
    atualizado_em = db.Column(db.DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "autor_id": self.fk_utilizador_id
        }

class TesteDenca(db.Model):
    __tablename__ = 'TESTES_DENCA'
    id = db.Column(db.Integer, primary_key=True)
    fk_utilizador_id = db.Column(db.Integer, db.ForeignKey('UTILIZADORES.id'), nullable=False)
    nome_doenca = db.Column(db.String(100), nullable=False)
    resultado = db.Column(db.String(20), nullable=False)  # 'positivo' ou 'negativo'
    criado_em = db.Column(db.DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "nome_doenca": self.nome_doenca,
            "resultado": self.resultado,
            "criado_em": self.criado_em.strftime('%d/%m/%Y %H:%M:%S') if self.criado_em else None
        }

# --- ENDPOINTS REQUISITADOS ---

@app.route('/api/stats/utilizadores', methods=['GET'])
def get_user_stats():
    """ US_B012: Total de utilizadores registados e ativos """
    try:
        total_registados = Utilizadores.query.count()
        
        # Fazemos um JOIN para contar apenas onde a descrição é 'Ativo'
        total_ativos = db.session.query(Utilizadores).join(EstadoUtilizador).filter(
            EstadoUtilizador.descricao_estado == 'Ativo'
        ).count()
        
        return jsonify({
            "total_registados": total_registados,
            "total_ativos": total_ativos
        }), 200
    except Exception as e:
        return jsonify({"erro": f"Erro na BD: {str(e)}"}), 500

@app.route('/api/stats/simulacoes/total', methods=['GET'])
def get_total_simulations():
    """ US_B013: Total de simulações na plataforma """
    try:
        total = Simulacoes.query.count()
        return jsonify({"total_simulacoes": total}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route('/api/stats/simulacoes/utilizador/<int:user_id>', methods=['GET'])
def get_user_simulations_count(user_id):
    """ US_B014: Simulações de um utilizador específico """
    try:
        # Verifica se o utilizador existe primeiro
        user = Utilizadores.query.get(user_id)
        if not user:
            return jsonify({"erro": "Utilizador não encontrado"}), 404
            
        contagem = Simulacoes.query.filter_by(fk_utilizador_id=user_id).count()
        return jsonify({
            "id_utilizador": user_id,
            "nome": user.nome,
            "total_simulacoes": contagem
        }), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# --- PÁGINAS E AUTENTICAÇÃO ---

@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('login.html')  # same template, tabs decide

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json or request.form
    nome = data.get('name')
    email = data.get('email')
    password = data.get('password')
    tipo = data.get('type', 'cliente')

    if not nome or not email or not password:
        return jsonify({"erro": "Campos obrigatórios em falta"}), 400

    existing = Utilizadores.query.filter_by(email=email).first()
    if existing:
        return jsonify({"erro": "Email já registado"}), 409

    estado = EstadoUtilizador.query.filter_by(descricao_estado='Ativo').first()
    tipo_obj = TipoUtilizador.query.filter_by(descricao_tipo=tipo).first()
    if not estado or not tipo_obj:
        return jsonify({"erro": "Dados de lookup em falta"}), 500

    user = Utilizadores(nome=nome, email=email, fk_estado_utilizador_id=estado.id, fk_tipo_utilizador_id=tipo_obj.id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"success": True}), 201

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or request.form
    email = data.get('email')
    password = data.get('password')
    user = Utilizadores.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"erro": "Credenciais inválidas"}), 401
    session['user_id'] = user.id
    session['user_type'] = user.tipo.descricao_tipo if user.tipo else None
    session['user_name'] = user.nome
    return jsonify({"success": True, "type": session['user_type']})

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/home')
def home_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Redirecionar baseado no tipo de utilizador
    user_type = session.get('user_type')
    if user_type in ['dev', 'gestor', 'admin']:
        return render_template('dev-home.html')
    else:
        return render_template('cliente.html')

@app.route('/admin')
def admin_page():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/manage')
def manage_page():
    # Dev, Gestor e Admin conseguem aceder
    if session.get('user_type') not in ['dev', 'gestor', 'admin']:
        return redirect(url_for('login_page'))
    return render_template('manage.html')

# APIs para gestão de utilizadores (admin)
@app.route('/api/users', methods=['GET'])
def api_get_users():
    users = Utilizadores.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/api/user/<int:user_id>', methods=['PUT','DELETE'])
def api_user_modify(user_id):
    # Verificar permissões
    if 'user_type' not in session or session['user_type'] not in ['dev', 'gestor', 'admin']:
        return jsonify({"erro": "Sem permissão"}), 403
    
    user = Utilizadores.query.get(user_id)
    if not user:
        return jsonify({"erro": "Utilizador não encontrado"}), 404
    
    if request.method == 'DELETE':
        # Apenas dev pode apagar
        if session['user_type'] != 'dev':
            return jsonify({"erro": "Apenas dev pode apagar utilizadores"}), 403
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True})
    else:
        # PUT - editar utilizador
        data = request.json
        
        # Dev pode editar nome e email
        if session['user_type'] == 'dev':
            if 'nome' in data:
                user.nome = data['nome']
            if 'email' in data:
                user.email = data['email']
        
        # Dev e Gestor podem editar tipo
        if 'tipo' in data:
            tipo_obj = TipoUtilizador.query.filter_by(descricao_tipo=data['tipo']).first()
            if tipo_obj:
                user.fk_tipo_utilizador_id = tipo_obj.id
        
        # Dev e Gestor podem editar estado
        if 'estado' in data:
            estado_obj = EstadoUtilizador.query.filter_by(descricao_estado=data['estado']).first()
            if estado_obj:
                user.fk_estado_utilizador_id = estado_obj.id
        
        db.session.commit()
        return jsonify({"success": True})

@app.route('/api/session', methods=['GET'])
def api_session():
    if 'user_id' not in session:
        return jsonify({}), 401
    return jsonify({
        "id": session['user_id'],
        "name": session.get('user_name'),
        "type": session.get('user_type')
    })

@app.route('/api/user-info/<int:user_id>', methods=['GET'])
def api_user_info(user_id):
    """Retorna informações de tipo e estado do utilizador."""
    user = Utilizadores.query.get(user_id)
    if not user:
        return jsonify({"erro": "Utilizador não encontrado"}), 404
    return jsonify({
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "tipo": user.tipo.descricao_tipo if user.tipo else None,
        "estado": user.estado.descricao_estado if user.estado else None
    })


# --- HELPER PARA VERIFICAÇÃO DE PERMISSÕES ---

def check_role(*allowed_roles):
    """Verifica se o utilizador atual tem uma das roles permitidas."""
    user_type = session.get('user_type')
    if user_type not in allowed_roles:
        return False
    return True

def require_role(*allowed_roles):
    """Decorator para exigir role; retorna 403 se não tiver permissão."""
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not check_role(*allowed_roles):
                return jsonify({"erro": "Sem permissão"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# --- APIS PARA GERIR ESTADOS DE UTILIZADOR ---
# Dev e Gestor conseguem ver, editar e eliminar estados

@app.route('/api/estado-utilizadores', methods=['GET'])
def api_get_estados():
    """Lista todos os estados de utilizador."""
    estados = EstadoUtilizador.query.all()
    return jsonify([e.to_dict() for e in estados])

@app.route('/api/estado-utilizador', methods=['POST'])
@require_role('dev', 'gestor', 'admin')
def api_create_estado():
    """Dev/Gestor criar novo estado de utilizador."""
    data = request.json
    descricao = data.get('descricao_estado')
    if not descricao:
        return jsonify({"erro": "Descrição obrigatória"}), 400
    
    existing = EstadoUtilizador.query.filter_by(descricao_estado=descricao).first()
    if existing:
        return jsonify({"erro": "Estado já existe"}), 409
    
    estado = EstadoUtilizador(descricao_estado=descricao)
    db.session.add(estado)
    db.session.commit()
    return jsonify(estado.to_dict()), 201

@app.route('/api/estado-utilizador/<int:estado_id>', methods=['PUT'])
@require_role('dev', 'gestor', 'admin')
def api_update_estado(estado_id):
    """Dev/Gestor editar estado de utilizador."""
    estado = EstadoUtilizador.query.get(estado_id)
    if not estado:
        return jsonify({"erro": "Estado não encontrado"}), 404
    
    data = request.json
    if 'descricao_estado' in data:
        estado.descricao_estado = data['descricao_estado']
    db.session.commit()
    return jsonify(estado.to_dict())

@app.route('/api/estado-utilizador/<int:estado_id>', methods=['DELETE'])
@require_role('dev', 'gestor', 'admin')
def api_delete_estado(estado_id):
    """Dev/Gestor eliminar estado de utilizador."""
    estado = EstadoUtilizador.query.get(estado_id)
    if not estado:
        return jsonify({"erro": "Estado não encontrado"}), 404
    
    # verifica se o estado está a ser usado
    count = Utilizadores.query.filter_by(fk_estado_utilizador_id=estado_id).count()
    if count > 0:
        return jsonify({"erro": f"Estado ainda está em uso por {count} utilizador(es)"}), 409
    
    db.session.delete(estado)
    db.session.commit()
    return jsonify({"success": True})


# --- APIS PARA GERIR TIPOS DE UTILIZADOR ---
# Only Dev consegue eliminar tipos; todos conseguem ver

@app.route('/api/tipo-utilizadores', methods=['GET'])
def api_get_tipos():
    """Lista todos os tipos de utilizador."""
    tipos = TipoUtilizador.query.all()
    return jsonify([t.to_dict() for t in tipos])

@app.route('/api/tipo-utilizador', methods=['POST'])
@require_role('dev', 'admin')
def api_create_tipo():
    """Dev/Admin criar novo tipo de utilizador."""
    data = request.json
    descricao = data.get('descricao_tipo')
    if not descricao:
        return jsonify({"erro": "Descrição obrigatória"}), 400
    
    existing = TipoUtilizador.query.filter_by(descricao_tipo=descricao).first()
    if existing:
        return jsonify({"erro": "Tipo já existe"}), 409
    
    tipo = TipoUtilizador(descricao_tipo=descricao)
    db.session.add(tipo)
    db.session.commit()
    return jsonify(tipo.to_dict()), 201

@app.route('/api/tipo-utilizador/<int:tipo_id>', methods=['PUT'])
@require_role('dev', 'admin')
def api_update_tipo(tipo_id):
    """Dev/Admin editar tipo de utilizador."""
    tipo = TipoUtilizador.query.get(tipo_id)
    if not tipo:
        return jsonify({"erro": "Tipo não encontrado"}), 404
    
    data = request.json
    if 'descricao_tipo' in data:
        tipo.descricao_tipo = data['descricao_tipo']
    db.session.commit()
    return jsonify(tipo.to_dict())

@app.route('/api/tipo-utilizador/<int:tipo_id>', methods=['DELETE'])
@require_role('dev')
def api_delete_tipo(tipo_id):
    """Only Dev consegue eliminar tipos de utilizador."""
    tipo = TipoUtilizador.query.get(tipo_id)
    if not tipo:
        return jsonify({"erro": "Tipo não encontrado"}), 404
    
    # verifica se o tipo está a ser usado
    count = Utilizadores.query.filter_by(fk_tipo_utilizador_id=tipo_id).count()
    if count > 0:
        return jsonify({"erro": f"Tipo ainda está em uso por {count} utilizador(es)"}), 409
    
    db.session.delete(tipo)
    db.session.commit()
    return jsonify({"success": True})

# --- APIS PARA TESTES DE DOENÇA ---

@app.route('/api/teste-denca', methods=['POST'])
def api_criar_teste_denca():
    """Criar novo teste de doença para o utilizador autenticado."""
    if 'user_id' not in session:
        return jsonify({"erro": "Não autenticado"}), 401
    
    data = request.json
    nome_doenca = data.get('nome_doenca', '').strip()
    resultado = data.get('resultado', '').strip()
    
    if not nome_doenca or resultado not in ['positivo', 'negativo']:
        return jsonify({"erro": "Dados inválidos"}), 400
    
    teste = TesteDenca(
        fk_utilizador_id=session['user_id'],
        nome_doenca=nome_doenca,
        resultado=resultado
    )
    db.session.add(teste)
    db.session.commit()
    return jsonify(teste.to_dict()), 201

@app.route('/api/testes-denca', methods=['GET'])
def api_listar_testes_denca():
    """Listar testes de doença do utilizador autenticado."""
    if 'user_id' not in session:
        return jsonify({"erro": "Não autenticado"}), 401
    
    testes = TesteDenca.query.filter_by(fk_utilizador_id=session['user_id']).order_by(TesteDenca.criado_em.desc()).all()
    return jsonify([t.to_dict() for t in testes])

@app.route('/api/testes-denca/<int:user_id>', methods=['GET'])
@require_role('dev', 'gestor', 'admin')
def api_listar_testes_denca_user(user_id):
    """Dev/Gestor veem testes de doença de um utilizador específico."""
    testes = TesteDenca.query.filter_by(fk_utilizador_id=user_id).order_by(TesteDenca.criado_em.desc()).all()
    return jsonify([t.to_dict() for t in testes])

@app.route('/api/simulacoes-user/<int:user_id>', methods=['GET'])
@require_role('dev', 'gestor', 'admin')
def api_listar_simulacoes_user(user_id):
    """Dev/Gestor veem simulações de um utilizador específico."""
    simulacoes = Simulacoes.query.filter_by(fk_utilizador_id=user_id).all()
    return jsonify([s.to_dict() for s in simulacoes])

# ensure tables exist & seed lookup values (development convenience)
with app.app_context():
    db.create_all()
    # insert default tipos and estados if they don't exist
    if not TipoUtilizador.query.first():
        db.session.add_all([
            TipoUtilizador(descricao_tipo='cliente'),
            TipoUtilizador(descricao_tipo='gestor'),
            TipoUtilizador(descricao_tipo='dev'),
            TipoUtilizador(descricao_tipo='admin')
        ])
    if not EstadoUtilizador.query.first():
        db.session.add_all([
            EstadoUtilizador(descricao_estado='Ativo'),
            EstadoUtilizador(descricao_estado='Inativo')
        ])
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)