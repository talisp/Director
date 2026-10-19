"""Guarda do Director no Hermes: repara perguntas do clarify, limita esperas a 60 s e impede duas alteracoes na mesma cena ao mesmo tempo."""
from __future__ import annotations

import json
import math
import re
from typing import Any, Optional


def _ler_json(texto: str):
    """Lê o JSON inicial, tolerando erros de fechamento já observados no Qwen."""
    t = texto.strip()
    for tentativa in (t, t + "]", t + "}]"):
        try:
            return json.JSONDecoder().raw_decode(tentativa)[0]
        except ValueError:
            pass
    raise ValueError("não é JSON")


def consertar_perguntas(args: Any) -> Optional[dict]:
    """Devolve argumentos reparados ou None quando não há reparo seguro."""
    if not isinstance(args, dict):
        return None
    q = args.get("questions")
    mudou = False
    if isinstance(q, str):
        try:
            q = _ler_json(q)
        except ValueError:
            return None
        mudou = True
    if isinstance(q, dict):
        q, mudou = (q["questions"] if isinstance(q.get("questions"), list) else [q]), True
    if not isinstance(q, list):
        return None
    itens = []
    for item in q:
        if isinstance(item, str):
            try:
                item, mudou = _ler_json(item), True
            except ValueError:
                item, mudou = {"question": item}, True
        if isinstance(item, list):
            itens.extend(item)
            mudou = True
        else:
            itens.append(item)
    novas = []
    for item in itens:
        if isinstance(item, str):
            item, mudou = {"question": item}, True
        if not isinstance(item, dict):
            return None
        item = dict(item)
        ops = item.get("choices")
        if isinstance(ops, str):
            try:
                ops, mudou = _ler_json(ops), True
            except ValueError:
                ops = None
        if isinstance(ops, list):
            limpas = []
            for c in ops:
                if isinstance(c, dict):
                    c, mudou = str(c.get("label") or c.get("text") or c.get("value") or "").strip(), True
                limpas.append(c if isinstance(c, str) else str(c))
            item["choices"] = [c for c in limpas if c]
        novas.append(item)
    return {"questions": novas} if mudou else None


# Esperas: no máximo 60 s cada (ordem do Talis, 17/10; issue #38 do Director).
ESPERA_MAX_S = 60
_SLEEP = re.compile(r"\b(?:sleep|Start-Sleep(?:\s+-Seconds)?|timeout\s+/t)\s+(\d+(?:\.\d+)?)([smhd]?)\b", re.I)
_TIME_SLEEP = re.compile(r"\btime\.sleep\(\s*(\d+(?:\.\d+)?)\s*\)")
_UNIDADE = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}

# Comandos do Director que mexem no editor. Cena "*" = qualquer cena (navegação, peças, script no editor).
_DIRECTOR = re.compile(r"-m\s+director\s+(fazer|objeto|verificar|revisar|material|incorporar|preparar|navegacao|pecas|ensaio\s+executar)\b\s*([^\s;|&>\"']*)")
_POR_CENA = {"fazer", "objeto", "verificar", "revisar", "material", "incorporar", "preparar"}


def maior_espera(texto: str) -> float:
    """A maior espera fixa (segundos) escrita num comando ou código; 0 se não houver."""
    maior = 0.0
    for n, u in _SLEEP.findall(texto or ""):
        maior = max(maior, float(n) * _UNIDADE[u.lower()])
    for n in _TIME_SLEEP.findall(texto or ""):
        maior = max(maior, float(n))
    return maior


def cenas_alteradas(texto: str) -> set:
    """Cenas que o comando altera pelo Director ("*" quando atinge o editor inteiro)."""
    cenas = set()
    for modo, cena in _DIRECTOR.findall(texto or ""):
        modo = modo.split()[0]
        cenas.add(cena if modo in _POR_CENA and cena and not cena.startswith("$") else "*")
    return cenas


def _processos_rodando() -> list:
    """Comandos em segundo plano ainda vivos no Hermes; vazio se a consulta não existir nesta versão."""
    try:
        from tools.process_registry import process_registry as R
        vivos = []
        R._any_running(lambda s: vivos.append(s.command) and False)
        return vivos
    except Exception:
        return []


def _conflito(cenas: set, rodando: list) -> Optional[str]:
    for cmd in rodando:
        outras = cenas_alteradas(cmd)
        if outras and ("*" in cenas or "*" in outras or cenas & outras):
            return cmd
    return None


def _regra(nome: str, args: Any, rodando=None) -> Optional[dict]:
    """Uma chamada de ferramenta: devolve block/modify ou None."""
    args = args if isinstance(args, dict) else {}
    if nome == "clarify":
        novos = consertar_perguntas(args)
        return {"action": "modify", "args": novos} if novos else None
    if nome in ("process", "process_manage") and args.get("action") == "wait":
        # Hermes instalado: PROCESS_SCHEMA e _SESSION_ACTIONS usam `timeout`.
        # `timeout_seconds` era ignorado e deixava prevalecer o padrao de 180 s.
        t = args.get("timeout", args.get("timeout_seconds", ESPERA_MAX_S))
        try:
            numero = float(t)
        except (TypeError, ValueError):
            numero = 0
        if not math.isfinite(numero) or numero < 1:
            return {"action": "block", "message": "Espera invalida: use process_manage wait com timeout inteiro entre 1 e 60 segundos."}
        novos = {k: v for k, v in args.items() if k != "timeout_seconds"}
        novos["timeout"] = min(int(numero), ESPERA_MAX_S)
        if novos != args:
            return {"action": "modify", "args": novos}
        return None
    texto = args.get("command") if nome == "terminal" else args.get("code") if nome == "execute_code" else None
    if not isinstance(texto, str):
        return None
    espera = maior_espera(texto)
    if espera > ESPERA_MAX_S:
        return {"action": "block", "message": (
            f"Bloqueado pela guarda do Director: espera fixa de {espera:g} s. Cada espera pode ter no máximo "
            f"{ESPERA_MAX_S} s (regra do Talis). Para acompanhar um processo em segundo plano, use "
            f"process_manage(action='wait', timeout={ESPERA_MAX_S}) e confira o resultado entre as esperas; "
            "quando ele terminar antes, continue na hora. Antes de esperar, diga no chat o que está esperando.")}
    cenas = cenas_alteradas(texto)
    if cenas:
        outro = _conflito(cenas, _processos_rodando() if rodando is None else rodando)
        if outro:
            return {"action": "block", "message": (
                "Bloqueado pela guarda do Director: já existe um processo em segundo plano alterando a mesma cena "
                f"({outro[:160]!r}). Duas alterações ao mesmo tempo misturam tamanhos e resultados. Espere esse "
                "processo terminar (process wait, até 60 s por vez) ou pare-o com process kill e confira o estado "
                "da cena antes de começar outro. Para testar tamanhos, use planejar com sala + minimo_cm/maximo_cm, "
                "que não muda a cena.")}
    return None


def _antes_da_ferramenta(tool_name: str = "", args: Any = None, **_: Any) -> Optional[dict]:
    if tool_name != "tool_call":
        return _regra(tool_name, args)
    # Chamadas embrulhadas em tool_call: aplica a regra a cada uma.
    calls = args.get("calls") if isinstance(args, dict) else None
    if isinstance(calls, str):
        try:
            calls = _ler_json(calls)
        except ValueError:
            return None
    if not isinstance(calls, list):
        return None
    novas, mudou = [], False
    for c in calls:
        if not isinstance(c, dict):
            novas.append(c)
            continue
        r = _regra(c.get("name", ""), c.get("arguments"))
        if r and r["action"] == "block":
            return r
        if r and r["action"] == "modify":
            c, mudou = {**c, "arguments": r["args"]}, True
        novas.append(c)
    return {"action": "modify", "args": {**args, "calls": novas}} if mudou else None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _antes_da_ferramenta)
