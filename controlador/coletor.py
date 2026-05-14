import docker
client = docker.from_env()

def coletar_ram():
    containers = client.containers.list()
    total = 0

    for c in containers:
        stats = c.stats(stream=False)
        uso = (stats["memory_stats"]["usage"]/(1024*1024))
        total += uso
        
    return total