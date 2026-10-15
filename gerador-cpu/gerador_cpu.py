import os, time, math, random, multiprocessing, psutil

CPU_CORES_ENV = os.getenv("CPU_CORES")
CICLO         = float(os.getenv("CICLO", "60"))
PADRAO        = os.getenv("PADRAO", "wave")
MAX_CPU       = int(os.getenv("MAX_CPU", "80"))
DURACAO       = float(os.getenv("DURACAO", "300"))
INTERVALO     = 0.5 
K             = 8

if CPU_CORES_ENV is not None:
    CPU_CORES = int(CPU_CORES_ENV)
else:
    CPU_CORES = multiprocessing.cpu_count()

start_time = time.time()
end_time = start_time + DURACAO
duty_cycle = multiprocessing.Value('d', 0.0)
keep_running = multiprocessing.Value('b', True)

def padrao_atual(tempo_decorrido):
    progresso = tempo_decorrido / DURACAO
    fase = (tempo_decorrido % CICLO) / CICLO

    if PADRAO == "constant":
        return 1.0
    elif PADRAO == "ascending":
        return min(1.0, progresso)
    elif PADRAO == "descending":
        return max(0.0, 1 - progresso)
    elif PADRAO == "wave":
        return 0.5 + 0.5 * math.sin(2 * math.pi * (tempo_decorrido / CICLO))
    elif PADRAO == "pos_exp":
        return (math.exp(K * fase) - 1) / (math.exp(K) - 1)
    elif PADRAO == "neg_exp":
        return (math.exp(-K * fase) - math.exp(-K)) / (1 - math.exp(-K))
    elif PADRAO == "partial_random":
        cycle_num = int(tempo_decorrido / 20)
        return 0.6 if cycle_num % 2 == 0 else random.random()
    elif PADRAO == "total_random":
        return random.random()
    else:
        raise ValueError(f"Padrão desconhecido: {PADRAO}")

def cpu_worker(duty_cycle, keep_running):
    while keep_running.value:
        current_duty = duty_cycle.value
        if current_duty <= 0.0:
            time.sleep(INTERVALO)
            continue

        start_work = time.perf_counter()
        work_duration = current_duty * INTERVALO

        while (time.perf_counter() - start_work) < work_duration:
            pass

        sleep_duration = INTERVALO - work_duration
        if sleep_duration > 0:
            time.sleep(sleep_duration)

if __name__ == '__main__':
    processes = []
    for _ in range(CPU_CORES):
        p = multiprocessing.Process(target=cpu_worker, args=(duty_cycle, keep_running))
        p.daemon = True
        p.start()
        processes.append(p)

    try:
        while time.time() < end_time:
            elapsed = time.time() - start_time

            fator = padrao_atual(elapsed)
            cpu_alvo_por_core = fator * MAX_CPU
            duty_cycle.value = cpu_alvo_por_core / 100.0

            time.sleep(1.0)

    finally:
        keep_running.value = False
        for p in processes:
            p.join(timeout=0.1)