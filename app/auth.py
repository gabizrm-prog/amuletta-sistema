"""Modulo de login: cadastro de usuarios e validacao de credenciais.

As senhas nunca sao gravadas em texto puro: guardamos um hash PBKDF2-SHA256
com um salt aleatorio por usuario.
"""

import hashlib
import hmac
import re
import secrets
import sqlite3
from dataclasses import dataclass

from app.banco import conectar

ITERACOES = 200_000
EMAIL_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ErroAutenticacao(Exception):
    """Credenciais invalidas ou usuario inativo."""


@dataclass
class Usuario:
    id: int
    nome: str
    email: str
    perfil: str


def gerar_hash(senha: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt), ITERACOES).hex()


def cadastrar_usuario(nome: str, email: str, senha: str, perfil: str = "funcionario") -> int:
    nome, email = nome.strip(), email.strip().lower()
    if not nome:
        raise ValueError("Informe o nome.")
    if not EMAIL_VALIDO.match(email):
        raise ValueError("E-mail inválido.")
    if len(senha) < 6:
        raise ValueError("A senha precisa ter pelo menos 6 caracteres.")
    if perfil not in ("admin", "funcionario"):
        raise ValueError("Perfil inválido.")

    salt = secrets.token_hex(16)
    try:
        with conectar() as conexao:
            cursor = conexao.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, salt, perfil) VALUES (?, ?, ?, ?, ?)",
                (nome, email, gerar_hash(senha, salt), salt, perfil),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("Já existe um usuário com esse e-mail.") from None


def autenticar(email: str, senha: str) -> Usuario:
    """Retorna o usuario se e-mail e senha conferem; senao levanta ErroAutenticacao."""
    email = email.strip().lower()
    if not email or not senha:
        raise ErroAutenticacao("Preencha e-mail e senha.")

    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT id, nome, email, senha_hash, salt, perfil, ativo FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()

    # Mesma mensagem para e-mail inexistente e senha errada (nao revela quais e-mails existem).
    if linha is None or not hmac.compare_digest(gerar_hash(senha, linha["salt"]), linha["senha_hash"]):
        raise ErroAutenticacao("E-mail ou senha incorretos.")
    if not linha["ativo"]:
        raise ErroAutenticacao("Usuário desativado. Procure o administrador.")

    return Usuario(linha["id"], linha["nome"], linha["email"], linha["perfil"])
