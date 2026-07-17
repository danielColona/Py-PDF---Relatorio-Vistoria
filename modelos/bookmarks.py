"""
Marcadores do PDF (o painel de navegação lateral que o leitor de PDF
exibe). Cada seção de pasta vira um item clicável nesse painel,
respeitando a hierarquia de pastas — e pode ser expandido/recolhido
como uma árvore de pastas, igual o Explorer.
"""

# Níveis (0-indexados) que já vêm abertos ao abrir o PDF.
# 0 = categorias (Segurança, Zeladoria, Organização, Infra)
# 1 = Contêiner / Fachada / Porta Acesso / Ambiente...
# A partir do nível 2 (Fila, Rack) vem fechado, para não poluir.
NIVEIS_ABERTOS_POR_PADRAO = {0, 1}


def registrar_marcador(canvas, chave, titulo, nivel):
    """
    chave: identificador único da página/seção (ex: 'sec_12')
    titulo: texto exibido no painel de marcadores
    nivel: 0 = raiz, 1 = filho, 2 = neto... (hierarquia do outline)
    """
    canvas.bookmarkPage(chave)
    aberto = nivel in NIVEIS_ABERTOS_POR_PADRAO
    canvas.addOutlineEntry(titulo, chave, level=nivel, closed=not aberto)