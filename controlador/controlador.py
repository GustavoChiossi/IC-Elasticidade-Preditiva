# falta implementar listas para armazenar os dados de ram real e prevista, para plotar o grafico depois
# implementar futuramente pra varios containers, e nao so pra um
# fazer uso do coletor.py

from collections import deque
from algoritmo import *
from coletor import *
from gerador import *
import docker, time

EXEC_AARIMA = 30
JANELA = 60
COLETA = 3
COOLDOWN = 20
MIN_RAM = 64
MAX_RAM = 2048
MARGEM = 0.1

historico = deque(maxlen=JANELA)
ultima_recalibracao = 0
ultima_alteracao = 0

# varios e nao um so
client = docker.from_env()
container = client.containers.get("teste") 

# para plotar graficos depois
#timestamps = []
#limite_ram = []
#uso_ram = []
#previsao_ram = []

def aplicar(previsao):
    global ultima_alteracao
    tempo_atual = time.time()

    if (tempo_atual-ultima_alteracao < COOLDOWN):
        return

    memoria = previsao * (1 + MARGEM)
    memoria = max(MIN_RAM, min(memoria, MAX_RAM))
    atual = (container.attrs["HostConfig"]["Memory"] / (1024*1024))

    if (abs(memoria-atual) < 100): 
        return
    container.update(mem_limit=f"{int(memoria)}m")
    ultima_alteracao = tempo_atual

while True:
    if len(historico) < JANELA:
        time.sleep(COLETA)
        continue

    tempo_atual = time.time()

    if (tempo_atual - ultima_recalibracao > EXEC_AARIMA):
        atualizar_parametros(historico)
        ultima_recalibracao = tempo_atual

    if ordem:
        previsao = prever(historico)
        aplicar(previsao)

    time.sleep(COLETA)