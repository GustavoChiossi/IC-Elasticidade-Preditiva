# autoarima executa e usa os parametros automaticamente no AARIMA
# falta analisar e imprimir metricas

from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from scipy.special import inv_boxcox
from scipy.stats import boxcox
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
import pmdarima as pm

warnings.filterwarnings("ignore")

CAMINHO_CSV = "../../gerador_ram/com_timestamp/csv/partial-random.csv"
DIVISAO_TREINO_TESTE = 0.8

df = pd.read_csv(CAMINHO_CSV)
dataBase = pd.Timestamp("2026-01-01")
df["dataHora"] = dataBase + pd.to_timedelta(df["timestamp_sec"], unit="s")
df = df.sort_values("dataHora")
df = df.set_index("dataHora")
serie = df["ram_mb"]

def escolherArima(serie):
    modelo = pm.auto_arima(
        serie,
        start_p=0,
        start_q=0,
        max_p=15,
        max_q=15,
        max_d=3,
        d=None,
        seasonal=False,
        stepwise=False, # false: otimo global. true: otimo local
        trace=False,    # false: nao mostrar no terminal
        test="kpss",
        information_criterion="aic",
        error_action="ignore",
        suppress_warnings=True,
        with_intercept="auto"
    )
    return modelo.order

def transformar_boxcox(valor, lmbda):
    if lmbda == 0:
        return np.log(valor)
    return (valor ** lmbda - 1) / lmbda

def arimaPlot(serie, nome, ordem):
    P, D, Q = ordem
    n = len(serie)
    indiceDivisao = int(n * DIVISAO_TREINO_TESTE)
    treino = serie.iloc[:indiceDivisao]
    teste = serie.iloc[indiceDivisao:]
    treinoBox, lambdaBox = boxcox(treino.values)
    historico = list(treino.values)
    historicoBox = list(treinoBox)
    previsoesBox = []

    for i in range(len(teste)):
        modelo = ARIMA(historicoBox, order=ordem)
        modeloFit = modelo.fit(method_kwargs={"maxiter": 10000})
        previsao = modeloFit.forecast(steps=1)[0]
        real = transformar_boxcox(
            teste.values[i],
            lambdaBox
        )
        if D == 0:
            if len(historico) >= 2:
                y_t  = historico[-1]
                y_t1 = historico[-2]
                ajuste = 0.5 * (y_t - y_t1)
            else:
                ajuste = 0
        else:
            if len(historico) >= 3:
                y_t  = historico[-1]
                y_t1 = historico[-2]
                y_t2 = historico[-3]
                ajuste = 0.5 * (
                    y_t - 2*y_t1 + y_t2
                )
            else:
                ajuste = 0

        previsaoCorrigida = previsao + ajuste
        valorRealOriginal = teste.values[i]
        historico.append(valorRealOriginal)
        historicoBox.append(real)
        previsoesBox.append(previsaoCorrigida)

    previsoes = inv_boxcox(np.array(previsoesBox), lambdaBox)
    seriePrevisao = pd.Series(previsoes, index=teste.index)

    plt.figure(figsize=(15, 5))
    plt.plot(treino.index, treino, label="treino")
    plt.plot(teste.index, teste, label="teste")
    plt.plot(seriePrevisao.index, seriePrevisao.values, label="previsao", ls="--")
    plt.title(f"{nome} - ordem {ordem}")
    plt.xlabel("tempo")
    plt.ylabel("ram (mb)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("resultado-aarima-boxcox.png", dpi=100)
    plt.close()

# metricas

if __name__ == "__main__":
    ordem = escolherArima(serie)
    print("\nOrdem escolhida:", ordem)
    #print("\nMétricas:")
    arimaPlot(serie, "AARIMA + BOXCOX", ordem)