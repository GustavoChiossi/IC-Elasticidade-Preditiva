# Uso:
#   python3 modulos/metricas.py                         -> log mais recente (qualquer container)
#   python3 modulos/metricas.py teste                   -> log mais recente do container "teste"
#   python3 modulos/metricas.py logs/teste/ts_xxx.jsonl -> arquivo específico

from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import json, sys

DIR_BASE = Path(__file__).resolve().parent.parent
DIR_LOGS = DIR_BASE / "logs"

def encontrar_jsonl(argumento: str | None) -> Path:
    if argumento is None:
        arquivos = sorted(DIR_LOGS.glob("*/ts_*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not arquivos:
            raise FileNotFoundError(f"Nenhum log ts_*.jsonl encontrado em '{DIR_LOGS}/<container>/'")
        return arquivos[-1]

    caminho = Path(argumento)
    if caminho.exists() and caminho.is_file():
        return caminho

    # Trata o argumento como nome de container
    arquivos = sorted((DIR_LOGS / argumento).glob("ts_*.jsonl"), key=lambda p: p.stat().st_mtime) \
        if (DIR_LOGS / argumento).is_dir() else []
    if not arquivos:
        raise FileNotFoundError(f"Nenhum log encontrado para '{argumento}' (nem como arquivo, nem como container).")
    return arquivos[-1]

def carregar_eventos(caminho: Path) -> list[dict]:
    eventos = []
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha:
                eventos.append(json.loads(linha))
    return eventos

def montar_dataframes(eventos: list[dict]):
    coletas = [e for e in eventos if e["tipo"] == "coleta"]
    escalas = [e for e in eventos if e["tipo"] == "escala"]
    recalib = [e for e in eventos if e["tipo"] == "recalibracao"]

    df_coletas = pd.DataFrame(coletas)
    if not df_coletas.empty:
        df_coletas["ts"] = pd.to_datetime(df_coletas["ts"])
        df_coletas = df_coletas.sort_values("ts").reset_index(drop=True)

    df_escalas = pd.DataFrame(escalas)
    if not df_escalas.empty:
        df_escalas["ts"] = pd.to_datetime(df_escalas["ts"])
        df_escalas = df_escalas.sort_values("ts").reset_index(drop=True)

    df_recalib = pd.DataFrame(recalib)
    if not df_recalib.empty:
        df_recalib["ts"] = pd.to_datetime(df_recalib["ts"])
        df_recalib = df_recalib.sort_values("ts").reset_index(drop=True)

    return df_coletas, df_escalas, df_recalib

def calcular_erro_previsao(df: pd.DataFrame, col_real: str, col_previsao: str,
                            limiar_outlier: float) -> dict:
    df = df.dropna(subset=[col_previsao, col_real]).reset_index(drop=True)
    if len(df) < 2:
        return {"smape": None, "mae": None, "rmse": None, "mediana_erro_abs": None,
                "n_amostras": 0, "n_outliers": 0,
                "smape_robusto": None, "mae_robusto": None, "rmse_robusto": None}

    previsto = df[col_previsao].values[:-1]
    real = df[col_real].values[1:]

    def _metricas(p, r):
        erro = r - p
        mae = float(np.mean(np.abs(erro)))
        rmse = float(np.sqrt(np.mean(erro ** 2)))
        mediana = float(np.median(np.abs(erro)))
        denom = np.abs(r) + np.abs(p)
        denom[denom == 0] = 1e-9
        smape = float(np.mean(2 * np.abs(erro) / denom) * 100)
        return smape, mae, rmse, mediana

    smape, mae, rmse, mediana = _metricas(previsto, real)

    mask_ok = previsto <= limiar_outlier
    n_outliers = int((~mask_ok).sum())
    if mask_ok.sum() >= 2:
        smape_r, mae_r, rmse_r, _ = _metricas(previsto[mask_ok], real[mask_ok])
    else:
        smape_r = mae_r = rmse_r = None

    return {
        "smape": round(smape, 3), "mae": round(mae, 3), "rmse": round(rmse, 3),
        "mediana_erro_abs": round(mediana, 3), "n_amostras": len(previsto), "n_outliers": n_outliers,
        "smape_robusto": round(smape_r, 3) if smape_r is not None else None,
        "mae_robusto": round(mae_r, 3) if mae_r is not None else None,
        "rmse_robusto": round(rmse_r, 3) if rmse_r is not None else None,
    }

def calcular_provisionamento(df: pd.DataFrame, col_real: str, col_limite: str) -> dict:
    df = df.dropna(subset=[col_real, col_limite])
    if df.empty:
        return {"over_medio": None, "ciclos_over": 0, "under_medio": None, "ciclos_under": 0, "total_ciclos": 0}

    total = len(df)
    over = df[df[col_real] < df[col_limite]]
    diffs_over = (over[col_limite] - over[col_real])
    over_medio = float(diffs_over.mean()) if not diffs_over.empty else 0.0

    under = df[df[col_real] > df[col_limite]]
    diffs_under = (under[col_real] - under[col_limite])
    under_medio = float(diffs_under.mean()) if not diffs_under.empty else 0.0

    return {
        "over_medio": round(over_medio, 2), "ciclos_over": len(over),
        "under_medio": round(under_medio, 2), "ciclos_under": len(under),
        "total_ciclos": total,
    }

def calcular_latencia(df_escalas: pd.DataFrame, recurso: str) -> dict:
    if df_escalas.empty or "recurso" not in df_escalas.columns:
        return {"media_ms": None, "min_ms": None, "max_ms": None, "n_escalas": 0}
    sub = df_escalas[df_escalas["recurso"] == recurso]
    lat = sub["latencia_docker_ms"].dropna() if "latencia_docker_ms" in sub.columns else pd.Series(dtype=float)
    if lat.empty:
        return {"media_ms": None, "min_ms": None, "max_ms": None, "n_escalas": 0}
    return {"media_ms": round(float(lat.mean()), 2), "min_ms": round(float(lat.min()), 2),
            "max_ms": round(float(lat.max()), 2), "n_escalas": len(lat)}

def calcular_recalibracoes(df_recalib: pd.DataFrame, recurso: str) -> dict:
    if df_recalib.empty or "recurso" not in df_recalib.columns:
        return {"total": 0, "intervalo_medio_s": None}
    sub = df_recalib[df_recalib["recurso"] == recurso]
    n = len(sub)
    if n < 2:
        return {"total": n, "intervalo_medio_s": None}
    intervalos = sub["ts"].diff().dropna().dt.total_seconds()
    return {"total": n, "intervalo_medio_s": round(float(intervalos.mean()), 1)}

def formatar_secao(nome_recurso: str, unidade: str, erro: dict, prov: dict, lat: dict, recalib: dict) -> list[str]:
    linhas = [f"\n{'-' * 68}", f"  [ {nome_recurso.upper()} ]", "-" * 68]

    linhas.append("\n  Erro de previsão:")
    if erro["smape"] is not None:
        linhas.append(f"    -- Todas as amostras ({erro['n_amostras']} pares previsão→real) --")
        linhas.append(f"    SMAPE           : {erro['smape']:.3f} %")
        linhas.append(f"    MAE             : {erro['mae']:.3f} {unidade}")
        linhas.append(f"    RMSE            : {erro['rmse']:.3f} {unidade}")
        linhas.append(f"    Mediana erro abs: {erro['mediana_erro_abs']:.3f} {unidade}")
        if erro["n_outliers"] > 0:
            linhas.append(f"\n    ATENÇÃO: {erro['n_outliers']} previsão(ões) outlier detectada(s).")
            if erro["smape_robusto"] is not None:
                linhas.append(f"    -- Robustas (outliers excluídos) --")
                linhas.append(f"    SMAPE : {erro['smape_robusto']:.3f} %  "
                              f"MAE: {erro['mae_robusto']:.3f} {unidade}  RMSE: {erro['rmse_robusto']:.3f} {unidade}")
    else:
        linhas.append("    Dados insuficientes para calcular.")

    linhas.append("\n  Provisionamento de recursos:")
    if prov["over_medio"] is not None:
        linhas.append(f"    Over-provisioning médio : {prov['over_medio']:.2f} {unidade} "
                      f"(em {prov['ciclos_over']} de {prov['total_ciclos']} ciclos)")
        linhas.append(f"    Under-provisioning médio: {prov['under_medio']:.2f} {unidade} "
                      f"(em {prov['ciclos_under']} de {prov['total_ciclos']} ciclos)")
    else:
        linhas.append("    Dados insuficientes para calcular.")

    linhas.append("\n  Latência de escala (Docker):")
    if lat["media_ms"] is not None:
        linhas.append(f"    Média: {lat['media_ms']:.2f}ms  Mín: {lat['min_ms']:.2f}ms  "
                      f"Máx: {lat['max_ms']:.2f}ms  (n={lat['n_escalas']})")
    else:
        linhas.append("    Nenhuma ação de escala registrada.")

    linhas.append("\n  Recalibrações do modelo:")
    linhas.append(f"    Total: {recalib['total']}"
                  + (f"  Intervalo médio: {recalib['intervalo_medio_s']:.1f}s" if recalib["intervalo_medio_s"] else ""))

    return linhas

def main():
    argumento = sys.argv[1] if len(sys.argv) > 1 else None
    caminho = encontrar_jsonl(argumento)

    eventos = carregar_eventos(caminho)
    df_coletas, df_escalas, df_recalib = montar_dataframes(eventos)

    if df_coletas.empty:
        print("Nenhum evento de coleta encontrado no arquivo.")
        sys.exit(1)

    duracao_s = (df_coletas["ts"].max() - df_coletas["ts"].min()).total_seconds()
    tem_ram = "ram_mb" in df_coletas.columns and df_coletas["ram_mb"].notna().any()
    tem_cpu = "cpu_percent" in df_coletas.columns and df_coletas["cpu_percent"].notna().any()

    linhas = [
        "=" * 68,
        "  RELATÓRIO DE MÉTRICAS — CONTROLADOR PREDITIVO DE ELASTICIDADE",
        "=" * 68,
        f"  Arquivo de origem : {caminho}",
        f"  Gerado em         : {datetime.now().isoformat(timespec='seconds')}",
        f"  Duração da sessão : {duracao_s:.1f}s",
    ]

    if tem_ram:
        erro = calcular_erro_previsao(df_coletas, "ram_mb", "previsao_ram_mb", limiar_outlier=2000)
        prov = calcular_provisionamento(df_coletas, "ram_mb", "limite_ram_mb")
        lat = calcular_latencia(df_escalas, "ram")
        recalib = calcular_recalibracoes(df_recalib, "ram")
        linhas += formatar_secao("Memória RAM", "MB", erro, prov, lat, recalib)

    if tem_cpu:
        erro = calcular_erro_previsao(df_coletas, "cpu_percent", "previsao_cpu_pct", limiar_outlier=200)
        prov = calcular_provisionamento(df_coletas, "cpu_percent", "limite_cpu_pct")
        lat = calcular_latencia(df_escalas, "cpu")
        recalib = calcular_recalibracoes(df_recalib, "cpu")
        linhas += formatar_secao("CPU", "%", erro, prov, lat, recalib)

    linhas.append("\n" + "=" * 68)
    relatorio = "\n".join(linhas)
    print(relatorio)

    arquivo_saida = caminho.parent / "saida_metricas.txt"
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(relatorio + "\n")
    print(f"\nMétricas gravadas em '{arquivo_saida}'")

if __name__ == "__main__":
    main()