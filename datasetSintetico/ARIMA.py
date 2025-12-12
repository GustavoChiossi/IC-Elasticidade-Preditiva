import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

# dataset
df = pd.read_csv("dataset.csv", parse_dates=["timestamp"])
df.set_index("timestamp", inplace=True)  # garante que o index é datetime
df.index = pd.to_datetime(df.index)
df = df.asfreq('5min') # freq de 5 minutos

# ARIMA + plot
def arima_plot(series, name, order):
    n = len(series)
    split = int(n * 0.8) # 80% treino, 20% teste
    
    train = series[:split]
    test = series[split:]
    
    # treino
    model = ARIMA(train, order=order)
    model_fit = model.fit(method_kwargs={"maxiter":500}) # maxiter aumentado para garantir convergencia
    
    # previsao
    forecast = model_fit.forecast(steps=len(test))
    
    # plot
    plt.figure(figsize=(15,5))
    plt.plot(train.index, train, label="Treino", color="blue")
    plt.plot(test.index, test, label="Teste", color="orange")
    plt.plot(test.index, forecast, label="Previsão ARIMA", color="green")
    plt.title(f"{name} - ARIMA{order}")
    plt.xlabel("Timestamp")
    plt.ylabel(f"{name} (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# exec
arima_plot(df["cpu"], "CPU", order=(2,0,2))
arima_plot(df["ram"], "RAM", order=(2,0,2))