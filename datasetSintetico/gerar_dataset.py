import numpy as np
import pandas as pd

np.random.seed(42) # para reprodutibilidade

# parametros
n_days = 7            # dias coletados
freq_min = 5          # coleta a cada 5 minutos
n = int((24*60/freq_min) * n_days)  # total de linhas
t = np.arange(n)

# gerar picos aleatorios
def add_random_spikes(series, spike_prob=0.01, spike_magnitude=50):
    spikes = np.random.choice([0, spike_magnitude], size=len(series), p=[1-spike_prob, spike_prob])
    return series + spikes

# ciclos diarios e ruido
cpu_base = 30 + 20*np.sin(2*np.pi*t/(24*60/freq_min)) + np.random.normal(0, 5, n)
cpu = add_random_spikes(cpu_base, spike_prob=0.02, spike_magnitude=40)
cpu = np.clip(cpu, 0, 100)

ram_base = 40 + 15*np.sin(2*np.pi*t/(24*60/freq_min) + np.pi/4) + np.random.normal(0, 3, n)
ram = add_random_spikes(ram_base, spike_prob=0.015, spike_magnitude=30)
ram = np.clip(ram, 0, 100)

# cria dataframe com timestamp
timestamps = pd.date_range(start="2025-12-11 00:00:00", periods=n, freq=f"{freq_min}min")
df = pd.DataFrame({"timestamp": timestamps, "cpu": cpu, "ram": ram})

# salva CSV
df.to_csv("dataset.csv", index=False)