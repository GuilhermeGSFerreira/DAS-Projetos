from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# --- CONFIGURAÇÃO DA LIGAÇÃO ---
# mysql+pymysql://[UTILIZADOR]:[PASSWORD]@[HOST]/[NOME_DA_BD]
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password_aqui@localhost/simulador_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- MAPEAMENTO DAS TABELAS (EXATAMENTE COMO O TEU SQL) ---

class EstadoUtilizador(db.Model):
    __tablename__ = 'ESTADO_UTILIZADOR'
    id = db.Column(db.Integer, primary_key=True)
    descricao_estado = db.Column(db.String(50), nullable=False)

class Utilizadores(db.Model):
    __tablename__ = 'UTILIZADORES'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    fk_estado_utilizador_id = db.Column(db.Integer, db.ForeignKey('ESTADO_UTILIZADOR.id'))
    
    # Relacionamento para facilitar a contagem
    simulacoes = db.relationship('Simulacoes', backref='autor', lazy=True)

class Simulacoes(db.Model):
    __tablename__ = 'SIMULACOES'
    id = db.Column(db.Integer, primary_key=True)
    fk_utilizador_id = db.Column(db.Integer, db.ForeignKey('UTILIZADORES.id'))
    nome = db.Column(db.String(100))
    # Outros campos do teu SQL para garantir compatibilidade
    populacao_total = db.Column(db.Integer)
    taxa_contagio_beta = db.Column(db.Numeric(5,4))

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

if __name__ == '__main__':
    app.run(debug=True)