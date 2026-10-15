import threading, json
from glances.stats import GlancesStats
from glances.main import GlancesMain

_glances_main = GlancesMain()
_stats = GlancesStats(config=_glances_main.get_config(), args=_glances_main.get_args())

def _converter_para_mb(valor):
    if valor is None:
        return None
    try:
        if isinstance(valor, (int, float)):
            return float(valor) / (1024 * 1024)

        valor = str(valor).strip().upper()

        if "KB" in valor:
            return float(valor.replace("KB", "").strip()) / 1024
        if "MB" in valor:
            return float(valor.replace("MB", "").strip())
        if "GB" in valor:
            return float(valor.replace("GB", "").strip()) * 1024

        return float(valor) / (1024 * 1024)
    except Exception:
        return None


def _normalizar_containers(containers_raw):
    if isinstance(containers_raw, bytes):
        containers_raw = containers_raw.decode("utf-8")
    if isinstance(containers_raw, str):
        containers_raw = json.loads(containers_raw)
    if isinstance(containers_raw, list):
        return containers_raw
    if isinstance(containers_raw, dict):
        if "containers" in containers_raw:
            return containers_raw["containers"]
        return list(containers_raw.values())
    return []


def _obter_ram_mb(container: dict):
    valor = container.get("memory_usage")
    if valor is not None:
        return _converter_para_mb(valor)

    memoria = container.get("memory")
    if isinstance(memoria, dict):
        for chave in ("usage", "used", "rss"):
            if chave in memoria:
                return _converter_para_mb(memoria[chave])
    return None


def _obter_cpu_pct(container: dict):
    valor = container.get("cpu_percent")
    if valor is not None:
        try:
            return float(valor)
        except (TypeError, ValueError):
            return None

    cpu = container.get("cpu")
    if isinstance(cpu, dict) and "total" in cpu:
        try:
            return float(cpu["total"])
        except (TypeError, ValueError):
            return None
    return None


class ColetorCompartilhado:
    def __init__(self, intervalo: float = 2.0):
        self._intervalo = intervalo
        self._lock = threading.Lock()
        self._snapshot: dict[str, dict] = {}
        self._parar = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="coletor-glances", daemon=True)

    def iniciar(self):
        self._thread.start()

    def parar(self):
        self._parar.set()
        self._thread.join(timeout=self._intervalo + 2)

    def _loop(self):
        while not self._parar.is_set():
            try:
                _stats.update()
                plugin = _stats.get_plugin("containers")
                containers = _normalizar_containers(plugin.get_stats()) if plugin else []

                novo_snapshot = {}
                for c in containers:
                    if not isinstance(c, dict):
                        continue
                    nome = c.get("name")
                    if not nome:
                        continue
                    novo_snapshot[nome] = {
                        "ram_mb": _obter_ram_mb(c),
                        "cpu_percent": _obter_cpu_pct(c),
                    }

                with self._lock:
                    self._snapshot = novo_snapshot
            except Exception:
                pass

            self._parar.wait(self._intervalo)

    def obter(self, nome_container: str) -> dict:
        with self._lock:
            dados = self._snapshot.get(nome_container)
        return dict(dados) if dados else {"ram_mb": None, "cpu_percent": None}

    def container_visto(self, nome_container: str) -> bool:
        with self._lock:
            return nome_container in self._snapshot