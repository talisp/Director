#!/usr/bin/env python3
"""Mede, no log do Hermes, se o Qwen erra mais quando o contexto cresce. Só lê o log; stdlib.

Para uma sessão: tamanho do contexto (tokens de entrada) a cada chamada e, por faixa de contexto, quantas chamadas
houve e quantos erros de USO de ferramenta (campo faltando, sobrescrita recusada, aviso de repetição). Erro de
RESULTADO (um teste que reprova, um comando que sai com código 1) é contado à parte: não é sinal de cansaço.

Uso: python medir_contexto.py [SESSAO] [--log CAMINHO] [--faixa TOKENS]
     sem SESSAO: a última sessão que aparece no log.
"""
from __future__ import annotations
import argparse
import os
import re
import sys
from pathlib import Path

CHAMADA = re.compile(r"\[(?P<s>[\w.-]+)\] agent\.conversation_loop: API call #\d+: .*?\bin=(?P<in>\d+)")
ERRO = re.compile(r"\[(?P<s>[\w.-]+)\] agent\.tool_executor: Tool (?P<t>\S+) returned error .*?: (?P<msg>.*)")
REPETICAO = re.compile(r"\[(?P<s>[\w.-]+)\] .*(Tool loop warning|same_tool_failure)")
USO = ("missing required", "refusing to overwrite", "unknown tool", "invalid arguments", "not valid json", "tool loop warning")


def log_padrao() -> Path:
    home = os.environ.get("HERMES_HOME") or str(Path.home() / "AppData" / "Local" / "hermes" / "profiles" / "hermes-dev")
    return Path(home) / "logs" / "agent.log"


def medir(linhas, sessao: str | None, faixa: int) -> dict:
    eventos, ultima = [], None
    for linha in linhas:
        m = CHAMADA.search(linha)
        if m:
            ultima = m["s"]
            eventos.append(("chamada", m["s"], int(m["in"])))
            continue
        m = ERRO.search(linha)
        if m:
            tipo = "uso" if any(u in m["msg"].lower() for u in USO) else "resultado"
            eventos.append((tipo, m["s"], m["t"]))
            continue
        m = REPETICAO.search(linha)
        if m:
            eventos.append(("uso", m["s"], "repeticao"))
    sessao = sessao or ultima
    if sessao is None:
        return {"sessao": None, "chamadas": 0, "faixas": []}
    contexto, faixas = 0, {}
    for tipo, s, valor in eventos:
        if not s.startswith(sessao):
            continue
        if tipo == "chamada":
            contexto = valor
        f = faixas.setdefault(contexto // faixa, {"chamadas": 0, "uso": 0, "resultado": 0})
        if tipo == "chamada":
            f["chamadas"] += 1
        else:
            f[tipo] += 1
    tamanhos = [v for t, s, v in eventos if t == "chamada" and s.startswith(sessao)]
    return {"sessao": sessao, "chamadas": len(tamanhos), "contexto_max": max(tamanhos, default=0),
            "faixas": [{"de": k * faixa, "ate": (k + 1) * faixa, **v} for k, v in sorted(faixas.items())]}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("sessao", nargs="?")
    p.add_argument("--log", type=Path, default=None)
    p.add_argument("--faixa", type=int, default=50000)
    a = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    log = a.log or log_padrao()
    if not log.is_file():
        print("ERRO: log não encontrado:", log, file=sys.stderr)
        return 2
    r = medir(log.read_text(encoding="utf-8", errors="replace").splitlines(), a.sessao, a.faixa)
    if not r["chamadas"]:
        print("Nenhuma chamada encontrada para a sessão", r["sessao"])
        return 1
    maximo = f"{r['contexto_max']:,}".replace(",", ".")
    print(f"Sessão {r['sessao'][:24]}…: {r['chamadas']} chamadas, contexto máximo {maximo} tokens")
    print("| contexto (mil tokens) | chamadas | erros de uso | erros de uso por chamada | erros de resultado |")
    print("|---|---:|---:|---:|---:|")
    for f in r["faixas"]:
        taxa = f["uso"] / f["chamadas"] if f["chamadas"] else 0.0
        print(f"| {f['de'] // 1000}–{f['ate'] // 1000} | {f['chamadas']} | {f['uso']} | {taxa:.2f} | {f['resultado']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
