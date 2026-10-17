"""Compatibilidade de perguntas da ferramenta clarify com o modelo local."""
from __future__ import annotations

import json
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


def _antes_da_ferramenta(tool_name: str = "", args: Any = None, **_: Any) -> Optional[dict]:
    if tool_name == "clarify":
        novos = consertar_perguntas(args)
        return {"action": "modify", "args": novos} if novos else None
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _antes_da_ferramenta)
