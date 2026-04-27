import os, csv, time, math, random, psutil, matplotlib.pyplot as plt

# parametros
PADRAO = os.getenv("PADRAO", "pos_exp") 
MAX_MB = int(os.getenv("MAX_MB", "512"))
STEPS = int(os.getenv("STEPS", "200")) # steps é o numero de vezes q mem é alocada
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
    elif PADRAO == "partial_random": # aleatorio mas com picos regulares
        mb = MAX_MB * 0.6 if (i // 20) % 2 == 0 else random.uniform(0, MAX_MB)
    elif PADRAO == "total_random": 
        mb = random.uniform(0, MAX_MB)
    elif PADRAO == "wave_hard": # onda com picos mais acentuados e frequencia/amplitude variaveis
        # frequência e amplitude variáveis
        freq = 2 + 1.5 * math.sin(2 * math.pi * x * 0.7)
        amp = 0.4 + 0.3 * math.sin(2 * math.pi * x * 0.3)

        # ruído suave (não totalmente aleatório)
        noise = random.uniform(-0.08, 0.08)

        mb = MAX_MB * (
            0.5 + amp * math.sin(2 * math.pi * freq * x + noise)
        )
        mb = max(0, min(MAX_MB, mb))
        
    elif PADRAO == "wave_hard_blocks": # por blocos, cada bloco tem frequência/amplitude diferente mas constante dentro do bloco
        block = (i // 25) % 4

        freqs = [1.5, 3.2, 0.8, 2.4]
        amps  = [0.35, 0.25, 0.45, 0.3]

        freq = freqs[block] + random.uniform(-0.2, 0.2)
        amp  = amps[block]  + random.uniform(-0.05, 0.05)

        mb = MAX_MB * (
            0.5 + amp * math.sin(2 * math.pi * freq * x)
        )
        mb = max(0, min(MAX_MB, mb))
        
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