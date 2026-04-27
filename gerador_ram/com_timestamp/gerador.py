import os, csv, time, math, random, psutil, matplotlib.pyplot as plt
from datetime import datetime, timedelta

# parametros
PADRAO = os.getenv("PADRAO", "pos_exp") 
MAX_MB = int(os.getenv("MAX_MB", "512"))
DURATION = float(os.getenv("DURATION", "180"))
SLEEP = float(os.getenv("SLEEP", "0.1"))
INTERVAL = float(os.getenv("INTERVAL", "1.0"))
K = 8

process = psutil.Process(os.getpid())
memory = None
uso_ram = []
timestamps = []

def alloc(mb):
    global memory 
    memory = bytearray(int(mb * 1024 * 1024))    
    time.sleep(0.5) 

# Funções para wave-hard
def random_walk(start, steps, step_size=0.1):
    values = [start]
    for i in range(1, steps):
        change = random.uniform(-step_size, step_size)
        new_value = values[-1] + change
        # Limita entre 0 e 1
        new_value = max(0, min(1, new_value))
        values.append(new_value)
    return values

def wave_hard_pattern(x, amp, freq, phase):
    # Gera uma "assinatura" única baseada no tempo
    #seed = int(time.time() * 1000) % 10000
    #random.seed(seed + int(x * 1000))
    
    # 1. Onda senoidal principal com frequência variável
    #freq_mult = random.uniform(3.0, 6.0)  # Frequência varia entre 3x e 6x
    #phase_shift = random.uniform(0, 2*math.pi)
    #phase = random_walk(0.0, num_points, 0.2)
    wave1 = amp * 0.4 * math.sin(freq * 2 * math.pi * x + phase)
    
    # 2. Onda secundária com diferente frequência
    freq2 = random.uniform(1.0, 2.0) * 2 * math.pi * x
    wave2 = 0.3 * math.sin(freq2 + random.uniform(0, math.pi))
    
    # 3. Componente de ruído colorido (autocorrelacionado)
    noise = random.uniform(-0.2, 0.2) * math.sin(random.uniform(10, 20) * x)
    
    # 4. Pulsos aleatórios
    pulse = 0
    if random.random() < 0.05:  # 5% de chance de pulso
        pulse_width = random.uniform(0.02, 0.1)
        if x % pulse_width < pulse_width/2:
            pulse = random.uniform(-0.15, 0.15)
    
    # 5. Mudanças abruptas de tendência (ocasionais)
    trend_shift = 0
    if random.random() < 0.03:  # 3% de chance
        trend_shift = random.uniform(-0.25, 0.25)
    
    # Combina todos os componentes
    combined = 0.5 + wave1 + wave2 + noise + pulse + trend_shift
    
    # Adiciona não-linearidade
    if random.random() < 0.3:
        combined = math.tanh(combined * 1.5)
    
    return max(0, min(1, combined))

# Tempo inicial
start_time = time.time()
end_time = start_time + DURATION
current_time = start_time

# Para wave-hard, pré-calculamos algumas variáveis
if PADRAO == "wave_hard":
    # Gera um passeio aleatório para amplitude
    num_points = int(DURATION / INTERVAL) + 1
    amplitude_walk = random_walk(0.5, num_points, 0.05)
    freq_walk = random_walk(1.0, num_points, 0.1)
    phase_walk = random_walk(0.0, num_points, 0.2)
    point_index = 0

while current_time < end_time:
    progresso = (current_time - start_time) / DURATION
    
    if PADRAO == "constant":
        rss = process.memory_info().rss / (1024 * 1024)
        uso_ram.append(rss)
        timestamps.append(current_time - start_time)
        time.sleep(SLEEP)
        current_time = time.time()
        continue
    
    # Calcular MB baseado no padrão
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
    elif PADRAO == "wave_hard":
        amp = amplitude_walk[point_index]
        freq = freq_walk[point_index]
        phase = phase_walk[point_index]
        mb = MAX_MB * wave_hard_pattern(progresso, amp, freq, phase)
        point_index += 1
    else:
        raise ValueError("Parâmetro inválido")
    
    alloc(mb)
    
    # Registrar uso de RAM e timestamp
    rss = process.memory_info().rss / (1024 * 1024)
    uso_ram.append(rss)
    timestamps.append(current_time - start_time)
    
    # Aguardar até o próximo intervalo
    sleep_time = INTERVAL - (time.time() - current_time)
    if sleep_time > 0:
        time.sleep(sleep_time)
    
    current_time = time.time()

# salva CSV
suffix = os.getenv("OUTPUT_SUFFIX", "")

with open(f"csv-timestamp/dataset-gerador-timestamp{suffix}.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timestamp_sec", "timestamp_hms", "ram_mb"])
    for i, (t, mb) in enumerate(zip(timestamps, uso_ram)):
        hms = str(timedelta(seconds=t)).split('.')[0]
        w.writerow([f"{t:.2f}", hms, f"{mb:.2f}"])

# plot final
plt.figure(figsize=(12, 6))
plt.plot(timestamps, uso_ram, 'b-', linewidth=1.5, alpha=0.7)
plt.fill_between(timestamps, uso_ram, alpha=0.2)
plt.xlabel("Tempo (segundos)")
plt.ylabel("Memória RAM (MB)")
plt.title(f"Uso de RAM - {PADRAO} - {DURATION}s")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f"imagens-timestamp/ram{suffix}.png", dpi=120)
plt.show()