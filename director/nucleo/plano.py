"""Comparar a planta com o que está no Unreal. Só conta, sem Unreal.

- `conciliar`: alguém mexeu à mão no editor? O que dá para adotar entra na planta (quem mexeu ganha).
- `planejar`: lista mínima de ações (criar, atualizar, remover) para o Unreal ficar igual às peças derivadas.
  Peça que já está certa não entra na lista. Peça que existe é atualizada, não recriada.
- `diferencas`: a conferência depois de aplicar (lista vazia = igual).
"""
import copy

from . import derivar as D
from .operacoes import MOVEIS, OBJETOS, levar_junto

TOL_CM = 0.05
TOL_GRAUS = 0.05
TOL_PARAM = 0.01
TOL_ESCALA = 0.001


def _dif_angulo(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _loc_difere(a, b) -> bool:
    return any(abs(x - y) > TOL_CM for x, y in zip(a, b))


def _rot_difere(a, b) -> bool:
    return any(_dif_angulo(x, y) > TOL_GRAUS for x, y in zip(a, b))


def _escala_difere(a, b) -> bool:
    return any(abs(x - y) > TOL_ESCALA for x, y in zip(a, b))


def _params_diferentes(alvo: dict, real: dict) -> dict:
    return {k: v for k, v in alvo.items() if abs(v - real.get(k, float("nan"))) > TOL_PARAM or k not in real}


def diferencas(alvo: dict, controlados: dict) -> list:
    """O que ainda difere entre as peças derivadas e o inventário do Unreal."""
    difs = []
    for pid, p in alvo.items():
        r = controlados.get(pid)
        if r is None:
            difs.append({"id": pid, "o_que": "falta"})
            continue
        if r["classe"] != p["classe"]:
            difs.append({"id": pid, "o_que": "classe", "alvo": p["classe"], "real": r["classe"]})
        if _loc_difere(p["loc"], r["loc"]):
            difs.append({"id": pid, "o_que": "loc", "alvo": p["loc"], "real": r["loc"]})
        if _rot_difere(p["rot"], r["rot"]):
            difs.append({"id": pid, "o_que": "rot", "alvo": p["rot"], "real": r["rot"]})
        if _escala_difere(p["escala"], r["escala"]):
            difs.append({"id": pid, "o_que": "escala", "alvo": p["escala"], "real": r["escala"]})
        errados = _params_diferentes(p["params"], r.get("params", {}))
        if errados:
            difs.append({"id": pid, "o_que": "params", "alvo": errados, "real": {k: r.get("params", {}).get(k) for k in errados}})
        if _objeto_difere(p,r): difs.append({"id":pid,"o_que":"objeto","alvo":p.get("objeto"),"real":r.get("objeto")})
    for pid in controlados:
        if pid not in alvo:
            difs.append({"id": pid, "o_que": "sobra"})
    return difs


def _objeto_difere(p,r):
    for k,v in p.get("objeto",{}).items():
        if k in ("adotar","duplicar","converter"): continue
        atual=r.get("objeto",{}).get(k)
        if isinstance(v,(int,float)) and not isinstance(v,bool):
            if atual is None or abs(v-atual)>.02: return True
        elif v!=atual: return True
    return False


def planejar(alvo: dict, controlados: dict) -> list:
    """Ações mínimas, na ordem: remover o que sobra, atualizar o que mudou, criar o que falta."""
    remover, atualizar, criar = [], [], []
    for pid in sorted(controlados):
        if pid not in alvo:
            remover.append({"acao": "remover", "id": pid})
    for pid, p in alvo.items():
        r = controlados.get(pid)
        if r is None:
            criar.append({"acao": "criar", "id": pid, "tipo": p["tipo"], "classe": p["classe"], "loc": p["loc"], "rot": p["rot"],
                          "escala": p["escala"], "params": p["params"], **({"objeto":p["objeto"]} if "objeto" in p else {})})
            continue
        if r["classe"] != p["classe"]:  # recriação controlada: o identificador é o mesmo, o ator é outro
            remover.append({"acao": "remover", "id": pid})
            criar.append({"acao": "criar", "id": pid, "tipo": p["tipo"], "classe": p["classe"], "loc": p["loc"], "rot": p["rot"],
                          "escala": p["escala"], "params": p["params"], "recriada": True, **({"objeto":p["objeto"]} if "objeto" in p else {})})
            continue
        a = {"acao": "atualizar", "id": pid, "tipo": p["tipo"]}
        if _loc_difere(p["loc"], r["loc"]) or _rot_difere(p["rot"], r["rot"]):
            a["loc"], a["rot"] = p["loc"], p["rot"]
        if _escala_difere(p["escala"], r["escala"]):
            a["escala"] = p["escala"]
        errados = _params_diferentes(p["params"], r.get("params", {}))
        if errados:
            a["params"] = errados
        if _objeto_difere(p,r): a["objeto"]=p["objeto"]
        if len(a) > 3:
            atualizar.append(a)
    return remover + atualizar + criar


def conciliar(planta: dict, controlados: dict) -> tuple:
    """Devolve (planta com as edições manuais adotadas, relatório).

    Adota: lugar, giro e medidas de mesa; lugar e giro de prato e copo; ângulo da porta.
    Não adota (o Director repõe na próxima mudança e avisa): estrutura (piso, paredes, navegação, lugar da porta e da
    janela, que são da parede). Peça apagada à mão vai para `faltando`: quem decide é a pessoa (operação `remover`)."""
    nova = copy.deepcopy(planta)
    rel = {"adotados": [], "estrutura_divergente": [], "faltando": [], "sobrando": []}
    alvo = D.derivar(planta)
    for pid, p in alvo.items():
        r = controlados.get(pid)
        if r is None:
            rel["faltando"].append(pid)
            continue
        o = nova["objetos"].get(pid)
        tipo = o["tipo"] if o else None
        mudou_lugar = _loc_difere(p["loc"], r["loc"]) or _rot_difere(p["rot"], r["rot"])
        errados = _params_diferentes(p["params"], r.get("params", {}))
        if tipo == "asset":
            if mudou_lugar or _escala_difere(p["escala"],r["escala"]):
                import math
                m=o["modelo"];es=r["escala"];g=math.radians(r["rot"][1]);cx=m["centro"][0]*es[0];cy=m["centro"][1]*es[1]
                o.update(x=r["loc"][0]+cx*math.cos(g)-cy*math.sin(g),y=r["loc"][1]+cx*math.sin(g)+cy*math.cos(g),z=r["loc"][2]+m["min_z"]*es[2],giro=r["rot"][1])
                for j,k in enumerate(("largura","profundidade","altura")): o[k]=m["tamanho"][j]*es[j]
                rel["adotados"].append({"id":pid,"campo":"transformacao_asset"})
        elif tipo in MOVEIS:
            antes = dict(o)
            if mudou_lugar:
                o["x"], o["y"], o["giro"] = r["loc"][0], r["loc"][1], r["rot"][1]
                rel["adotados"].append({"id": pid, "campo": "lugar", "de": p["loc"][:2] + [p["rot"][1]], "para": r["loc"][:2] + [r["rot"][1]]})
            for var, chave in (("Largura", "largura"), ("Profundidade", "profundidade"), ("Altura", "altura")):
                if var in errados:
                    o[chave] = r["params"][var]
                    rel["adotados"].append({"id": pid, "campo": chave, "de": p["params"][var], "para": r["params"][var]})
            if o != antes:
                rel["levados_junto"] = rel.get("levados_junto", []) + levar_junto(nova, pid, antes, o)
        elif tipo in OBJETOS:
            if mudou_lugar:
                o["x"], o["y"], o["z"], o["rot"] = r["loc"][0], r["loc"][1], r["loc"][2], list(r["rot"])
                rel["adotados"].append({"id": pid, "campo": "lugar", "de": p["loc"], "para": r["loc"]})
            for var, chave in (("Diametro", "diametro"), ("Altura", "altura")):
                if var in errados:
                    o[chave] = r["params"][var]
                    rel["adotados"].append({"id": pid, "campo": chave, "de": p["params"][var], "para": r["params"][var]})
        elif tipo == "porta" and "Angulo" in errados:
            from . import portas
            antes = o['angulo']
            o["angulo"] = r["params"]["Angulo"] * portas.sinal(o)
            rel["adotados"].append({"id": pid, "campo": "angulo", "de": antes, "para": o['angulo']})
            if mudou_lugar or len(errados) > 1:
                rel["estrutura_divergente"].append(pid)
        elif mudou_lugar or errados or _escala_difere(p["escala"], r["escala"]):
            rel["estrutura_divergente"].append(pid)
    rel["sobrando"] = sorted(pid for pid in controlados if pid not in alvo)
    return nova, rel
