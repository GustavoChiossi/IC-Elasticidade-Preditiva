import warnings
import pmdarima as pm
import pandas as pd

warnings.filterwarnings("ignore")

csv_path = "dataset.csv"
df = pd.read_csv(csv_path)

cpu_series = df["cpu"] 
ram_series = df["ram"]

def escolher_arima(nome, serie, max_p=12, max_q=3):
    print(f"\n\n=========== {nome} ===========\n")

    modelo = pm.auto_arima(
        serie,
        start_p=0, start_q=0,
        max_p=max_p, max_q=max_q,
        d=0,  # ja é stationary
        seasonal=False,
        trace=True,
        stepwise=True,
        information_criterion="aic",
        error_action="ignore",
        suppress_warnings=True
    )

    print("\n--- Melhor modelo ---\n")
    print(modelo.summary())
    print("\nEscolhido:", modelo.order)
    return modelo

cpu_model = escolher_arima("CPU", cpu_series)
ram_model = escolher_arima("RAM", ram_series)
