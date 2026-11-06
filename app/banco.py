"""Conexao com o SQLite, criacao das tabelas e dados iniciais."""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCHEMA = RAIZ / "schema.sql"
# O caminho do banco pode ser trocado pela variavel AMULETTA_DB (usado nos testes).
CAMINHO_PADRAO = RAIZ / "amuletta.db"

CATEGORIAS_INICIAIS = ["Colares", "Brincos", "Anéis", "Pulseiras", "Bolsas", "Cabelo"]

PRODUTOS_INICIAIS = [
    ("Colar Coração Rubi", "Corrente delicada com pingente de coração em tom rubi. Banhado a ouro 18k, 45 cm com extensor.", "Colares", 129.90, 12, 1),
    ("Brinco Gota Carmim", "Brinco pendente em formato de gota com acabamento carmim brilhante.", "Brincos", 89.90, 20, 0),
    ("Anel Solitário Rosé", "Anel solitário com pedra rosé lapidada. Aro fino ajustável, banhado a ouro rosé.", "Anéis", 99.90, 8, 1),
    ("Pulseira Pérolas Duo", "Pulseira com pérolas sintéticas em dois tamanhos. Fecho de rosca.", "Pulseiras", 79.90, 15, 0),
    ("Bolsa Mini Cereja", "Bolsa mini estruturada em vermelho cereja, com alça de mão e alça transversal.", "Bolsas", 219.90, 5, 0),
    ("Laço de Cabelo Carmim", "Laço de cetim carmim com presilha de metal.", "Cabelo", 59.90, 30, 1),
    ("Colar Amuleto Estrela", "Colar com pingente de estrela cravejado de zircônias.", "Colares", 149.90, 10, 0),
    ("Brinco Argola Fina", "Argola fina de 3 cm, banhada a ouro 18k.", "Brincos", 69.90, 25, 0),
]

USUARIO_ADMIN = ("Administrador", "admin@amuletta.com", "admin123", "admin")
USUARIO_FUNCIONARIO = ("Equipe Loja", "loja@amuletta.com", "loja123", "funcionario")


def caminho_banco() -> Path:
    return Path(os.environ.get("AMULETTA_DB", CAMINHO_PADRAO))


@contextmanager
def conectar() -> Iterator[sqlite3.Connection]:
    """Abre uma conexao (chaves estrangeiras ativas, linhas acessiveis por nome),
    faz commit se tudo der certo, rollback em caso de erro, e sempre fecha."""
    conexao = sqlite3.connect(caminho_banco())
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def criar_tabelas() -> None:
    with conectar() as conexao:
        conexao.executescript(SCHEMA.read_text(encoding="utf-8"))


def popular_dados_iniciais() -> None:
    """Insere categorias, produtos e usuarios de exemplo apenas se o banco estiver vazio."""
    from app import auth  # import local para evitar import circular

    with conectar() as conexao:
        if conexao.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
            conexao.executemany(
                "INSERT INTO categorias (nome) VALUES (?)",
                [(nome,) for nome in CATEGORIAS_INICIAIS],
            )
        if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
            ids = {linha["nome"]: linha["id"] for linha in conexao.execute("SELECT id, nome FROM categorias")}
            conexao.executemany(
                """INSERT INTO produtos (nome, descricao, categoria_id, preco, estoque, lancamento)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [(n, d, ids[c], p, e, l) for n, d, c, p, e, l in PRODUTOS_INICIAIS],
            )
        tem_usuario = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] > 0

    if not tem_usuario:
        for nome, email, senha, perfil in (USUARIO_ADMIN, USUARIO_FUNCIONARIO):
            auth.cadastrar_usuario(nome, email, senha, perfil)


def inicializar() -> None:
    criar_tabelas()
    popular_dados_iniciais()
