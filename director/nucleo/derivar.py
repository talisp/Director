"""Da planta para as peças: que atores o Unreal tem de ter, onde, e com que parâmetros. Só conta, sem Unreal.

A planta guarda objetos lógicos (sala, porta, janela, mesa, prato, copo). Aqui cada um vira uma ou mais PEÇAS
(atores), cada peça com identificador estável:
- sala `s`  -> `s.piso`, `s.parede_sul` (e `_2`, `_3`... se a parede tem mais de um vão), `s.parede_norte`,
               `s.parede_leste`, `s.parede_oeste`, `s.nav` (volume de navegação do motor);
- porta, janela, mesa, prato, copo -> uma peça com o mesmo nome do objeto.
Uma parede com vão é a mesma peça com os parâmetros do vão: o vão não é um ator à parte.
Duas salas encostadas (a uma parede de distância) dividem a parede: ela sai uma vez só, com o nome da primeira sala
em ordem alfabética, e o vão posto por qualquer das duas corta essa parede.
"""
from . import pecas as P
import math
from .operacoes import VAOS, trechos_de_parede, vao_no_mundo,material_do_trecho
from . import portas

MARGEM_NAV = 300.0  # cm de área navegável em volta da sala (para o personagem chegar pela porta)
FOLGA_NAV_Z = 100.0
ESPESSURA_PISO = 10.0

# parede -> (direção no mundo em que ela corre, giro do ator)
_CORRE = {"sul": ((1.0, 0.0), 0.0), "norte": ((1.0, 0.0), 0.0), "leste": ((0.0, 1.0), 90.0), "oeste": ((0.0, 1.0), 90.0)}


def _linha_da_parede(s: dict, lado: str) -> tuple:
    """(origem x, y do EIXO da parede no canto interno de onde se mede a posição; avanço antes do canto interno)."""
    t = s["parede"]
    if lado == "sul":
        return s["x"], s["y"] - t / 2, t
    if lado == "norte":
        return s["x"], s["y"] + s["comprimento"] + t / 2, t
    if lado == "leste":
        return s["x"] + s["largura"] + t / 2, s["y"], 0.0
    return s["x"] - t / 2, s["y"], 0.0


def _peca(tipo: str, loc, giro: float, params: dict, escala=None, rot=None) -> dict:
    return {"tipo": tipo, "classe": P.classe_de(tipo), "loc": [float(v) for v in loc],
            "rot": [float(v) for v in rot] if rot is not None else [0.0, float(giro), 0.0],
            "escala": [float(v) for v in escala] if escala else [1.0, 1.0, 1.0],
            "params": {k: float(v) for k, v in params.items()}}


def _paredes(planta: dict) -> dict:
    """As paredes de todas as salas. A parede em comum de duas salas encostadas sai uma vez só (`trechos_de_parede`),
    com o nome da primeira sala; cada vão divide a parede em pedaços, um vão por pedaço."""
    objs = planta["objetos"]
    saida, contagem = {}, {}
    for tr in trechos_de_parede(planta):
        s = objs[tr["sala"]]
        (dx, dy), giro = _CORRE[tr["lado"]]
        meio = (tr["chave"][1] + tr["chave"][2]) / 2  # eixo da parede, no outro sentido
        meus = sorted(((vao_no_mundo(planta, objs[v]), objs[v]) for v in tr["vaos"]), key=lambda par: par[0][1])
        cortes = [tr["ini"]] + [(a[0][2] + b[0][1]) / 2 for a, b in zip(meus, meus[1:])] + [tr["fim"]]
        for n, (ini, fim) in enumerate(zip(cortes, cortes[1:])):
            (_, vi, vf), v = meus[n] if meus else ((None, 0.0, 0.0), None)
            params = {"Comprimento": fim - ini, "Altura": tr["altura"], "Espessura": s["parede"],
                      "VaoLargura": v["largura"] if v else 0.0, "VaoCentro": (vi + vf) / 2 - ini if v else 0.0,
                      "VaoBase": v.get("peitoril", 0.0) if v else 0.0, "VaoAltura": v["altura"] if v else 0.0}
            base = f"{tr['sala']}.parede_{tr['lado']}"
            contagem[base] = contagem.get(base, 0) + 1
            nome = base + (f"_{contagem[base]}" if contagem[base] > 1 else "")
            loc = (ini, meio) if dx else (meio, ini)
            saida[nome] = _peca("parede", (loc[0], loc[1], s["z"]), giro, params)
            material=material_do_trecho(planta,tr)
            if material:saida[nome]['material']=material
            if v and v['tipo']=='passagem':
                saida[nome]['passagem']=next(vid for vid in tr['vaos'] if objs[vid] is v)
    return saida


def _vao(o: dict, s: dict) -> dict:
    """Porta ou janela, encaixada no vão da parede. A porta abre sempre para dentro da sala."""
    lado = o["parede"]
    (dx, dy), giro = _CORRE[lado]
    ox, oy, _ = _linha_da_parede(s, lado)
    ini, fim = o["posicao"] - o["largura"] / 2, o["posicao"] + o["largura"] / 2
    z = s["z"] + o.get("peitoril", 0.0)
    if o["tipo"] == "janela":
        return _peca("janela", (ox + dx * ini, oy + dy * ini, z), giro, {"Largura": o["largura"], "Altura": o["altura"]})
    # a folha gira para o +Y local da peça: nas paredes norte e oeste o +Y do giro da parede aponta para fora,
    # então a dobradiça vai para a outra ponta do vão e a peça gira 180 graus
    if portas.dobradica(o) == 'fim':
        ancora, giro = fim, giro + 180.0
    else:
        ancora = ini
    return _peca("porta", (ox + dx * ancora, oy + dy * ancora, z), giro,
                 {"Largura": o["largura"], "Altura": o["altura"], "Angulo": o["angulo"] * portas.sinal(o)})


def derivar(planta: dict) -> dict:
    """identificador -> peça {tipo, classe, loc, rot, escala, params}."""
    objs = planta["objetos"]
    saida = {}
    for oid, o in objs.items():
        t = o["tipo"]
        if t == "sala":
            esp = o["parede"]
            saida[f"{oid}.piso"] = _peca("piso", (o["x"] - esp, o["y"] - esp, o["z"]), 0.0,
                                         {"Largura": o["largura"] + 2 * esp, "Comprimento": o["comprimento"] + 2 * esp,
                                          "Espessura": ESPESSURA_PISO})
            if o.get('teto'):
                saida[f'{oid}.teto']=_peca('piso',(o['x']+o['largura']+esp,o['y']-esp,o['z']+o['altura']),0,
                    {'Largura':o['largura']+2*esp,'Comprimento':o['comprimento']+2*esp,'Espessura':ESPESSURA_PISO},rot=[0,180,180])
            for alvo in ('piso','teto'):
                if f'{oid}.{alvo}' in saida and alvo in o.get('materiais',{}):
                    saida[f'{oid}.{alvo}']['material']=o['materiais'][alvo]['caminho']
            base = P.NATIVAS["nav"]["caixa_base"]
            tam = (o["largura"] + 2 * MARGEM_NAV, o["comprimento"] + 2 * MARGEM_NAV, o["altura"] + 2 * FOLGA_NAV_Z)
            saida[f"{oid}.nav"] = _peca("nav", (o["x"] + o["largura"] / 2, o["y"] + o["comprimento"] / 2, o["z"] + o["altura"] / 2),
                                        0.0, {}, escala=[v / base for v in tam])
        elif t in VAOS:
            if t!='passagem':saida[oid] = _vao(o, objs[o["sala"]])
        elif t == "asset":
            m=o["modelo"]; escala=[o[k]/m["tamanho"][i] for i,k in enumerate(("largura","profundidade","altura"))]
            cx,cy=[m["centro"][i]*escala[i] for i in (0,1)]
            g=math.radians(o["giro"])
            loc=[o["x"]-cx*math.cos(g)+cy*math.sin(g),o["y"]-cx*math.sin(g)-cy*math.cos(g),o["z"]-m["min_z"]*escala[2]]
            saida[oid]={"tipo":"asset","classe":o.get("classe","/Script/Engine.StaticMeshActor"),"loc":loc,
                "rot":[0.0,o["giro"],0.0],"escala":escala,"params":{},
                "objeto":{"asset":m["asset"],**o["fisica"],**{k:o[k] for k in ("adotar","duplicar","converter") if k in o}}}
        elif t == "mesa":
            saida[oid] = _peca("mesa", (o["x"], o["y"], objs[o["sala"]]["z"]), o["giro"],
                               {"Largura": o["largura"], "Profundidade": o["profundidade"], "Altura": o["altura"]})
        else:  # prato, copo: a peça é o corpo físico genérico; o tamanho é parâmetro e também a escala do ator
            d, a = o["diametro"], o["altura"]
            saida[oid] = _peca("objeto", (o["x"], o["y"], o["z"]), 0.0, {"Diametro": d, "Altura": a},
                               escala=[d / 100.0, d / 100.0, a / 100.0], rot=o["rot"])
    saida.update(_paredes(planta))
    return saida


def dono(planta: dict, peca_id: str) -> str:
    """De que objeto da planta é esta peça."""
    return peca_id if peca_id in planta["objetos"] else peca_id.split(".")[0]
