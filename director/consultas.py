"""Observação e medidas para agentes. Consultas não abrem levels nem alteram a planta."""
import math
import os

from .nucleo import derivar as D, pecas as P, plano as PN, planta as PL, operacoes as OP


def _nivel(cena, editor, raiz_cenas):
    p = PL.carregar(raiz_cenas, cena)
    info = editor.chamar("info")
    if info["level"] != p["nivel"]:
        raise ValueError(f"a cena {cena} nao esta aberta; level atual: {info['level']}")
    return p


def _caixa(atores):
    caixas = [a["caixa"] for a in atores if "caixa" in a]
    if not caixas:
        return None
    return {"min": [min(c["centro"][i] - c["meia_extensao"][i] for c in caixas) for i in range(3)],
            "max": [max(c["centro"][i] + c["meia_extensao"][i] for c in caixas) for i in range(3)]}


def observar(cena, editor, raiz_cenas, ids=()):
    p = PL.carregar(raiz_cenas, cena)
    if not os.path.exists(PL.caminho(raiz_cenas, cena)):
        return {"ok": True, "cena": cena, "existe": False,
                "como_criar": "fazer CENA FICHA.json cria a cena automaticamente; nao e preciso cria-la antes"}
    desejados = p["objetos"]
    faltam = set(ids) - desejados.keys()
    if faltam:
        raise ValueError("identificadores desconhecidos: " + ", ".join(sorted(faltam)))
    _nivel(cena, editor, raiz_cenas)
    inv = editor.chamar("inventory", variaveis=P.variaveis(), detalhes=True)
    selecionados = set(ids) if ids else set(desejados)
    selecionados.update(i for i, o in desejados.items() if o.get("sala") in selecionados)
    objetos = {}
    for oid in sorted(selecionados):
        reais = {pid: a for pid, a in inv["controlados"].items() if D.dono(p, pid) == oid and a["tipo"] != "nav"}
        r = {"caixa": _caixa(reais.values()), "atores": sorted(reais)}
        if len(reais) == 1:
            a = next(iter(reais.values()))
            r.update({k: a[k] for k in ("loc", "rot", "pontos") if k in a})
        if ids:
            r["detalhes"] = reais
        objetos[oid] = {"tipo": desejados[oid]["tipo"],
                        "planejado": {k: v for k, v in desejados[oid].items() if k != "tipo"}, "real": r}
    return {"ok": True, "cena": cena, "existe": True, "revisao": p["revisao"], "unidades": "centimetros e graus",
            "avisos": OP.avisos(p),
            "objetos": objetos, "diferencas": PN.diferencas(D.derivar(p), inv["controlados"]),
            "navegacao": editor.chamar("measure", consultas=[{"tipo": "nav"}])["medidas"][0],
            "outros_atores": len(inv["fora"]), "por_salvar": inv["por_salvar"],
            "limite": "caixa envolve componentes com colisao; nao e largura livre nem prova de interacao; use medir"}


def medir(cena, pedido, editor, raiz_cenas):
    if isinstance(pedido, list):
        pedido = {"consultas": pedido}
    if not isinstance(pedido, dict) or set(pedido) - {"consultas", "mundo"}:
        raise ValueError("use uma lista ou {consultas: [...], mundo: editor|jogo}")
    qs, mundo = pedido.get("consultas"), pedido.get("mundo", "editor")
    if mundo not in ("editor", "jogo") or not isinstance(qs, list) or not qs:
        raise ValueError("consultas deve ser uma lista nao vazia; mundo e editor ou jogo")
    for c in qs:
        if not isinstance(c, dict) or c.get("tipo") not in ("raio", "varredura", "caminho", "nav"):
            raise ValueError("tipos: raio, varredura, caminho, nav")
        if c["tipo"] != "nav":
            for nome in ("de", "ate"):
                v = c.get(nome)
                if (not isinstance(v, list) or len(v) != 3 or
                        not all(type(n) in (int, float) and math.isfinite(n) for n in v)):
                    raise ValueError(f"{nome} deve ter tres numeros finitos em centimetros")
        if c["tipo"] == "varredura":
            raio, metade = c.get("raio", 34.0), c.get("meia_altura", 88.0)
            if not all(type(n) in (int, float) and math.isfinite(n) for n in (raio, metade)) or not 0 < raio <= metade:
                raise ValueError("varredura exige 0 < raio <= meia_altura, em centimetros; de/ate sao centros da capsula")
    _nivel(cena, editor, raiz_cenas)
    res = editor.chamar("measure", consultas=qs, mundo=mundo)
    for q, m in zip(qs, res["medidas"]):
        if q["tipo"] == "caminho":
            m["completo"] = bool(m.get("existe")) and m.get("parcial") is False
        elif q["tipo"] == "varredura":
            m["livre"] = not m["acertou"]
    return {"ok": True, "cena": cena, "unidades": "centimetros", "mundo": mundo,
            "consultas": qs, "medidas": res["medidas"]}
