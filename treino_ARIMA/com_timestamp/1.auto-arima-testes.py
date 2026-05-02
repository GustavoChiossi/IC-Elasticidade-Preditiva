import warnings
import pmdarima as pm
import pandas as pd

warnings.filterwarnings("ignore")  # evita muitos avisos do auto arima

CAMINHO_CSV = "../../gerador_ram/com_timestamp/csv/descending.csv"

df = pd.read_csv(CAMINHO_CSV)                            # carrega dataset
df["timestamp_sec"] = pd.to_numeric(df["timestamp_sec"]) # converte timestamp para numerico
df = df.set_index("timestamp_sec")                       # define indice temporal
df = df.sort_index()                                     # ordena por tempo
serie = df["ram_mb"]                                     # define serie temporal

def escolherArima(nome, serie, maxP=15, maxQ=15):
    print(f"\n=========== {nome} ===========\n")

    # busca automatica de parametros
    modelo = pm.auto_arima(
        serie,
        start_p=0,
        start_q=0,
        max_p=maxP,
        max_q=maxQ,
        max_d=2,
        maxiter=200,
        d=None,  
        test="kpss",
        seasonal=False,  
        stepwise=True,
        trace=True,
        with_intercept="auto",
        information_criterion="aic",
        error_action="ignore",
        suppress_warnings=True
    )

    # mostra melhor modelo
    print("\n--- melhor modelo ---\n")
    print(modelo.summary())
    print("\nescolhido:", modelo.order)
    return modelo.order

ordemRam = escolherArima("ram", serie)

print("\nUse esses parâmetros no arima.py:", ordemRam)