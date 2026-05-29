from datetime import timedelta
import os, gc, time, math, ctypes, random, psutil

CICLO = float(os.getenv("CICLO", "60"))
PADRAO = os.getenv("PADRAO", "pos_exp")
MAX_MB = int(os.getenv("MAX_MB", "900"))
DURACAO = float(os.getenv("DURACAO", "300"))
SLEEP = float(os.getenv("SLEEP", "0.1"))
INTERVALO = float(os.getenv("INTERVAL", "1.0"))
K = 8

process = psutil.Process(os.getpid())
memory = None
libc = ctypes.CDLL("libc.so.6")

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

    progresso = (current_time - start_time) / DURACAO
    tempo_decorrido = current_time - start_time
    fase = (tempo_decorrido % CICLO) / CICLO

    if PADRAO == "constant":

        alloc(MAX_MB)
        time.sleep(SLEEP)
        current_time = time.time()
        continue

    if PADRAO == "ascending":
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
    
    sleep_time = INTERVALO - (time.time() - current_time)

    if sleep_time > 0:
        time.sleep(sleep_time)
    current_time = time.time()