import warnings
import pmdarima as pm
import pandas as pd

warnings.filterwarnings("ignore") # para evitar muitos avisos do auto arima

CSV_PATH = "dataset-gerador.csv"

# carrega dataset
df = pd.read_csv(CSV_PATH)

# garante ordenacao por step
df = df.sort_values("step") 

serie = df["ram"] # serie temporal de uso de RAM

def escolher_arima(nome, serie, max_p=15, max_q=15):
    print(f"\n=========== {nome} ===========\n")

    modelo = pm.auto_arima(
        serie,
        start_p=0,
        start_q=0,
        max_p=max_p,
        max_q=max_q,
        d=None, # deixa o auto_arima decidir
        seasonal=False,
        stepwise=True,
        trace=True,
        information_criterion="aic",
        error_action="ignore",
        suppress_warnings=True
    )

    # prompt dos melhores parametros
    print("\n--- Melhor modelo ---\n")
    print(modelo.summary())
    print("\nEscolhido:", modelo.order)

    return modelo.order 

order_ram = escolher_arima("RAM", serie)
print("\nUse estes parametros no arima.py:", order_ram)