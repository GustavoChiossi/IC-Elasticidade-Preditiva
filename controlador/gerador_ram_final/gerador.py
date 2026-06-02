from datetime import timedelta
import os, gc, time, math, ctypes, random, psutil
import matplotlib
import matplotlib.pyplot as plt

CICLO = float(os.getenv("CICLO", "60"))
PADRAO = os.getenv("PADRAO", "pos_exp")
MAX_MB = int(os.getenv("MAX_MB", "900"))
DURACAO = float(os.getenv("DURACAO", "300"))
SLEEP = float(os.getenv("SLEEP", "0.1"))
INTERVALO = float(os.getenv("INTERVAL", "1.0"))
K = 8

matplotlib.use('Agg') # backend sem interface grafica (p/ container)
process = psutil.Process(os.getpid())
memory = None
libc = ctypes.CDLL("libc.so.6")
timestamps = []
ram_values = []

def alloc(mb):
    global memory
    if memory is not None:
        del memory
    gc.collect()
    libc.malloc_trim(0)
    memory = bytearray(int(mb * 1024 * 1024))

start_time = time.time()
end_time = start_time + DURACAO
current_time = start_time

while current_time < end_time:
    tempo_decorrido = current_time - start_time
    progresso = tempo_decorrido / DURACAO
    fase = (tempo_decorrido % CICLO) / CICLO

    if PADRAO == "constant":
        mb = MAX_MB
    elif PADRAO == "ascending":
        mb = MAX_MB * progresso
    elif PADRAO == "descending":
        mb = MAX_MB * (1 - progresso)
    elif PADRAO == "wave":
        mb = MAX_MB * (0.5 + 0.5 * math.sin(4 * math.pi * progresso))
    elif PADRAO == "pos_exp":
        mb = MAX_MB * ((math.exp(K * fase) - 1) / (math.exp(K) - 1))
    elif PADRAO == "neg_exp":
        mb = MAX_MB * ((math.exp(-K * fase) - math.exp(-K)) / (1 - math.exp(-K)))
    elif PADRAO == "partial_random":
        cycle_num = int(progresso * (DURACAO / 20))
        mb = MAX_MB * 0.6 if cycle_num % 2 == 0 else random.uniform(0, MAX_MB)
    elif PADRAO == "total_random":
        mb = random.uniform(0, MAX_MB)
    else:
        raise ValueError("Parâmetro inválido")

    alloc(mb)
    ram_real = process.memory_info().rss / (1024 * 1024)
    timestamps.append(tempo_decorrido)
    ram_values.append(ram_real)
    sleep_time = max(0, INTERVALO - (time.time() - current_time))
    time.sleep(sleep_time)
    current_time = time.time()

# plot
plt.figure(figsize=(10, 5))
plt.plot(timestamps, ram_values)
plt.xlabel("Tempo (s)")
plt.ylabel("RAM (MB)")
plt.title(f"Uso de RAM - {PADRAO}")
plt.grid(True)
plt.tight_layout()
plt.savefig("grafico_gerador.png")   