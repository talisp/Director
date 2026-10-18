"""Medidas reais separadas do plano. Uma ausencia de medida nunca vira zero."""
import math
from .nucleo import planta as PL


def medir(planta, editor, ids=None, solicitado=None):
    objs = planta["objetos"]
    selecionados = set(ids) if ids is not None else set(objs)
    selecionados.update(objs[i]["sala"] for i in list(selecionados) if i in objs and objs[i].get("sala"))
    saida = {"solicitado": solicitado, "planejado": {i: objs[i] for i in sorted(selecionados) if i in objs},
             "medido": {}, "nao_verificado": ["fisica, circulacao e interacao exigem verificar"],
             "unidades": "centimetros, graus; area em metros quadrados"}
    for sid in sorted(selecionados):
        s = objs.get(sid, {})
        if s.get("tipo") != "sala":
            continue
        origem = [s["x"] + s["largura"] / 2, s["y"] + s["comprimento"] / 2, s["z"] + s["altura"] - 10]
        qs = []
        for eixo, sinal, tamanho in [(0, -1, s["largura"]), (0, 1, s["largura"]), (1, -1, s["comprimento"]), (1, 1, s["comprimento"])]:
            fim = list(origem)
            fim[eixo] += sinal * (tamanho / 2 + s["parede"] + 100)
            qs.append({"tipo": "raio", "de": origem, "ate": fim})
        try:
            hits = editor.chamar("measure", consultas=qs)["medidas"]
            validos = len(hits) == 4 and all(h.get("acertou") is True and h.get("tipo") == "parede"
                       and isinstance(h.get("distancia"), (int, float)) and math.isfinite(h["distancia"]) for h in hits)
            if validos:
                largura = hits[0]["distancia"] + hits[1]["distancia"]
                comprimento = hits[2]["distancia"] + hits[3]["distancia"]
                saida["medido"][sid] = {"largura": round(largura, 3), "comprimento": round(comprimento, 3),
                    "area_m2": round(largura * comprimento / 10000, 4), "metodo": "quatro raios internos abaixo do teto",
                    "confere_com_planta": abs(largura-s["largura"]) <= 2 and abs(comprimento-s["comprimento"]) <= 2,
                    "acertos": hits}
            else:
                saida["nao_verificado"].append({"id": sid, "motivo": "quatro paredes nao confirmadas pelos raios", "acertos": hits})
        except Exception as exc:
            saida["nao_verificado"].append({"id": sid, "motivo": str(exc)})
    return saida


def consultar(cena, editor, raiz, ids=None):
    p = PL.carregar(raiz, cena)
    if editor.chamar("info")["level"] != p["nivel"]:
        raise ValueError("a cena precisa estar aberta; relatorio nao troca level")
    return {"ok": True, "cena": cena, **medir(p, editor, ids)}
