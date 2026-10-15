from datetime import datetime, timezone
from typing import Literal
from pathlib import Path
import threading, json, sys

DIR_LOGS_BASE = Path("logs")

_registro_lock = threading.Lock()
_loggers_ativos: list["Logger"] = []

def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _agora_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

def _ts_arquivo() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def encerrar_todos_os_loggers():
    with _registro_lock:
        loggers = list(_loggers_ativos)
    for lg in loggers:
        try:
            lg.encerrar()
        except Exception as e:
            print(f"[LOG] Erro ao encerrar logger de '{lg.nome_container}': {e}")

class Logger:
    def __init__(self, nome_container: str):
        self.nome_container = nome_container
        self.inicio = datetime.now(timezone.utc)
        self._ts = _ts_arquivo()

        self._dir_logs = DIR_LOGS_BASE / nome_container
        self._dir_logs.mkdir(parents=True, exist_ok=True)

        self._caminho_log = self._dir_logs / f"ts_{self._ts}.log"
        self._caminho_jsonl = self._dir_logs / f"ts_{self._ts}.jsonl"
        self._caminho_resumo = self._dir_logs / f"ts_{self._ts}.json"

        self._total_coletas = 0
        self._erros = 0
        self._encerrado = False
        self._lock = threading.Lock()

        self._contadores = {"ram": self._novo_contador(), "cpu": self._novo_contador()}
        self._flog = open(self._caminho_log, "a", encoding="utf-8", buffering=1)
        self._fjsonl = open(self._caminho_jsonl, "a", encoding="utf-8", buffering=1)

        self._flog.write(
            f"{'=' * 80}\n"
            f"  SESSÃO INICIADA  {_agora_iso()}\n"
            f"  Container: {nome_container}\n"
            f"{'=' * 80}\n\n"
        )

        print(f"[LOG] Arquivos de sessão criados em '{self._dir_logs}/'")
        print(f"      .log    → {self._caminho_log.name}")
        print(f"      .jsonl  → {self._caminho_jsonl.name}")
        print(f"      resumo  → {self._caminho_resumo.name}\n")

        with _registro_lock:
            _loggers_ativos.append(self)

    @staticmethod
    def _novo_contador() -> dict:
        return {
            "total_escalas": 0,
            "escalas_cima": 0,
            "escalas_baixo": 0,
            "recalibracoes": 0,
            "minimo": float("inf"),
            "maximo": float("-inf"),
            "soma": 0.0,
            "n_amostras": 0,
            "limite_inicial": None,
            "limite_final": None,
            "latencias_docker": [],
            "historico_escala": [],
        }

    def coleta(self, ram_mb: float | None = None, previsao_ram_mb: float | None = None,
               limite_ram_mb: float | None = None, cpu_percent: float | None = None,
               previsao_cpu_pct: float | None = None, limite_cpu_pct: float | None = None) -> None:
        ts = _agora_iso()

        with self._lock:
            self._total_coletas += 1

            if ram_mb is not None:
                c = self._contadores["ram"]
                c["n_amostras"] += 1
                c["soma"] += ram_mb
                c["minimo"] = min(c["minimo"], ram_mb)
                c["maximo"] = max(c["maximo"], ram_mb)
                if c["limite_inicial"] is None:
                    c["limite_inicial"] = limite_ram_mb
                c["limite_final"] = limite_ram_mb

            if cpu_percent is not None:
                c = self._contadores["cpu"]
                c["n_amostras"] += 1
                c["soma"] += cpu_percent
                c["minimo"] = min(c["minimo"], cpu_percent)
                c["maximo"] = max(c["maximo"], cpu_percent)
                if c["limite_inicial"] is None:
                    c["limite_inicial"] = limite_cpu_pct
                c["limite_final"] = limite_cpu_pct

        partes = [f"[{ts}] COLETA      "]
        if ram_mb is not None:
            prev_str = f"{previsao_ram_mb:.2f}" if previsao_ram_mb is not None else "—"
            partes.append(f"RAM={ram_mb:8.2f}MB Prevista={prev_str:>8}MB Limite={limite_ram_mb:.0f}MB  ")
        if cpu_percent is not None:
            prev_str = f"{previsao_cpu_pct:.2f}" if previsao_cpu_pct is not None else "—"
            partes.append(f"CPU={cpu_percent:7.2f}% Prevista={prev_str:>8}% Limite={limite_cpu_pct:.1f}%")

        self._flog.write("".join(partes) + "\n")

        self._gravar_jsonl({
            "tipo": "coleta",
            "ts": ts,
            "ram_mb": round(ram_mb, 3) if ram_mb is not None else None,
            "previsao_ram_mb": round(previsao_ram_mb, 3) if previsao_ram_mb is not None else None,
            "limite_ram_mb": limite_ram_mb,
            "cpu_percent": round(cpu_percent, 3) if cpu_percent is not None else None,
            "previsao_cpu_pct": round(previsao_cpu_pct, 3) if previsao_cpu_pct is not None else None,
            "limite_cpu_pct": limite_cpu_pct,
        })

    def escala(self, recurso: Literal["ram", "cpu"], valor_atual: float, previsao: float,
               limite_antes: float, limite_depois: float, direcao: Literal["cima", "baixo"],
               latencia_ms: float) -> None:
        ts = _agora_iso_ms()
        unidade = "MB" if recurso == "ram" else "%"

        with self._lock:
            c = self._contadores[recurso]
            c["total_escalas"] += 1
            c["limite_final"] = limite_depois
            c["latencias_docker"].append(latencia_ms)
            if direcao == "cima":
                c["escalas_cima"] += 1
            else:
                c["escalas_baixo"] += 1

        seta = "↑ AUMENTOU" if direcao == "cima" else "↓ REDUZIU "
        delta = limite_depois - limite_antes

        self._flog.write(
            f"[{ts}] ESCALA({recurso.upper()}) {seta}  "
            f"Atual={valor_atual:.2f}{unidade}  Prevista={previsao:.2f}{unidade}  "
            f"{limite_antes:.0f} → {limite_depois:.0f}{unidade}  (Δ {delta:+.1f}{unidade})  "
            f"[Docker: {latencia_ms:.1f}ms]\n"
        )

        evento = {
            "tipo": "escala",
            "ts": ts,
            "recurso": recurso,
            "direcao": direcao,
            "valor_atual": round(valor_atual, 3),
            "previsao": round(previsao, 3),
            "limite_antes": limite_antes,
            "limite_depois": limite_depois,
            "delta": delta,
            "latencia_docker_ms": round(latencia_ms, 2),
        }
        self._gravar_jsonl(evento)
        with self._lock:
            self._contadores[recurso]["historico_escala"].append(evento)

    def recalibracao(self, recurso: Literal["ram", "cpu"], ciclo: int, nova_ordem: tuple) -> None:
        ts = _agora_iso()
        with self._lock:
            self._contadores[recurso]["recalibracoes"] += 1

        self._flog.write(
            f"[{ts}] RECALIB({recurso.upper()}) Ciclo={ciclo}  Nova ordem ARIMA={nova_ordem}\n"
        )
        self._gravar_jsonl({
            "tipo": "recalibracao",
            "ts": ts,
            "recurso": recurso,
            "ciclo": ciclo,
            "nova_ordem": list(nova_ordem),
        })

    def erro(self, mensagem: str) -> None:
        ts = _agora_iso()
        with self._lock:
            self._erros += 1
        self._flog.write(f"[{ts}] ERRO        {mensagem}\n")
        self._gravar_jsonl({"tipo": "erro", "ts": ts, "mensagem": mensagem})

    def encerrar(self) -> None:
        with self._lock:
            if self._encerrado:
                return
            self._encerrado = True

        ts = _agora_iso()
        duracao = (datetime.now(timezone.utc) - self.inicio).total_seconds()

        resumo = {
            "container": self.nome_container,
            "inicio": self.inicio.isoformat(timespec="seconds"),
            "fim": ts,
            "duracao_segundos": round(duracao, 1),
            "coletas": self._total_coletas,
            "erros": self._erros,
        }

        for recurso, unidade in (("ram", "mb"), ("cpu", "pct")):
            c = self._contadores[recurso]
            if c["n_amostras"] == 0:
                continue
            media = c["soma"] / c["n_amostras"]
            lats = c["latencias_docker"]
            lat_media = sum(lats) / len(lats) if lats else None
            resumo[recurso] = {
                f"minima_{unidade}": round(c["minimo"], 2),
                f"maxima_{unidade}": round(c["maximo"], 2),
                f"media_{unidade}": round(media, 2),
                "recalibracoes": c["recalibracoes"],
                "escalas": {
                    "total": c["total_escalas"],
                    "cima": c["escalas_cima"],
                    "baixo": c["escalas_baixo"],
                    f"limite_inicial_{unidade}": c["limite_inicial"],
                    f"limite_final_{unidade}": c["limite_final"],
                    "latencia_docker_ms": {
                        "media": round(lat_media, 2) if lat_media is not None else None,
                        "minima": round(min(lats), 2) if lats else None,
                        "maxima": round(max(lats), 2) if lats else None,
                    },
                    "historico": c["historico_escala"],
                },
            }

        with open(self._caminho_resumo, "w", encoding="utf-8") as f:
            json.dump(resumo, f, indent=2, ensure_ascii=False)

        self._flog.write(
            f"\n{'=' * 80}\n"
            f"  SESSÃO ENCERRADA  {ts}\n"
            f"  Duração: {duracao:.0f}s | Coletas: {self._total_coletas} | Erros: {self._erros}\n"
            f"{'=' * 80}\n"
        )

        self._flog.close()
        self._fjsonl.close()

        with _registro_lock:
            if self in _loggers_ativos:
                _loggers_ativos.remove(self)

        print(f"\n[{self.nome_container}] Sessão encerrada. Resumo salvo em '{self._caminho_resumo}'")

    def _gravar_jsonl(self, evento: dict) -> None:
        with self._lock:
            self._fjsonl.write(json.dumps(evento, ensure_ascii=False) + "\n")