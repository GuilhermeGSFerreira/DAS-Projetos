-- 1. Tabelas de Domínio (Lookups)
CREATE TABLE TIPO_UTILIZADOR (
    id INT PRIMARY KEY AUTO_INCREMENT,
    descricao_tipo VARCHAR(50) NOT NULL
);

CREATE TABLE ESTADO_UTILIZADOR (
    id INT PRIMARY KEY AUTO_INCREMENT,
    descricao_estado VARCHAR(50) NOT NULL
);

CREATE TABLE ESTADO_SIMULACAO (
    id INT PRIMARY KEY AUTO_INCREMENT,
    descricao_estado VARCHAR(50) NOT NULL
);

-- 2. Entidade de Utilizadores
CREATE TABLE UTILIZADORES (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    genero_id INT,
    data_nascimento DATE,
    img_url VARCHAR(255),
    fk_estado_utilizador_id INT,
    fk_tipo_utilizador_id INT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (fk_estado_utilizador_id) REFERENCES ESTADO_UTILIZADOR(id),
    FOREIGN KEY (fk_tipo_utilizador_id) REFERENCES TIPO_UTILIZADOR(id)
);

-- 3. Entidade de Simulações
CREATE TABLE SIMULACOES (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fk_utilizador_id INT,
    fk_estado_simulacao_id INT,
    nome VARCHAR(100),
    populacao_total INT,
    infetados_iniciais INT,
    taxa_contagio_beta DECIMAL(5,4),
    taxa_recuperacao_gamma DECIMAL(5,4),
    duracao_t INT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (fk_utilizador_id) REFERENCES UTILIZADORES(id),
    FOREIGN KEY (fk_estado_simulacao_id) REFERENCES ESTADO_SIMULACAO(id)
);

-- 4. Execuções e Passos (Rastreabilidade de Dados)
CREATE TABLE EXECUCOES_SIMULACAO (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fk_simulacao_id INT,
    numero_execucao INT,
    random_seed INT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fk_simulacao_id) REFERENCES SIMULACOES(id)
);

CREATE TABLE PASSOS_SIMULACAO (
    id INT PRIMARY KEY AUTO_INCREMENT,
    fk_execucao_id INT,
    passo_tempo INT,
    suscetiveis INT,
    infetados INT,
    recuperados INT,
    FOREIGN KEY (fk_execucao_id) REFERENCES EXECUCOES_SIMULACAO(id)
);