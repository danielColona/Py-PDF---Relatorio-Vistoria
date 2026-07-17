"""
Feedback de progresso simples no terminal (texto), sem dependências
externas. Usado enquanto o script lê/processa as fotos, que costuma
ser a parte mais demorada quando a pasta do site está em rede.
"""


class Progresso:

    def __init__(self, total, rotulo="Processando"):
        self.total = max(total, 1)
        self.rotulo = rotulo
        self.atual = 0
        self._ultimo_percentual = -1

    def avancar(self, incremento=1):
        self.atual += incremento
        percentual = int((self.atual / self.total) * 100)

        if percentual != self._ultimo_percentual:
            self._ultimo_percentual = percentual
            print(
                f"\r{self.rotulo}... {percentual:3d}% "
                f"({self.atual}/{self.total})",
                end="",
                flush=True,
            )

    def finalizar(self):
        print()