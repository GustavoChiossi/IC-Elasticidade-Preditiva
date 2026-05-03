# implementacao do algoritmo usando:
# feedback de erro (AARIMA) + ARIMA + Box-Cox

from statsmodels.tsa.stattools import adfuller
#from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA
from scipy.special import inv_boxcox
import matplotlib.pyplot as plt
from scipy.stats import boxcox
import pandas as pd
import numpy as np

CAMINHO_CSV = "../../gerador_ram/com_timestamp/csv/neg-exp.csv"
DIVISAO_TREINO_TESTE = 0.8

P = 1
D = 2
Q = 2
ordem= (P, D, Q)

df = pd.read_csv(CAMINHO_CSV) # carrega dataset

# converte timestamp para datetime usando uma data base
dataBase = pd.Timestamp('2026-01-01')
df['dataHora'] = dataBase + pd.to_timedelta(df['timestamp_sec'], unit='s')
df = df.sort_values('dataHora') # ordena por tempo
df = df.set_index('dataHora')   # define indice temporal
serie = df['ram_mb']            # define serie temporal

# boxcox exige valores positivos
if (serie <= 0).any():
    serie = serie + abs(serie.min()) + 1

# funcao para aplicar boxcox manualmente em novos valores
def transformar_boxcox(valor, lmbda):
    if lmbda == 0:
        return np.log(valor)
    return (valor ** lmbda - 1) / lmbda

def arimaPlot(serie, nome, ordem):
    n = len(serie)
    indiceDivisao = int(n * DIVISAO_TREINO_TESTE)
    treino = serie.iloc[:indiceDivisao]
    teste = serie.iloc[indiceDivisao:]

    # aplica boxcox no treino e obtem lambda
    treinoBox, lambdaBox = boxcox(treino.values)

    historico = list(treino.values)  # original
    historicoBox = list(treinoBox)   # transformado

    # lista de previsoes transformadas
    previsoesBox = []

    # loop sequencial (aarima)
    for i in range(len(teste)):
        # treina modelo com historico atual
        modelo = ARIMA(historicoBox, order=ordem)
        modeloFit = modelo.fit(method_kwargs={'maxiter': 10000})

        # previsao de 1 passo a frente
        previsao = modeloFit.forecast(steps=1)[0]

        # transforma valor real usando mesmo lambda
        real = transformar_boxcox(teste.values[i], lambdaBox)

        # aplica feedback (aarima)
        if D == 0:
            # serie estacionaria
            if len(historico) >= 2:
                y_t  = historico[-1]
                y_t1 = historico[-2]
                ajuste = 0.5 * (y_t - y_t1)
            else:
                ajuste = 0

        else:
            # serie nao estacionaria
            if len(historico) >= 3:
                y_t  = historico[-1]
                y_t1 = historico[-2]
                y_t2 = historico[-3]
                ajuste = 0.5 * (y_t - 2*y_t1 + y_t2)
            else:
                ajuste = 0
            
        previsaoCorrigida = previsao + ajuste
        valorRealOriginal = teste.values[i]
        historico.append(valorRealOriginal)
        historicoBox.append(real)
        previsoesBox.append(previsaoCorrigida)
        
    # converte previsoes de volta para escala original
    previsoes = inv_boxcox(np.array(previsoesBox), lambdaBox)

    # cria serie com indice temporal correto
    seriePrevisao = pd.Series(previsoes, index=teste.index)

    # analisa metricas de erro
    #mae = mean_absolute_error(teste.to_numpy(), seriePrevisao.to_numpy())
    #rmse = np.sqrt(mean_squared_error(teste.to_numpy(), seriePrevisao.to_numpy()))
    #mape = np.mean(np.abs((teste.values - seriePrevisao.values) / teste.values)) * 100
    #print(f"{nome} - MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
    
    result = adfuller(serie)
    print(result[1])  # p-value
    
    plt.figure(figsize=(15, 5))
    plt.plot(treino.index, treino, label="treino", alpha=0.8)
    plt.plot(teste.index, teste, label="teste", alpha=0.8)
    plt.plot(seriePrevisao.index, seriePrevisao.values, label="previsao", ls='--', alpha=0.8)
    plt.title(f"{nome} com parametros {ordem}")
    plt.xlabel("tempo")
    plt.ylabel("ram (mb)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("resultado-aarima-boxcox.png", dpi=100)
    plt.close()

if __name__ == "__main__":
    arimaPlot(serie, "AARIMA + BOXCOX", ordem=ordem)