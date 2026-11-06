"""Cadastro base de produtos: inclusao, consulta, alteracao e exclusao (CRUD)."""

from dataclasses import dataclass

from app.banco import conectar


@dataclass
class Produto:
    nome: str
    categoria_id: int
    preco: float
    estoque: int = 0
    descricao: str = ""
    lancamento: bool = False
    id: int | None = None


def _validar(produto: Produto) -> None:
    if not produto.nome.strip():
        raise ValueError("Informe o nome do produto.")
    if len(produto.nome.strip()) > 80:
        raise ValueError("O nome pode ter no máximo 80 caracteres.")
    if produto.preco is None or produto.preco <= 0:
        raise ValueError("O preço precisa ser maior que zero.")
    if produto.estoque is None or produto.estoque < 0:
        raise ValueError("O estoque não pode ser negativo.")
    with conectar() as conexao:
        if conexao.execute("SELECT 1 FROM categorias WHERE id = ?", (produto.categoria_id,)).fetchone() is None:
            raise ValueError("Selecione uma categoria válida.")


def _de_linha(linha) -> Produto:
    return Produto(
        id=linha["id"],
        nome=linha["nome"],
        descricao=linha["descricao"],
        categoria_id=linha["categoria_id"],
        preco=linha["preco"],
        estoque=linha["estoque"],
        lancamento=bool(linha["lancamento"]),
    )


# ---------- Create ----------
def incluir(produto: Produto) -> int:
    _validar(produto)
    with conectar() as conexao:
        cursor = conexao.execute(
            """INSERT INTO produtos (nome, descricao, categoria_id, preco, estoque, lancamento)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (produto.nome.strip(), produto.descricao.strip(), produto.categoria_id,
             round(produto.preco, 2), produto.estoque, int(produto.lancamento)),
        )
        return cursor.lastrowid


# ---------- Read ----------
def buscar_por_id(produto_id: int) -> Produto | None:
    with conectar() as conexao:
        linha = conexao.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    return _de_linha(linha) if linha else None


def consultar(texto: str = "", categoria_id: int | None = None) -> list[dict]:
    """Lista produtos com o nome da categoria, filtrando por texto (nome/descricao) e categoria."""
    sql = """SELECT p.id, p.nome, p.descricao, p.preco, p.estoque, p.lancamento,
                    p.categoria_id, c.nome AS categoria, p.atualizado_em
             FROM produtos p JOIN categorias c ON c.id = p.categoria_id
             WHERE (p.nome LIKE ? OR p.descricao LIKE ?)"""
    termo = f"%{texto.strip()}%"
    parametros: list = [termo, termo]
    if categoria_id is not None:
        sql += " AND p.categoria_id = ?"
        parametros.append(categoria_id)
    sql += " ORDER BY p.nome COLLATE NOCASE"
    with conectar() as conexao:
        return [dict(linha) for linha in conexao.execute(sql, parametros)]


# ---------- Update ----------
def alterar(produto: Produto) -> None:
    if produto.id is None:
        raise ValueError("Selecione um produto para alterar.")
    _validar(produto)
    with conectar() as conexao:
        cursor = conexao.execute(
            """UPDATE produtos
               SET nome = ?, descricao = ?, categoria_id = ?, preco = ?, estoque = ?, lancamento = ?,
                   atualizado_em = datetime('now', 'localtime')
               WHERE id = ?""",
            (produto.nome.strip(), produto.descricao.strip(), produto.categoria_id,
             round(produto.preco, 2), produto.estoque, int(produto.lancamento), produto.id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Produto não encontrado.")


# ---------- Delete ----------
def excluir(produto_id: int) -> None:
    with conectar() as conexao:
        cursor = conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        if cursor.rowcount == 0:
            raise ValueError("Produto não encontrado.")


def listar_categorias() -> list[dict]:
    with conectar() as conexao:
        return [dict(linha) for linha in conexao.execute("SELECT id, nome FROM categorias ORDER BY id")]
