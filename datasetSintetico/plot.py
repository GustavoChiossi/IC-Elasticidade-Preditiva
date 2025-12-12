import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

# carrega o dataset
df = pd.read_csv("dataset.csv", parse_dates=["timestamp"])

# plota CPU e RAM
plt.figure(figsize=(15,5))
plt.plot(df["timestamp"], df["cpu"], label="CPU (%)", color="tab:blue")
plt.plot(df["timestamp"], df["ram"], label="RAM (%)", color="tab:orange")
plt.xlabel("Timestamp")
plt.ylabel("Uso (%)")
plt.title("Uso de CPU e RAM - Dataset Sintético")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# plota ACF e PACF para CPU
fig, axs = plt.subplots(2, 2, figsize=(15,10))

plot_acf(df["cpu"], lags=50, ax=axs[0,0])
axs[0,0].set_title("ACF - CPU")

plot_pacf(df["cpu"], lags=50, ax=axs[0,1])
axs[0,1].set_title("PACF - CPU")

# plota ACF e PACF para RAM
plot_acf(df["ram"], lags=50, ax=axs[1,0])
axs[1,0].set_title("ACF - RAM")

plot_pacf(df["ram"], lags=50, ax=axs[1,1])
axs[1,1].set_title("PACF - RAM")

plt.tight_layout()
plt.show()
