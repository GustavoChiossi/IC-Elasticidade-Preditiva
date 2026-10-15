# Uso:
#   python3 modulos/graficos.py                         -> log mais recente
#   python3 modulos/graficos.py teste                   -> container "teste"
#   python3 modulos/graficos.py logs/teste/ts_xxx.jsonl -> arquivo específico

from metricas import encontrar_jsonl, carregar_eventos 
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import matplotlib, json, sys

matplotlib.use("Agg")
sys.path.insert(0, str(Path(__file__).resolve().parent))

def _carregar_coletas(eventos: list[dict]) -> pd.DataFrame:
    registros = [e for e in eventos if e["tipo"] == "coleta"]
    df = pd.DataFrame(registros)
    if df.empty:
        raise ValueError("Nenhum evento de coleta encontrado no arquivo.")
    df["ts"] = pd.to_datetime(df["ts"])
    return df.sort_values("ts").reset_index(drop=True)

def _estilo_padrao():
    plt.rcParams.update({
        "font.size": 22, "axes.titlesize": 24, "axes.labelsize": 22,
        "xtick.labelsize": 18, "ytick.labelsize": 18, "legend.fontsize": 18,
        "figure.figsize": (14, 9), "lines.linewidth": 3.0,
    })

def gerar_grafico_ram(df: pd.DataFrame, caminho_saida: Path, teto_mb: float | None = None) -> None:
    _estilo_padrao()
    fig, ax = plt.subplots(figsize=(14, 9))

    ax.step(df["ts"], df["limite_ram_mb"], label="Limite alocado", color="#2ca02c",
            linewidth=3.0, where="post", zorder=1)
    ax.plot(df["ts"], df["ram_mb"], label="Uso real (RAM)", color="#1f77b4",
            linewidth=3.0, marker="o", markersize=5, zorder=2)

    df_prev = df.dropna(subset=["previsao_ram_mb"])
    if not df_prev.empty:
        teto_clip = teto_mb if teto_mb else float(df["ram_mb"].max()) * 1.3
        previsao_clamped = df_prev["previsao_ram_mb"].clip(lower=0, upper=teto_clip)
        ax.plot(df_prev["ts"], previsao_clamped, label="Previsão (AARIMA)", color="#d62728",
                linewidth=2.5, linestyle="--", zorder=3)

    ax.set_xlabel("Tempo", fontweight="bold")
    ax.set_ylabel("Memória (MB)", fontweight="bold")
    ax.set_title("Elasticidade Vertical Preditiva — RAM", fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=":", linewidth=1.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(caminho_saida, dpi=200, bbox_inches="tight")
    plt.close(fig)

def gerar_grafico_cpu(df: pd.DataFrame, caminho_saida: Path, teto_pct: float | None = None) -> None:
    _estilo_padrao()
    fig, ax = plt.subplots(figsize=(14, 9))

    ax.step(df["ts"], df["limite_cpu_pct"], label="Limite alocado", color="#2ca02c",
            linewidth=3.0, where="post", zorder=1)
    ax.plot(df["ts"], df["cpu_percent"], label="Uso real (CPU)", color="#ff7f0e",
            linewidth=3.0, marker="o", markersize=5, zorder=2)

    df_prev = df.dropna(subset=["previsao_cpu_pct"])
    if not df_prev.empty:
        teto_clip = teto_pct if teto_pct else float(df["cpu_percent"].max()) * 1.3
        previsao_clamped = df_prev["previsao_cpu_pct"].clip(lower=0, upper=teto_clip)
        ax.plot(df_prev["ts"], previsao_clamped, label="Previsão (AARIMA)", color="#d62728",
                linewidth=2.5, linestyle="--", zorder=3)

    ax.set_xlabel("Tempo", fontweight="bold")
    ax.set_ylabel("CPU (%)", fontweight="bold")
    ax.set_title("Elasticidade Vertical Preditiva — CPU", fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.25), ncol=3, framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle=":", linewidth=1.2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate(rotation=30)
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(caminho_saida, dpi=200, bbox_inches="tight")
    plt.close(fig)

def main():
    argumento = sys.argv[1] if len(sys.argv) > 1 else None
    caminho = encontrar_jsonl(argumento)
    eventos = carregar_eventos(caminho)
    df = _carregar_coletas(eventos)

    gerados = []

    if "ram_mb" in df.columns and df["ram_mb"].notna().any():
        saida = caminho.parent / "grafico_ram.png"
        gerar_grafico_ram(df.dropna(subset=["ram_mb"]), saida)
        gerados.append(saida)

    if "cpu_percent" in df.columns and df["cpu_percent"].notna().any():
        saida = caminho.parent / "grafico_cpu.png"
        gerar_grafico_cpu(df.dropna(subset=["cpu_percent"]), saida)
        gerados.append(saida)

    if not gerados:
        print("Nenhuma métrica (RAM ou CPU) encontrada no arquivo para plotar.")
        sys.exit(1)

    for g in gerados:
        print(f"Gráfico salvo em '{g}'")

if __name__ == "__main__":
    main()