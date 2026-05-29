from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
from scipy.special import inv_boxcox
from scipy.stats import boxcox
import matplotlib.pyplot as plt
import pmdarima as pm
import pandas as pd
import numpy as np
import warnings

DIVISAO_TREINO_TESTE = 0.8
#CAMINHO_CSV = "../../controlador/gerador_ram_final/resultados/pos-exp.csv"
CAMINHO_CSV = "../../controlador/gerador_ram_final/resultados/neg-exp.csv"

warnings.filterwarnings("ignore")
df = pd.read_csv(CAMINHO_CSV)
dataBase = pd.Timestamp("2026-01-01")
df["dataHora"] = dataBase + pd.to_timedelta(df["timestamp_sec"], unit="s")
df = df.sort_values("dataHora")
df = df.set_index("dataHora")
serie = df["ram_mb"]

def aplicar_boxcox(serie):
    offset = 0
    if serie.min() <= 0:
        offset = abs(serie.min()) + 1
        serie = serie + offset
    serieTransformada, lambdaBox = boxcox(serie.values)
    serieTransformada = pd.Series(serieTransformada, index=serie.index)
    return serieTransformada, lambdaBox, offset

def escolherArima(serie):
    modelo = pm.auto_arima(
        serie,
        start_p=0, start_q=0,
        max_p=15, max_q=15, max_d=3,
        d=None,
        seasonal=False,
        stepwise=False,
        trace=False,
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

def arimaPlot(serie, nome):
    n = len(serie)
    indiceDivisao = int(n * DIVISAO_TREINO_TESTE)
    treino = serie.iloc[:indiceDivisao]
    teste = serie.iloc[indiceDivisao:]
    treinoBox, lambdaBox, offset = aplicar_boxcox(treino)
    ordem = escolherArima(treinoBox)
    
    print(f"Ordem escolhida para {nome}: {ordem}")
    
    P, D, Q = ordem
    historico = list(treino.values)
    historicoBox = list(treinoBox.values)
    previsoesBox = []
    
    for i in range(len(teste)):
        modelo = ARIMA(historicoBox, order=ordem)
        modeloFit = modelo.fit(method_kwargs={"maxiter": 10000})
        previsao = modeloFit.forecast(steps=1)[0]
        valorReal = teste.values[i] + offset
        real = transformar_boxcox(valorReal, lambdaBox)
    
        if D == 0:
            if len(historicoBox) >= 2:
                ajuste = 0.5 * (historicoBox[-1] - historicoBox[-2])
            else:
                ajuste = 0
        else:
            if len(historicoBox) >= 3:
                ajuste = 0.5 * (historicoBox[-1] - 2*historicoBox[-2] + historicoBox[-3])
            else:
                ajuste = 0
        
        previsaoCorrigida = previsao + ajuste
        historico.append(teste.values[i])
        historicoBox.append(real)
        previsoesBox.append(previsaoCorrigida)
    
    previsoes = inv_boxcox(np.array(previsoesBox), lambdaBox) - offset
    seriePrevisao = pd.Series(previsoes, index=teste.index)
    
    plt.figure(figsize=(15,5))
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

if __name__ == "__main__":
    arimaPlot(serie, "AARIMA + BOXCOX")