CREATE DATABASE meu_projeto;
USE meu_projeto;

CREATE TABLE produtos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    quantidade INT NOT NULL,
    preco REAL(10, 2) NOT NULL
);

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    senha VARCHAR(255) NOT NULL
);

CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(255),
    horario DATETIME,
    acao VARCHAR(255),
    produto TEXT
);

INSERT INTO usuarios (username, senha) VALUES ('admin', '1234');
INSERT INTO usuarios (username, senha) VALUES ('user', 'abcd');
