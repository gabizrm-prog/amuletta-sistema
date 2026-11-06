"""Interface grafica (Tkinter): tela de login e tela de cadastro de produtos."""

import tkinter as tk
from tkinter import messagebox, ttk

from app import auth, produtos
from app.produtos import Produto

VERMELHO = "#B3122E"
VERMELHO_ESCURO = "#8E0E24"
CREME = "#FBF6F2"
TEXTO = "#2B1A1D"
CINZA = "#7A6A6D"
FONTE = "Segoe UI"


def _estilizar(raiz: tk.Tk) -> None:
    estilo = ttk.Style(raiz)
    estilo.theme_use("clam")
    estilo.configure(".", font=(FONTE, 10), background=CREME, foreground=TEXTO)
    estilo.configure("TFrame", background=CREME)
    estilo.configure("Card.TFrame", background="white")
    estilo.configure("TLabel", background=CREME)
    estilo.configure("Card.TLabel", background="white")
    estilo.configure("Titulo.TLabel", font=(FONTE, 20, "bold"), foreground=VERMELHO, background=CREME)
    estilo.configure("Sub.TLabel", foreground=CINZA, background=CREME)
    estilo.configure("CardSub.TLabel", foreground=CINZA, background="white")
    estilo.configure("Erro.TLabel", foreground=VERMELHO, background="white")
    estilo.configure("TCheckbutton", background="white")
    estilo.configure("Primario.TButton", background=VERMELHO, foreground="white", padding=(14, 6),
                     font=(FONTE, 10, "bold"), borderwidth=0)
    estilo.map("Primario.TButton", background=[("active", VERMELHO_ESCURO), ("disabled", "#D9A3AD")])
    estilo.configure("TButton", padding=(12, 6))
    estilo.configure("Treeview", rowheight=26, fieldbackground="white", background="white")
    estilo.configure("Treeview.Heading", font=(FONTE, 10, "bold"), background="#F1E4E6", foreground=TEXTO)
    estilo.map("Treeview", background=[("selected", VERMELHO)], foreground=[("selected", "white")])


class TelaLogin(ttk.Frame):
    """Tela 1 - Login da equipe da loja."""

    def __init__(self, raiz: tk.Tk, ao_entrar):
        super().__init__(raiz, padding=40)
        self.ao_entrar = ao_entrar
        raiz.title("Amuletta - Login")

        ttk.Label(self, text="AMULETTA", style="Titulo.TLabel").pack()
        ttk.Label(self, text="Área administrativa da loja", style="Sub.TLabel").pack(pady=(0, 18))

        card = ttk.Frame(self, style="Card.TFrame", padding=24)
        card.pack(fill="x")
        ttk.Label(card, text="E-mail", style="Card.TLabel").pack(anchor="w")
        self.email = ttk.Entry(card, width=34)
        self.email.pack(fill="x", pady=(2, 10))
        ttk.Label(card, text="Senha", style="Card.TLabel").pack(anchor="w")
        self.senha = ttk.Entry(card, width=34, show="•")
        self.senha.pack(fill="x", pady=(2, 6))
        self.erro = ttk.Label(card, text="", style="Erro.TLabel")
        self.erro.pack(anchor="w", pady=(0, 8))
        ttk.Button(card, text="Entrar", style="Primario.TButton", command=self.entrar).pack(fill="x")

        ttk.Label(self, text="Usuário de teste: admin@amuletta.com / admin123", style="Sub.TLabel").pack(pady=(14, 0))

        self.email.focus()
        raiz.bind("<Return>", lambda _e: self.entrar())

    def entrar(self) -> None:
        try:
            usuario = auth.autenticar(self.email.get(), self.senha.get())
        except auth.ErroAutenticacao as erro:
            self.erro.configure(text=str(erro))
            self.senha.delete(0, "end")
            return
        self.master.unbind("<Return>")
        self.ao_entrar(usuario)


class TelaProdutos(ttk.Frame):
    """Tela 2 - Cadastro de produtos (incluir, consultar, alterar, excluir)."""

    COLUNAS = (("id", "Cód.", 50), ("nome", "Produto", 210), ("categoria", "Categoria", 100),
               ("preco", "Preço", 90), ("estoque", "Estoque", 70), ("lancamento", "Lançamento", 90))

    def __init__(self, raiz: tk.Tk, usuario: auth.Usuario, ao_sair):
        super().__init__(raiz, padding=20)
        self.usuario = usuario
        self.ao_sair = ao_sair
        self.selecionado: int | None = None
        self.categorias = produtos.listar_categorias()
        self.nomes_categorias = [c["nome"] for c in self.categorias]
        raiz.title("Amuletta - Cadastro de produtos")

        self._montar_topo()
        corpo = ttk.Frame(self)
        corpo.pack(fill="both", expand=True, pady=(14, 0))
        self._montar_lista(corpo)
        self._montar_formulario(corpo)
        self.atualizar_lista()

    # ---------- montagem ----------
    def _montar_topo(self) -> None:
        topo = ttk.Frame(self)
        topo.pack(fill="x")
        ttk.Label(topo, text="AMULETTA", style="Titulo.TLabel").pack(side="left")
        ttk.Label(topo, text="  Cadastro de produtos", style="Sub.TLabel").pack(side="left", pady=(8, 0))
        ttk.Button(topo, text="Sair", command=self.ao_sair).pack(side="right")
        perfil = "admin" if self.usuario.perfil == "admin" else "funcionário"
        ttk.Label(topo, text=f"{self.usuario.email} · {perfil}   ", style="Sub.TLabel").pack(side="right")

    def _montar_lista(self, pai) -> None:
        esquerda = ttk.Frame(pai)
        esquerda.pack(side="left", fill="both", expand=True)

        filtros = ttk.Frame(esquerda)
        filtros.pack(fill="x", pady=(0, 8))
        ttk.Label(filtros, text="Buscar:").pack(side="left")
        self.busca = tk.StringVar()
        self.busca.trace_add("write", lambda *_: self.atualizar_lista())
        ttk.Entry(filtros, textvariable=self.busca, width=24).pack(side="left", padx=(4, 12))
        ttk.Label(filtros, text="Categoria:").pack(side="left")
        self.filtro_categoria = ttk.Combobox(filtros, values=["Todas", *self.nomes_categorias],
                                             state="readonly", width=12)
        self.filtro_categoria.current(0)
        self.filtro_categoria.bind("<<ComboboxSelected>>", lambda _e: self.atualizar_lista())
        self.filtro_categoria.pack(side="left", padx=4)

        self.tabela = ttk.Treeview(esquerda, columns=[c[0] for c in self.COLUNAS], show="headings",
                                   selectmode="browse", height=14)
        for chave, titulo, largura in self.COLUNAS:
            self.tabela.heading(chave, text=titulo)
            alinhamento = "w" if chave in ("nome", "categoria") else "center"
            self.tabela.column(chave, width=largura, anchor=alinhamento)
        self.tabela.pack(fill="both", expand=True)
        self.tabela.bind("<<TreeviewSelect>>", self.ao_selecionar)
        self.total = ttk.Label(esquerda, text="", style="Sub.TLabel")
        self.total.pack(anchor="w", pady=(6, 0))

    def _montar_formulario(self, pai) -> None:
        form = ttk.Frame(pai, style="Card.TFrame", padding=18)
        form.pack(side="right", fill="y", padx=(16, 0))
        self.titulo_form = ttk.Label(form, text="Novo produto", style="Card.TLabel", font=(FONTE, 12, "bold"))
        self.titulo_form.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.campo_nome = self._campo(form, "Nome *", 1)
        ttk.Label(form, text="Categoria *", style="Card.TLabel").grid(row=3, column=0, sticky="w")
        self.campo_categoria = ttk.Combobox(form, values=self.nomes_categorias, state="readonly", width=30)
        self.campo_categoria.grid(row=4, column=0, columnspan=2, sticky="we", pady=(2, 8))
        self.campo_preco = self._campo(form, "Preço (R$) *", 5, largura=14, coluna=0)
        self.campo_estoque = self._campo(form, "Estoque *", 5, largura=14, coluna=1)
        ttk.Label(form, text="Descrição", style="Card.TLabel").grid(row=7, column=0, sticky="w")
        self.campo_descricao = tk.Text(form, width=32, height=4, font=(FONTE, 10), relief="solid", borderwidth=1, wrap="word")
        self.campo_descricao.grid(row=8, column=0, columnspan=2, sticky="we", pady=(2, 8))
        self.campo_lancamento = tk.BooleanVar()
        ttk.Checkbutton(form, text="Lançamento (selo NOVO no site)", variable=self.campo_lancamento,
                        style="TCheckbutton").grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 12))

        botoes = ttk.Frame(form, style="Card.TFrame")
        botoes.grid(row=10, column=0, columnspan=2, sticky="we")
        self.botao_salvar = ttk.Button(botoes, text="Incluir", style="Primario.TButton", command=self.salvar)
        self.botao_salvar.pack(side="left")
        ttk.Button(botoes, text="Limpar", command=self.limpar).pack(side="left", padx=6)
        self.botao_excluir = ttk.Button(botoes, text="Excluir", command=self.excluir, state="disabled")
        self.botao_excluir.pack(side="left")
        ttk.Label(form, text="* campos obrigatórios", style="CardSub.TLabel").grid(row=11, column=0, sticky="w", pady=(10, 0))

    def _campo(self, form, rotulo, linha, largura=32, coluna=0):
        ttk.Label(form, text=rotulo, style="Card.TLabel").grid(row=linha, column=coluna, sticky="w")
        entrada = ttk.Entry(form, width=largura)
        span = 2 if largura == 32 else 1
        entrada.grid(row=linha + 1, column=coluna, columnspan=span, sticky="we", pady=(2, 8),
                     padx=(0, 6) if coluna == 0 and span == 1 else 0)
        return entrada

    # ---------- acoes ----------
    def atualizar_lista(self) -> None:
        nome_cat = self.filtro_categoria.get()
        categoria_id = next((c["id"] for c in self.categorias if c["nome"] == nome_cat), None)
        self.tabela.delete(*self.tabela.get_children())
        lista = produtos.consultar(self.busca.get(), categoria_id)
        for p in lista:
            self.tabela.insert("", "end", iid=str(p["id"]), values=(
                p["id"], p["nome"], p["categoria"], _moeda(p["preco"]), p["estoque"],
                "Sim" if p["lancamento"] else "-"))
        self.total.configure(text=f"{len(lista)} produto(s)")

    def ao_selecionar(self, _evento=None) -> None:
        selecao = self.tabela.selection()
        if not selecao:
            return
        produto = produtos.buscar_por_id(int(selecao[0]))
        if produto is None:
            return
        self.selecionado = produto.id
        self._preencher(produto)
        self.titulo_form.configure(text=f"Editar produto #{produto.id}")
        self.botao_salvar.configure(text="Salvar alterações")
        self.botao_excluir.configure(state="normal")

    def _preencher(self, p: Produto) -> None:
        for campo, valor in ((self.campo_nome, p.nome), (self.campo_preco, f"{p.preco:.2f}".replace(".", ",")),
                             (self.campo_estoque, str(p.estoque))):
            campo.delete(0, "end")
            campo.insert(0, valor)
        self.campo_categoria.set(next(c["nome"] for c in self.categorias if c["id"] == p.categoria_id))
        self.campo_descricao.delete("1.0", "end")
        self.campo_descricao.insert("1.0", p.descricao)
        self.campo_lancamento.set(p.lancamento)

    def _ler_formulario(self) -> Produto:
        texto_preco = self.campo_preco.get().strip()
        if "," in texto_preco:  # formato brasileiro: 1.299,90
            texto_preco = texto_preco.replace(".", "").replace(",", ".")
        try:
            preco = float(texto_preco)
        except ValueError:
            raise ValueError("Preço inválido. Use por exemplo 129,90.") from None
        try:
            estoque = int(self.campo_estoque.get().strip())
        except ValueError:
            raise ValueError("Estoque deve ser um número inteiro.") from None
        categoria_id = next((c["id"] for c in self.categorias if c["nome"] == self.campo_categoria.get()), 0)
        return Produto(id=self.selecionado, nome=self.campo_nome.get(), categoria_id=categoria_id,
                       preco=preco, estoque=estoque, descricao=self.campo_descricao.get("1.0", "end"),
                       lancamento=self.campo_lancamento.get())

    def salvar(self) -> None:
        try:
            produto = self._ler_formulario()
            if self.selecionado is None:
                novo_id = produtos.incluir(produto)
                mensagem = f"Produto #{novo_id} incluído."
            else:
                produtos.alterar(produto)
                mensagem = f"Produto #{produto.id} alterado."
        except ValueError as erro:
            messagebox.showwarning("Verifique os dados", str(erro), parent=self)
            return
        self.limpar()
        self.atualizar_lista()
        messagebox.showinfo("Pronto", mensagem, parent=self)

    def excluir(self) -> None:
        if self.selecionado is None:
            return
        nome = self.campo_nome.get()
        if not messagebox.askyesno("Excluir produto", f"Excluir \"{nome}\"? Essa ação não pode ser desfeita.",
                                   parent=self):
            return
        try:
            produtos.excluir(self.selecionado)
        except ValueError as erro:
            messagebox.showerror("Erro", str(erro), parent=self)
        self.limpar()
        self.atualizar_lista()

    def limpar(self) -> None:
        self.selecionado = None
        for campo in (self.campo_nome, self.campo_preco, self.campo_estoque):
            campo.delete(0, "end")
        self.campo_categoria.set("")
        self.campo_descricao.delete("1.0", "end")
        self.campo_lancamento.set(False)
        self.titulo_form.configure(text="Novo produto")
        self.botao_salvar.configure(text="Incluir")
        self.botao_excluir.configure(state="disabled")
        self.tabela.selection_remove(*self.tabela.selection())


def _moeda(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class Aplicacao:
    """Controla a troca entre a tela de login e a tela de produtos."""

    def __init__(self):
        self.raiz = tk.Tk()
        self.raiz.configure(background=CREME)
        _estilizar(self.raiz)
        self.tela = None
        self.mostrar_login()

    def _trocar(self, nova_tela, geometria: str) -> None:
        if self.tela is not None:
            self.tela.destroy()
        self.tela = nova_tela
        self.tela.pack(fill="both", expand=True)
        self.raiz.geometry(geometria)

    def mostrar_login(self) -> None:
        self._trocar(TelaLogin(self.raiz, self.mostrar_produtos), "440x460")

    def mostrar_produtos(self, usuario: auth.Usuario) -> None:
        self._trocar(TelaProdutos(self.raiz, usuario, self.mostrar_login), "1180x620")

    def executar(self) -> None:
        self.raiz.mainloop()
