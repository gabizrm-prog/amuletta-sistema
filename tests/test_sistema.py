"""Testes do login e do CRUD de produtos. Rodar com: python -m unittest -v"""

import os
import tempfile
import unittest
from pathlib import Path


class BaseTeste(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        os.environ["AMULETTA_DB"] = str(Path(self.pasta.name) / "teste.db")
        from app import banco
        banco.inicializar()

    def tearDown(self):
        os.environ.pop("AMULETTA_DB", None)
        self.pasta.cleanup()


class TesteLogin(BaseTeste):
    def test_login_valido(self):
        from app import auth
        usuario = auth.autenticar("admin@amuletta.com", "admin123")
        self.assertEqual(usuario.perfil, "admin")

    def test_email_sem_diferenca_de_maiusculas(self):
        from app import auth
        self.assertEqual(auth.autenticar("  ADMIN@Amuletta.com ", "admin123").email, "admin@amuletta.com")

    def test_senha_errada(self):
        from app import auth
        with self.assertRaises(auth.ErroAutenticacao):
            auth.autenticar("admin@amuletta.com", "errada")

    def test_usuario_inexistente(self):
        from app import auth
        with self.assertRaises(auth.ErroAutenticacao):
            auth.autenticar("ninguem@amuletta.com", "admin123")

    def test_usuario_inativo(self):
        from app import auth, banco
        with banco.conectar() as c:
            c.execute("UPDATE usuarios SET ativo = 0 WHERE email = 'loja@amuletta.com'")
        with self.assertRaises(auth.ErroAutenticacao):
            auth.autenticar("loja@amuletta.com", "loja123")

    def test_senha_nao_fica_em_texto_puro(self):
        from app import banco
        with banco.conectar() as c:
            hashes = [l["senha_hash"] for l in c.execute("SELECT senha_hash FROM usuarios")]
        self.assertNotIn("admin123", hashes)

    def test_email_duplicado(self):
        from app import auth
        with self.assertRaises(ValueError):
            auth.cadastrar_usuario("Outro", "admin@amuletta.com", "123456")


class TesteProdutos(BaseTeste):
    def test_crud_completo(self):
        from app import produtos
        from app.produtos import Produto

        novo_id = produtos.incluir(Produto(nome="Tornozeleira Rubi", categoria_id=4, preco=49.9, estoque=7))
        self.assertEqual(produtos.buscar_por_id(novo_id).nome, "Tornozeleira Rubi")

        p = produtos.buscar_por_id(novo_id)
        p.preco, p.estoque = 54.9, 3
        produtos.alterar(p)
        self.assertEqual(produtos.buscar_por_id(novo_id).preco, 54.9)

        produtos.excluir(novo_id)
        self.assertIsNone(produtos.buscar_por_id(novo_id))

    def test_consulta_com_filtros(self):
        from app import produtos
        self.assertEqual(len(produtos.consultar()), 8)
        self.assertEqual({p["categoria"] for p in produtos.consultar(categoria_id=1)}, {"Colares"})
        self.assertEqual(len(produtos.consultar("argola")), 1)

    def test_validacoes(self):
        from app import produtos
        from app.produtos import Produto
        invalidos = [
            Produto(nome="", categoria_id=1, preco=10),
            Produto(nome="X", categoria_id=1, preco=0),
            Produto(nome="X", categoria_id=1, preco=10, estoque=-1),
            Produto(nome="X", categoria_id=999, preco=10),
        ]
        for produto in invalidos:
            with self.assertRaises(ValueError):
                produtos.incluir(produto)

    def test_excluir_inexistente(self):
        from app import produtos
        with self.assertRaises(ValueError):
            produtos.excluir(12345)


if __name__ == "__main__":
    unittest.main()
