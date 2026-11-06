"""Cria (ou recria com --recriar) o arquivo amuletta.db com as tabelas e os dados iniciais."""

import sys

from app import banco


def main() -> None:
    caminho = banco.caminho_banco()
    if "--recriar" in sys.argv and caminho.exists():
        caminho.unlink()
    banco.inicializar()
    print(f"Banco pronto em {caminho}")


if __name__ == "__main__":
    main()
