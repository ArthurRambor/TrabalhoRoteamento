import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

raiz = Path(__file__).resolve().parents[1]
arquivo = raiz / "resultados" / "metricas_algoritmo.csv"
saida = raiz / "graficos"
saida.mkdir(exist_ok=True)

with arquivo.open(newline="", encoding="utf-8") as f:
    dados = [linha for linha in csv.DictReader(f) if linha["ensaio"] in ("1", "2")]

ensaios = [d["ensaio"] for d in dados]

graficos = [
    ("troca_ms", "Tempo de comutação para rota alternativa", "Tempo (ms)", "tempo_troca.png"),
    ("restauracao_ms", "Tempo de restauração da rota principal", "Tempo (ms)", "tempo_restauracao.png"),
    ("latencia_media_ping_ms", "Latência média durante a rota alternativa", "Latência (ms)", "latencia_alternativa.png"),
    ("perda_ping_pct", "Perda de pacotes durante o teste de ping", "Perda (%)", "perda_pacotes.png"),
]

for coluna, titulo, eixo_y, nome in graficos:
    valores = [float(d[coluna]) for d in dados]
    plt.figure(figsize=(7, 4))
    plt.bar(ensaios, valores)
    plt.title(titulo)
    plt.xlabel("Ensaio")
    plt.ylabel(eixo_y)
    plt.xticks(ensaios, [f"Ensaio {n}" for n in ensaios])
    plt.tight_layout()
    plt.savefig(saida / nome, dpi=150)
    plt.close()

print("Gráficos gerados:")
for _, _, _, nome in graficos:
    print(saida / nome)
