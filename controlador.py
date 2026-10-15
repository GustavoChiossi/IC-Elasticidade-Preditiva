import os, sys, time, math, signal, threading, docker
from collections import deque
from modulos.algoritmo import AARIMA
from modulos.coletor import ColetorCompartilhado
from modulos.logger_elasticidade import Logger, encerrar_todos_os_loggers

CONTAINERS_RAW = os.getenv("CONTAINERS", os.getenv("NOME_CONTAINER", ""))
MODO_PADRAO = os.getenv("MODO", "ambos") 
INTERVALO = 2.0
DURACAO_CONTROLADOR = float(os.getenv("DURACAO_CONTROLADOR", "910"))  
COOLDOWN = float(os.getenv("COOLDOWN", "1"))
PASSO_REL = float(os.getenv("PASSO_REL", "0.05")) 
MARGEM = float(os.getenv("MARGEM", "0.1")) 
MIN_AMOSTRAS = int(os.getenv("MIN_AMOSTRAS", "75"))  
CICLOS_RECALIBRACAO = int(os.getenv("CICLOS_RECALIBRACAO", "50"))  
JANELA_DESLIZANTE = int(os.getenv("JANELA_DESLIZANTE", "40"))  
MAX_PASSOS_RED = int(os.getenv("MAX_PASSOS_RED", "2"))  
RAM_MIN_MB = float(os.getenv("RAM_MIN_MB", "64"))
RAM_MAX_MB = float(os.getenv("RAM_MAX_MB", "1024"))
PISO_PREVISAO_MB = float(os.getenv("PISO_PREVISAO_MB", "32"))
CPU_PERIOD_US = int(os.getenv("CPU_PERIOD_US", "100000"))
CPU_MIN_PCT = float(os.getenv("CPU_MIN_PCT", "10"))

cliente_docker = docker.from_env()
_parar_evento = threading.Event()

def _handler_sinal_global(signum, frame):
    print("\n[SINAL] Encerrando controlador (todos os containers)...")
    _parar_evento.set()

signal.signal(signal.SIGINT, _handler_sinal_global)
signal.signal(signal.SIGTERM, _handler_sinal_global)

def parse_containers(bruto: str):
    alvos = []
    for item in bruto.split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            nome, modo = item.split(":", 1)
            modo = modo.strip().lower()
        else:
            nome, modo = item, MODO_PADRAO
        if modo not in ("ram", "cpu", "ambos"):
            print(f"[AVISO] Modo '{modo}' inválido para '{nome}', usando '{MODO_PADRAO}'.")
            modo = MODO_PADRAO
        alvos.append((nome.strip(), modo))
    return alvos

def obter_containers_em_execucao():
    try:
        containers = cliente_docker.containers.list(filters={"status": "running"})
        return [c.name for c in containers]
    except Exception as e:
        print(f"[AVISO] Falha ao obter lista de containers em execução: {e}")
        return []

def inferir_modo_por_limites(nome_container: str) -> str:
    try:
        container = cliente_docker.containers.get(nome_container)
        hc = container.attrs["HostConfig"]
        tem_ram = hc.get("Memory", 0) > 0
        tem_cpu = bool(hc.get("NanoCpus", 0)) or bool(hc.get("CpuQuota", 0)) or bool(hc.get("CpusetCpus", ""))
    except Exception as e:
        print(f"[AVISO] Não foi possível inspecionar limites de '{nome_container}': {e}. Usando MODO_PADRAO.")
        return MODO_PADRAO

    if tem_ram and not tem_cpu:
        return "ram"
    if tem_cpu and not tem_ram:
        return "cpu"
    return MODO_PADRAO

def obter_limite_ram_atual(container) -> float:
    limite = container.attrs["HostConfig"]["Memory"]
    if limite == 0:
        return RAM_MAX_MB
    return limite / (1024 * 1024)

def aplicar_limite_ram(nome_container: str, novo_limite_mb: float):
    novo_limite_bytes = int(novo_limite_mb * 1024 * 1024)
    t_inicio = time.perf_counter()
    try:
        container = cliente_docker.containers.get(nome_container)
        container.update(mem_limit=novo_limite_bytes, memswap_limit=-1)
        latencia_ms = (time.perf_counter() - t_inicio) * 1000
        return True, latencia_ms
    except docker.errors.NotFound:
        print(f"[ERRO] Container '{nome_container}' não encontrado.")
        return False, 0.0
    except docker.errors.APIError as e:
        print(f"[ERRO] Docker API (RAM/{nome_container}): {e}")
        return False, 0.0

def decidir_escala_ram(ram_atual, previsao, limite, ram_max_mb, passo_mb):
    base = max(ram_atual, previsao)
    alvo = base * (1 + MARGEM)
    alvo = math.ceil(alvo / passo_mb) * passo_mb
    alvo = max(RAM_MIN_MB, min(alvo, ram_max_mb))

    if alvo > limite:
        return alvo, f"↑ {alvo:.0f}MB"
    if alvo < limite:
        reducao = min(limite - alvo, MAX_PASSOS_RED * passo_mb)
        novo = limite - reducao
        return novo, f"↓ {novo:.0f}MB"
    return None, "estável"

def descobrir_cpu_cores(container) -> float:
    hc = container.attrs["HostConfig"]
    nano = hc.get("NanoCpus", 0)
    if nano and nano > 0:
        return nano / 1e9
    quota = hc.get("CpuQuota", 0)
    period = hc.get("CpuPeriod", 0)
    if quota and period:
        return quota / period
    cpuset = hc.get("CpusetCpus", "")
    if cpuset:
        ids = []
        for part in cpuset.split(","):
            if "-" in part:
                a, b = part.split("-")
                ids.extend(range(int(a), int(b) + 1))
            elif part:
                ids.append(int(part))
        if ids:
            return len(ids)
    return float(os.cpu_count() or 1)

def obter_limite_cpu_atual(container, cpu_max_pct: float) -> float:
    quota = container.attrs["HostConfig"].get("CpuQuota", 0)
    if not quota:
        return cpu_max_pct
    return (quota / CPU_PERIOD_US) * 100.0

def aplicar_limite_cpu(nome_container: str, novo_pct: float):
    nova_quota = int((novo_pct / 100.0) * CPU_PERIOD_US)
    t0 = time.perf_counter()
    try:
        c = cliente_docker.containers.get(nome_container)
        c.update(cpu_period=CPU_PERIOD_US, cpu_quota=nova_quota)
        lat = (time.perf_counter() - t0) * 1000
        return True, lat
    except docker.errors.NotFound:
        print(f"[ERRO] Container '{nome_container}' não encontrado.")
        return False, 0.0
    except docker.errors.APIError as e:
        print(f"[ERRO] Docker API (CPU/{nome_container}): {e}")
        return False, 0.0

def decidir_escala_cpu(atual, previsao, limite, cpu_max_pct, passo_pct):
    base = max(atual, previsao)
    alvo = base * (1 + MARGEM)
    alvo = math.ceil(alvo / passo_pct) * passo_pct
    alvo = max(CPU_MIN_PCT, min(alvo, cpu_max_pct))

    if alvo > limite:
        return alvo, f"↑ {alvo:.0f}%"
    if alvo < limite:
        reducao = min(limite - alvo, MAX_PASSOS_RED * passo_pct)
        novo = limite - reducao
        return novo, f"↓ {novo:.0f}%"
    return None, "estável"

def executar_container(nome_container: str, modo: str, coletor: ColetorCompartilhado, inicio_global: float):
    monitora_ram = modo in ("ram", "ambos")
    monitora_cpu = modo in ("cpu", "ambos")

    log = Logger(nome_container=nome_container)

    print(f"[{nome_container}] Conectando (modo={modo})...")
    try:
        container = cliente_docker.containers.get(nome_container)
    except docker.errors.NotFound:
        msg = f"Container '{nome_container}' não encontrado. Encerrando thread."
        print(f"[{nome_container}] ERRO: {msg}")
        log.erro(msg)
        log.encerrar()
        return

    historico_ram = deque(maxlen=150)
    modelo_ram = AARIMA(min_amostras=MIN_AMOSTRAS, piso_previsao=PISO_PREVISAO_MB)
    ram_limite_atual = obter_limite_ram_atual(container) if monitora_ram else None
    ram_max_mb = passo_mb = None
    ultimo_escala_ram = 0.0
    if monitora_ram:
        ram_max_mb = RAM_MAX_MB
        passo_mb = ram_max_mb * PASSO_REL
        print(f"[{nome_container}] Limite de RAM inicial: {ram_limite_atual:.0f} MB "
              f"(teto {ram_max_mb:.0f}MB, passo {passo_mb:.0f}MB)")

    historico_cpu = deque(maxlen=150)
    cpu_cores = cpu_max_pct = passo_pct = cpu_limite_atual = None
    modelo_cpu = None
    ultimo_escala_cpu = 0.0
    falhas_consecutivas = 0
    if monitora_cpu:
        cpu_cores = descobrir_cpu_cores(container)
        cpu_max_pct = cpu_cores * 100.0
        passo_pct = cpu_cores * 100.0 * PASSO_REL
        modelo_cpu = AARIMA(min_amostras=MIN_AMOSTRAS, piso_previsao=CPU_MIN_PCT, teto_previsao=cpu_max_pct)
        cpu_limite_atual = obter_limite_cpu_atual(container, cpu_max_pct)
        print(f"[{nome_container}] Núcleos: {cpu_cores:.2f} → teto {cpu_max_pct:.0f}%, "
              f"passo {passo_pct:.0f}%, limite inicial {cpu_limite_atual:.1f}%")

    ciclo = 0

    try:
        while not _parar_evento.is_set():
            if DURACAO_CONTROLADOR > 0 and (time.time() - inicio_global) > DURACAO_CONTROLADOR:
                print(f"[{nome_container}] Tempo limite do controlador atingido. Encerrando.")
                break

            ciclo += 1

            if not coletor.container_visto(nome_container):
                falhas_consecutivas += 1
                print(f"[{nome_container}] Aviso: não visto no snapshot "
                      f"(tentativa {falhas_consecutivas}/{5})")
                if falhas_consecutivas >= 5:
                    msg = f"Container '{nome_container}' não visto após {5} tentativas. Encerrando thread."
                    print(f"[{nome_container}] {msg}")
                    log.erro(msg)
                    break
                _parar_evento.wait(INTERVALO)
                continue
            falhas_consecutivas = 0

            leitura = coletor.obter(nome_container)
            ram_atual = leitura["ram_mb"] if monitora_ram else None
            cpu_atual = leitura["cpu_percent"] if monitora_cpu else None

            previsao_ram = previsao_cpu = None

            if monitora_ram and ram_atual is not None:
                historico_ram.append(ram_atual)

                if ciclo % CICLOS_RECALIBRACAO == 0 and len(historico_ram) >= 10:
                    try:
                        nova_ordem = modelo_ram.inicializar(list(historico_ram))
                        log.recalibracao("ram", ciclo, nova_ordem)
                        print(f"[{nome_container}] RECALIB(RAM) #{ciclo // CICLOS_RECALIBRACAO}: {nova_ordem}")
                    except Exception as e:
                        log.erro(f"Recalibração RAM: {e}")

                try:
                    previsao_ram = modelo_ram.prever_proximo_passo(list(historico_ram), janela_deslizante=JANELA_DESLIZANTE)
                except Exception as e:
                    log.erro(f"Previsão RAM: {e}")
                    previsao_ram = None

                if previsao_ram is not None and (time.time() - ultimo_escala_ram) >= COOLDOWN:
                    novo_limite, razao = decidir_escala_ram(
                        ram_atual, previsao_ram, ram_limite_atual, ram_max_mb, passo_mb)
                    if novo_limite is not None:
                        sucesso, latencia_ms = aplicar_limite_ram(nome_container, novo_limite)
                        if sucesso:
                            delta = novo_limite - ram_limite_atual
                            direcao = "cima" if delta > 0 else "baixo"
                            log.escala("ram", ram_atual, previsao_ram, ram_limite_atual, novo_limite, direcao, latencia_ms)
                            print(f"[{nome_container}] RAM {'↑' if delta > 0 else '↓'} "
                                  f"{abs(delta):.0f}MB → {novo_limite:.0f}MB [{latencia_ms:.1f}ms] ({razao})")
                            ram_limite_atual = novo_limite
                            ultimo_escala_ram = time.time()
                        else:
                            log.erro(f"Falha ao aplicar limite RAM {novo_limite:.0f}MB")

            if monitora_cpu and cpu_atual is not None:
                historico_cpu.append(cpu_atual)

                if ciclo % CICLOS_RECALIBRACAO == 0 and len(historico_cpu) >= 10:
                    try:
                        nova_ordem = modelo_cpu.inicializar(list(historico_cpu))
                        log.recalibracao("cpu", ciclo, nova_ordem)
                        print(f"[{nome_container}] RECALIB(CPU) #{ciclo // CICLOS_RECALIBRACAO}: {nova_ordem}")
                    except Exception as e:
                        log.erro(f"Recalibração CPU: {e}")

                try:
                    previsao_cpu = modelo_cpu.prever_proximo_passo(list(historico_cpu), janela_deslizante=JANELA_DESLIZANTE)
                except Exception as e:
                    log.erro(f"Previsão CPU: {e}")
                    previsao_cpu = None

                if previsao_cpu is not None and (time.time() - ultimo_escala_cpu) >= COOLDOWN:
                    novo_limite, razao = decidir_escala_cpu(cpu_atual, previsao_cpu, cpu_limite_atual, cpu_max_pct, passo_pct)
                    if novo_limite is not None:
                        sucesso, latencia_ms = aplicar_limite_cpu(nome_container, novo_limite)
                        if sucesso:
                            delta = novo_limite - cpu_limite_atual
                            direcao = "cima" if delta > 0 else "baixo"
                            log.escala("cpu", cpu_atual, previsao_cpu, cpu_limite_atual, novo_limite, direcao, latencia_ms)
                            print(f"[{nome_container}] CPU {'↑' if delta > 0 else '↓'} "
                                  f"{abs(delta):.1f}% → {novo_limite:.1f}% [{latencia_ms:.1f}ms] ({razao})")
                            cpu_limite_atual = novo_limite
                            ultimo_escala_cpu = time.time()
                        else:
                            log.erro(f"Falha ao aplicar limite CPU {novo_limite:.1f}%")

            if (monitora_ram and ram_atual is not None) or (monitora_cpu and cpu_atual is not None):
                log.coleta(
                    ram_mb=ram_atual, previsao_ram_mb=previsao_ram, limite_ram_mb=ram_limite_atual,
                    cpu_percent=cpu_atual, previsao_cpu_pct=previsao_cpu, limite_cpu_pct=cpu_limite_atual,
                )

                linha = [f"[{nome_container} #{ciclo:04d}]"]
                if monitora_ram and ram_atual is not None:
                    linha.append(f"RAM {ram_atual:7.2f}MB (lim {ram_limite_atual:6.0f}MB)")
                if monitora_cpu and cpu_atual is not None:
                    linha.append(f"CPU {cpu_atual:6.2f}% (lim {cpu_limite_atual:6.1f}%)")
                print(" | ".join(linha))

            _parar_evento.wait(INTERVALO)

    finally:
        log.encerrar()
        print(f"[{nome_container}] Controlador encerrado.")

def main():
    raw_containers = os.getenv("CONTAINERS")
    if raw_containers is not None and raw_containers != "":
        alvos = parse_containers(raw_containers)
    else:
        nome_container = os.getenv("NOME_CONTAINER")
        if nome_container:
            alvos = parse_containers(nome_container)
        else:
            nomes = obter_containers_em_execucao()
            if not nomes:
                print("Nenhum container em execução encontrado. Encerrando.")
                sys.exit(1)
            alvos = [(nome, inferir_modo_por_limites(nome)) for nome in nomes]
            print(f"CONTAINERS não definido: modo de cada container foi inferido "
                  f"pelos limites já configurados no Docker: {alvos}")

    if not alvos:
        print("Nenhum container configurado para monitoramento. Encerrando.")
        sys.exit(1)

    print(f"Containers monitorados: {alvos}")

    coletor = ColetorCompartilhado(intervalo=INTERVALO)
    coletor.iniciar()

    inicio_global = time.time()
    threads = []
    for nome, modo in alvos:
        t = threading.Thread(
            target=executar_container,
            args=(nome, modo, coletor, inicio_global),
            name=f"container-{nome}",
            daemon=True,
        )
        threads.append(t)
        t.start()

    try:
        while any(t.is_alive() for t in threads) and not _parar_evento.is_set():
            time.sleep(0.5)
        for t in threads:
            t.join(timeout=INTERVALO + 5)
    except KeyboardInterrupt:
        _parar_evento.set()
        for t in threads:
            t.join(timeout=INTERVALO + 5)
    finally:
        coletor.parar()
        encerrar_todos_os_loggers()
        print("Todos os containers encerrados.")

if __name__ == "__main__":
    main()
