CREATE DATABASE IF NOT EXISTS estoque_recanto CHARACTER SET utf8mb4;
USE estoque_recanto;

CREATE TABLE IF NOT EXISTS produto (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(80) NOT NULL UNIQUE,
    estoque_minimo INT NOT NULL CHECK (estoque_minimo >= 0)
);

CREATE TABLE IF NOT EXISTS movimentacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    produto_id INT NOT NULL,
    tipo ENUM('entrada', 'retirada') NOT NULL,
    quantidade INT NOT NULL CHECK (quantidade > 0),
    data DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produto(id)
);
