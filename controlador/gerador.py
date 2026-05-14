# gerador de RAM (nao plota imagens, nao salva em csv, nao tem padrao wave_hard)

import os, time, math, random, psutil
import matplotlib.pyplot as plt

PADRAO = os.getenv("PADRAO", "pos_exp") 
MAX_MB = int(os.getenv("MAX_MB", "512"))
DURATION = float(os.getenv("DURATION", "180"))
SLEEP = float(os.getenv("SLEEP", "0.1"))
INTERVALO = float(os.getenv("INTERVAL", "1.0"))
K = 8

process = psutil.Process(os.getpid())
memory = None
uso_ram = []
timestamps = []

def alloc(mb):
    global memory 
    memory = bytearray(int(mb * 1024 * 1024))    
    time.sleep(0.5) 

# tempo inicial
start_time = time.time()
end_time = start_time + DURATION
current_time = start_time

while current_time < end_time:
    progresso = (current_time - start_time) / DURATION
    
    if PADRAO == "constant":
        rss = process.memory_info().rss / (1024 * 1024)
        uso_ram.append(rss)
        timestamps.append(current_time - start_time)
        time.sleep(SLEEP)
        current_time = time.time()
        continue
    
    # calcular MB baseado no padrao
    if PADRAO == "ascending":
        mb = MAX_MB * progresso
    elif PADRAO == "descending":
        mb = MAX_MB * (1 - progresso)
    elif PADRAO == "wave":
        mb = MAX_MB * (0.5 + 0.5 * math.sin(4 * math.pi * progresso))
    elif PADRAO == "pos_exp":
        mb = MAX_MB * (math.exp(K * progresso) - 1) / (math.exp(K) - 1)
    elif PADRAO == "neg_exp":
        mb = MAX_MB * (math.exp(-K * progresso) - math.exp(-K)) / (1 - math.exp(-K))
    elif PADRAO == "partial_random":
        cycle_num = int(progresso * (DURATION / 20))
        mb = MAX_MB * 0.6 if cycle_num % 2 == 0 else random.uniform(0, MAX_MB)
    elif PADRAO == "total_random":
        mb = random.uniform(0, MAX_MB)
    else:
        raise ValueError("Parâmetro inválido")
    
    alloc(mb)
    
    # aguardar ate o proximo intervalo
    sleep_time = INTERVALO - (time.time() - current_time)
    if sleep_time > 0:
        time.sleep(sleep_time)
    current_time = time.time()