import os, gc, time, math, mmap, ctypes, random

CICLO     = float(os.getenv("CICLO", "60"))
PADRAO    = os.getenv("PADRAO", "wave")
MAX_MB    = float(os.getenv("MAX_MB", "800"))
DURACAO   = float(os.getenv("DURACAO", "300"))
INTERVALO = 0.5
PAGE_SIZE = mmap.PAGESIZE
K         = 8

class AllocatorDirect:
    def __init__(self):
        self._mmaps = []
        self._bytes_alocados = 0

    def ajustar_para(self, bytes_alvo: int):
        bytes_alvo = max(0, bytes_alvo)
        bytes_alvo = (bytes_alvo // PAGE_SIZE) * PAGE_SIZE

        if bytes_alvo > self._bytes_alocados:
            diferenca = bytes_alvo - self._bytes_alocados
            try:
                mm = mmap.mmap(-1, diferenca, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
                ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(mm)), 1, diferenca)
                self._mmaps.append((mm, diferenca))
                self._bytes_alocados += diferenca
            except (MemoryError, OSError):
                pass

        elif bytes_alvo < self._bytes_alocados:
            diferenca_para_remover = self._bytes_alocados - bytes_alvo

            while diferenca_para_remover > 0 and self._mmaps:
                mm, tamanho = self._mmaps.pop()

                if tamanho <= diferenca_para_remover:
                    mm.close()
                    self._bytes_alocados -= tamanho
                    diferenca_para_remover -= tamanho
                else:
                    novo_tamanho = tamanho - diferenca_para_remover
                    mm.close()
                    try:
                        novo_mm = mmap.mmap(-1, novo_tamanho, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
                        ctypes.memset(ctypes.addressof(ctypes.c_char.from_buffer(novo_mm)), 1, novo_tamanho)
                        self._mmaps.append((novo_mm, novo_tamanho))
                        self._bytes_alocados -= diferenca_para_remover
                        diferenca_para_remover = 0
                    except (MemoryError, OSError):
                        self._bytes_alocados -= diferenca_para_remover
                        diferenca_para_remover = 0

            gc.collect()

    def limpar(self):
        for mm, _ in self._mmaps:
            try:
                mm.close()
            except Exception:
                pass
        self._mmaps.clear()
        self._bytes_alocados = 0
        gc.collect()

def calcular_alvo_mb(tempo_decorrido: float, duracao: float) -> float:
    progresso = tempo_decorrido / duracao

    if PADRAO == "constant":
        mb = MAX_MB
    elif PADRAO == "ascending":
        mb = MAX_MB * progresso
    elif PADRAO == "descending":
        mb = MAX_MB * (1 - progresso)
    elif PADRAO == "wave":
        fase = (tempo_decorrido % CICLO) / CICLO
        mb = MAX_MB * (0.5 + 0.5 * math.sin(2 * math.pi * fase))
    elif PADRAO == "pos_exp":
        fase = (tempo_decorrido % CICLO) / CICLO
        mb = MAX_MB * ((math.exp(K * fase) - 1) / (math.exp(K) - 1))
    elif PADRAO == "neg_exp":
        fase = (tempo_decorrido % CICLO) / CICLO
        mb = MAX_MB * ((math.exp(-K * fase) - math.exp(-K)) / (1 - math.exp(-K)))
    elif PADRAO == "partial_random":
        cycle_num = int(progresso * (duracao / 20))
        mb = MAX_MB * 0.6 if cycle_num % 2 == 0 else random.uniform(0, MAX_MB)
    elif PADRAO == "total_random":
        mb = random.uniform(0, MAX_MB)
    else:
        raise ValueError(f"Parâmetro PADRAO inválido: {PADRAO}")

    return max(0, min(MAX_MB, mb))

if __name__ == "__main__":
    allocator = AllocatorDirect()
    start_time = time.time()
    end_time = start_time + DURACAO

    try:
        while True:
            current_time = time.time()
            if current_time >= end_time:
                break

            tempo_decorrido = current_time - start_time

            mb_alvo = calcular_alvo_mb(tempo_decorrido, DURACAO)
            bytes_alvo = int(mb_alvo * 1024 * 1024)
            allocator.ajustar_para(bytes_alvo)

            sleep_time = (current_time + INTERVALO) - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass

    finally:
        allocator.limpar()