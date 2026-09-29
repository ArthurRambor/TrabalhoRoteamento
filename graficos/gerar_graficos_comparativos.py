import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

raiz = Path(__file__).resolve().parents[1]
arquivo = raiz / "resultados" / "comparacao_metricas.csv"
saida = raiz / "graficos"
saida.mkdir(exist_ok=True)

with arquivo.open(newline="", encoding="utf-8") as f:
    dados = list(csv.DictReader(f))

def salvar_barras(coluna, titulo, eixo_y, nome, rotulo):
    linhas = [
        d for d in dados
        if d[coluna].strip() not in ("", "NA", "N/A")
    ]
    nomes = [d["cenario"] for d in linhas]
    valores = [float(d[coluna]) for d in linhas]

    plt.figure(figsize=(7, 4))
    barras = plt.bar(nomes, valores)
    plt.title(titulo)
    plt.xlabel("Cenário")
    plt.ylabel(eixo_y)

    for barra, valor in zip(barras, valores):
        plt.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height(),
            rotulo.format(valor),
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(saida / nome, dpi=150)
    plt.close()
    print(f"Gerado: {saida / nome}")

salvar_barras(
    "rotas_FIB_R1",
    "Rotas instaladas na FIB do R1",
    "Quantidade de rotas",
    "comparacao_rotas_fib.png",
    "{:.0f}"
)

salvar_barras(
    "pacotes_controle_R1_eth1_60s",
    "Pacotes de controle observados em 60 s",
    "Pacotes",
    "comparacao_pacotes_controle.png",
    "{:.0f}"
)

salvar_barras(
    "bytes_protocolo_R1_eth1_60s",
    "Bytes de protocolo observados em 60 s",
    "Bytes",
    "comparacao_bytes_controle.png",
    "{:.0f}"
)

salvar_barras(
    "taxa_bit_s",
    "Taxa média de tráfego de controle observada",
    "bit/s",
    "comparacao_taxa_controle.png",
    "{:.2f}"
)

salvar_barras(
    "tempo_troca_ms",
    "Tempo médio de troca para rota alternativa",
    "Tempo (ms)",
    "comparacao_tempo_troca.png",
    "{:.1f}"
)

salvar_barras(
    "tempo_restauracao_ms",
    "Tempo médio de restauração da rota principal",
    "Tempo (ms)",
    "comparacao_tempo_restauracao.png",
    "{:.1f}"
)

print("Concluído.")
