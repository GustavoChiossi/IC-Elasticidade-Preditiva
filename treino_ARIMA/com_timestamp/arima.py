# implementacao do ARIMA

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_absolute_error, mean_squared_error

# (alterar o caminho caso necessario)
CAMINHO_CSV = "../../gerador_ram/com_timestamp/csv-timestamp/dataset-gerador-timestamp_wave.csv"
df = pd.read_csv(CAMINHO_CSV) # carrega dataset
 
# converte timestamp para datetime usando data base
dataBase = pd.Timestamp('2026-01-01')
df['dataHora'] = dataBase + pd.to_timedelta(df['timestamp_sec'], unit='s')
df = df.sort_values('dataHora') # ordena por tempo
df = df.set_index('dataHora')   # define indice temporal
serie = df['ram_mb']            # define serie temporal

def arimaPlot(serie, nome, ordem):
    n = len(serie)
    indiceDivisao = int(n * 0.8) 

    # divsao treino/teste
    treino = serie.iloc[:indiceDivisao]
    teste = serie.iloc[indiceDivisao:]

    # treina modelo e faz previsao
    modelo = ARIMA(treino.values, order=ordem)
    modeloFit = modelo.fit()
    previsao = modeloFit.forecast(steps=len(teste))

    # cria indice da previsao
    ultimoTreino = treino.index[-1]
    indicePrevisao = pd.date_range(
        start=ultimoTreino + pd.Timedelta(seconds=1),
        periods=len(teste),
        freq='s'
    )

    seriePrevisao = pd.Series(previsao, index=indicePrevisao)

    # analisa metricas de erro
    mae = mean_absolute_error(teste, seriePrevisao)
    rmse = np.sqrt(mean_squared_error(teste, seriePrevisao))
    mape = np.mean(np.abs((teste.values - seriePrevisao.values) / teste.values)) * 100
    print(f"{nome} - MAE: {mae:.2f}, RMSE: {rmse:.2f}, MAPE: {mape:.2f}%")
    
    # plot
    plt.figure(figsize=(15, 5))
    plt.plot(treino.index, treino, label="treino", alpha=0.8)
    plt.plot(teste.index, teste, label="teste", alpha=0.8)
    plt.plot(seriePrevisao.index, seriePrevisao.values, label="previsao", ls='--', alpha=0.8)
    plt.title(f"{nome} com parâmetros {ordem}")
    plt.xlabel("tempo")
    plt.ylabel("ram (mb)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.savefig("resultado-arima-timestamp.png", dpi=100)
    plt.close()

if __name__ == "__main__":
    arimaPlot(serie, "ARIMA", ordem=(0, 1, 1))