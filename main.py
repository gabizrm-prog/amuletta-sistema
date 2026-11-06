"""Ponto de entrada: cria o banco (se preciso) e abre o sistema."""

from app import banco
from app.telas import Aplicacao


def main() -> None:
    banco.inicializar()
    Aplicacao().executar()


if __name__ == "__main__":
    main()
