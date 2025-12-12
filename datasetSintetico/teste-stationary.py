# teste pra ver se é stationary ou nao

from statsmodels.tsa.stattools import adfuller
import pandas as pd

csv_path = 'dataset.csv'

def test_stationarity(name, series):
    adf, p, _, _, crit, _ = adfuller(series)

    print(f"\n=== {name.upper()} ===")
    print(f"ADF: {adf:.4f}")
    print(f"p-value: {p:.4f}")
    print("Critical values:")
    for lvl, val in crit.items():
        print(f"  {lvl}: {val:.4f}")
    print("Status:", "Stationary" if p <= 0.05 else "Non-stationary")

# carregar dataset
df = pd.read_csv(csv_path)

# rodar os dois testes
test_stationarity("cpu", df["cpu"].dropna())
test_stationarity("ram", df["ram"].dropna())