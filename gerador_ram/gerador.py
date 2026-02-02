import os, csv, time, math, random, psutil, matplotlib.pyplot as plt

# parametros
PADRAO = os.getenv("PADRAO", "pos_exp") 
MAX_MB = int(os.getenv("MAX_MB", "512"))
STEPS = int(os.getenv("STEPS", "200")) 
SLEEP = float(os.getenv("SLEEP", "0.1")) 
K = 8 # constante para ajustar a curva exponencial

process = psutil.Process(os.getpid()) # processo atual

memory = None # referencia para a memoria alocada
uso_ram = [] 

def alloc(mb):
    global memory
    memory = bytearray(int(mb * 1024 * 1024))
    time.sleep(2) # garante que o constant nao comece alto e depois desca

for i in range(STEPS):
    x = i / (STEPS - 1) 

    if PADRAO == "constant":
        rss = process.memory_info().rss / (1024 * 1024)
        uso_ram.append(rss)
        time.sleep(SLEEP)
        continue
    
    if PADRAO == "ascending":
        mb = MAX_MB * x
    elif PADRAO == "descending":
        mb = MAX_MB * (1 - x)
    elif PADRAO == "wave":
        mb = MAX_MB * (0.5 + 0.5 * math.sin(4 * math.pi * x))
    elif PADRAO == "pos_exp":
        mb = MAX_MB * (math.exp(K * x) - 1) / (math.exp(K) - 1)
    elif PADRAO == "neg_exp":
        mb = MAX_MB * (math.exp(-K * x) - math.exp(-K)) / (1 - math.exp(-K))
    elif PADRAO == "partial_random":
        mb = MAX_MB * 0.6 if (i // 20) % 2 == 0 else random.uniform(0, MAX_MB)
    elif PADRAO == "total_random":
        mb = random.uniform(0, MAX_MB)
    else:
        raise ValueError("Parâmetro inválido")

    alloc(mb)

    rss = process.memory_info().rss / (1024 * 1024)
    uso_ram.append(rss)

    time.sleep(SLEEP)
    
# salva CSV
with open("dataset-gerador.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["step", "ram"])
    for i, mb in enumerate(uso_ram):
        w.writerow([i, mb])
        
# plot final 
plt.plot(uso_ram)
plt.xlabel("tempo (STEPS)")
plt.ylabel("memória RAM (MB)")
plt.title(f"Uso de RAM - {PADRAO}")
plt.savefig("ram-gerador.png")