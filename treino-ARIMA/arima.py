import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

CAMINHO_CSV = "dataset-gerador.csv"

# carrega dataset
df = pd.read_csv(CAMINHO_CSV)
df = df.sort_values("step")

series = df["ram"]
steps = df["step"]

def arima_plot(series, steps, name, order):
    n = len(series)
    split = int(n * 0.8)  # 80% treino, 20% teste

    # separa treino e teste
    train = series.iloc[:split]
    test = series.iloc[split:]

    train_steps = steps.iloc[:split]
    test_steps = steps.iloc[split:]

    # treino do modelo
    model = ARIMA(train, order=order)
    model_fit = model.fit()

    # previsão para o teste
    forecast = model_fit.forecast(steps=len(test))

    # transforma forecast em Series com índice do teste
    forecast_series = pd.Series(forecast, index=test_steps)

    # plot
    plt.figure(figsize=(15,5))
    plt.plot(train_steps, train, label="Treino")
    plt.plot(test_steps, test, label="Teste")
    plt.plot(forecast_series, label="Previsão ARIMA", color="red")

    plt.title(f"{name} - ARIMA{order}")
    plt.xlabel("step")
    plt.ylabel("Memória (MB)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# EXECUÇÃO
arima_plot(series, steps, "RAM", order=(4,0,0))
