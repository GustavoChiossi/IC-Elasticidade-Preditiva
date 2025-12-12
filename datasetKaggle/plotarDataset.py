import pandas as pd
import matplotlib.pyplot as plt

# caminhos
csv_path = "/home/gustavo/faculdade/ic/controlador-preditivo/datasetKaggle/dataset.csv"

df = pd.read_csv(csv_path)
df = df.sort_values("index").reset_index(drop=True)

# cpu
plt.figure(figsize=(12, 4))
plt.plot(df["index"], df["cpu"], linewidth=0.8)
plt.title("Uso de CPU")
plt.xlabel("Index")
plt.ylabel("CPU (%)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# ram
plt.figure(figsize=(12, 4))
plt.plot(df["index"], df["ram"], linewidth=0.8)
plt.title("Uso de RAM")
plt.xlabel("Index")
plt.ylabel("RAM (%)")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()