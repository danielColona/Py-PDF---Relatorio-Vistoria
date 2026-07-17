"""
Gerador de Relatório Fotográfico
"""

from util.config import Configuracao
from modelos.relatorio import RelatorioPDF


def main():

    config = Configuracao()

    print("=" * 60)
    print(config.titulo)
    print("=" * 60)

    relatorio = RelatorioPDF(config)
    relatorio.gerar()


if __name__ == "__main__":
    main()