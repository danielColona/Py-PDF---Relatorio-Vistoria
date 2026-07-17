"""
Leitura do arquivo config.json e exposição dos dados como atributos simples.
"""

import json
from pathlib import Path


class Configuracao:

    def __init__(self, caminho_config="config.json"):

        caminho = Path(caminho_config)

        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {caminho.resolve()}"
            )

        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        self.empresa = dados["empresa"]
        self.cliente = dados["cliente"]
        self.site = dados["site"]
        self.cidade = dados["cidade"]
        self.estado = dados["estado"]

        self.pasta_site = Path(dados["pasta_site"])
        self.pasta_saida = Path(dados["saida"])

        self.titulo = dados["titulo"]
        self.logo = Path(dados["logo"])

    @property
    def prefixo_arquivos(self):
        """
        Prefixo usado nos nomes dos arquivos de foto (ex: 'HUB_SEA').
        Usado para limpar a legenda das fotos.
        """
        return self.site.replace(" ", "_")

    @property
    def arquivo_pdf(self):
        return self.pasta_saida / f"{self.site.replace(' ', '_')}.pdf"