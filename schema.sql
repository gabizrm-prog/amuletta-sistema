-- Amuletta - Sistema administrativo
-- Script de criacao das tabelas (SQLite)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    senha_hash  TEXT    NOT NULL,
    salt        TEXT    NOT NULL,
    perfil      TEXT    NOT NULL DEFAULT 'funcionario'
                        CHECK (perfil IN ('admin', 'funcionario')),
    ativo       INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS categorias (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT    NOT NULL UNIQUE COLLATE NOCASE
);

CREATE TABLE IF NOT EXISTS produtos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT    NOT NULL,
    descricao      TEXT    NOT NULL DEFAULT '',
    categoria_id   INTEGER NOT NULL REFERENCES categorias (id),
    preco          REAL    NOT NULL CHECK (preco > 0),
    estoque        INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
    lancamento     INTEGER NOT NULL DEFAULT 0 CHECK (lancamento IN (0, 1)),
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos (categoria_id);
CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos (nome);
