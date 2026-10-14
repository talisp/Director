"""Demonstração da primeira entrega: os três comandos e as medidas de aceite (critérios A a F do pedido de 13/10).

Uso, na raiz:  venv\\Scripts\\python.exe -m director.demonstracao ETAPA [CENA]
Etapas, nesta ordem: c1 | manual | c2 | c3 | fisica | incorporar | persistencia | seguranca
Cada etapa grava o que mediu em work\\director\\demo\\CENA\\ETAPA.json e imprime um resumo.

Os comandos passam pelo executor do núcleo (o mesmo de `-m director fazer`). As medidas são do próprio Unreal
(raios, varredura de cápsula, caminho de navegação, física e o Character do motor); as réguas estão em nucleo/regua.py.
"""
import json
import os
import sys
import time

from . import config as C
from . import lab, ponte
from .nucleo import derivar as D
from .nucleo import executor as X
from .nucleo import pecas as P
from .nucleo import planta as PL
from .nucleo import regua as R

FICHAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fichas")
PONTOS = os.path.join(C.WORK, "restauracao")
CAPSULA = {"raio": 34.0, "meia_altura": 88.0}  # a do Character do motor


def _ficha(n: int) -> dict:
    with open(os.path.join(FICHAS, f"comando{n}.json"), encoding="utf-8") as f:
        return json.load(f)


def _gravar(cena: str, etapa: str, dados: dict) -> None:
    pasta = os.path.join(C.WORK, "demo", cena)
    os.makedirs(pasta, exist_ok=True)
    with open(os.path.join(pasta, etapa + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(dados, f, ensure_ascii=False, indent=1)


def _fazer(p, cena: str, ficha: dict) -> dict:
    return X.executar(cena, ficha, p, C.CENAS, C.LAB_DIR, PONTOS)


def _inv(p) -> dict:
    return p.chamar("inventory", variaveis=P.variaveis())


def _medir(p, consultas: list, mundo: str = "editor") -> list:
    return p.chamar("measure", consultas=consultas, mundo=mundo)["medidas"]


def _sala(planta: dict) -> dict:
    return next(o for o in planta["objetos"].values() if o["tipo"] == "sala")


def _vao_no_mundo(planta: dict, oid: str) -> tuple:
    """(ponto de fora, ponto de dentro) a 120 cm do eixo da parede, na frente do meio do vão, ao nível do chão."""
    o, s = planta["objetos"][oid], _sala(planta)
    t = s["parede"]
    if o["parede"] in ("sul", "norte"):
        x = s["x"] + o["posicao"]
        y_eixo = s["y"] - t / 2 if o["parede"] == "sul" else s["y"] + s["comprimento"] + t / 2
        sinal = 1.0 if o["parede"] == "sul" else -1.0
        return [x, y_eixo - sinal * 120.0, s["z"]], [x, y_eixo + sinal * 120.0, s["z"]]
    y = s["y"] + o["posicao"]
    x_eixo = s["x"] - t / 2 if o["parede"] == "oeste" else s["x"] + s["largura"] + t / 2
    sinal = 1.0 if o["parede"] == "oeste" else -1.0
    return [x_eixo - sinal * 120.0, y, s["z"]], [x_eixo + sinal * 120.0, y, s["z"]]


def _varredura(de: list, ate: list) -> dict:
    alto = CAPSULA["meia_altura"] + 3.0  # a cápsula passa 3 cm acima do chão
    return {"tipo": "varredura", "de": [de[0], de[1], de[2] + alto], "ate": [ate[0], ate[1], ate[2] + alto], **CAPSULA}


def medir_sala(p, planta: dict) -> dict:
    """A1, A3, A4 (e a parte de medida de B): tamanho interno, janela, chão e as quatro paredes."""
    s = _sala(planta)
    cx, cy, z = s["x"] + s["largura"] / 2, s["y"] + s["comprimento"] / 2, s["z"]
    alto = z + 135.0
    # os raios do tamanho saem a 50 cm do canto sudoeste, longe dos vãos e acima da mesa
    px, py = s["x"] + 50.0, s["y"] + 50.0
    longe = 3000.0
    consultas = [{"tipo": "raio", "de": [cx, py, alto], "ate": [cx - longe, py, alto]},  # oeste
                 {"tipo": "raio", "de": [cx, py, alto], "ate": [cx + longe, py, alto]},  # leste
                 {"tipo": "raio", "de": [px, cy, alto], "ate": [px, cy - longe, alto]},  # sul
                 {"tipo": "raio", "de": [px, cy, alto], "ate": [px, cy + longe, alto]},  # norte
                 {"tipo": "raio", "de": [cx + 80.0, cy + 80.0, z + 100.0], "ate": [cx + 80.0, cy + 80.0, z - 50.0]}]  # chão
    saida = {}
    oeste, leste, sul, norte, chao = _medir(p, consultas)
    saida["largura"] = R.medida_interna(oeste["distancia"], leste["distancia"], s["largura"])
    saida["comprimento"] = R.medida_interna(sul["distancia"], norte["distancia"], s["comprimento"])
    saida["paredes_barram"] = {"ok": all(m["acertou"] and m["tipo"] == "parede" for m in (oeste, leste, sul, norte)),
                               "acertos": [m.get("id") for m in (oeste, leste, sul, norte)]}
    saida["chao"] = {"ok": chao["acertou"] and chao["tipo"] == "piso" and abs(chao["ponto"][2]) <= 1.0,
                     "id": chao.get("id"), "z": chao["ponto"][2] if chao["acertou"] else None}
    for oid, o in planta["objetos"].items():
        if o["tipo"] != "janela":
            continue
        fora, dentro = _vao_no_mundo(planta, oid)
        meio, baixo = z + o["peitoril"] + o["altura"] / 2, z + o["peitoril"] / 2
        no_meio, abaixo = _medir(p, [{"tipo": "raio", "de": dentro[:2] + [meio], "ate": fora[:2] + [meio]},
                                     {"tipo": "raio", "de": dentro[:2] + [baixo], "ate": fora[:2] + [baixo]}])
        saida[oid] = {"ok": no_meio.get("id") == oid and abaixo.get("tipo") == "parede",
                      "no_meio_acertou": no_meio.get("id"), "abaixo_do_peitoril_acertou": abaixo.get("id")}
    return saida


def medir_porta(p, cena: str, planta: dict, oid: str = "porta1", vao_antigo=None) -> dict:
    """A2: fechada barra, aberta libera, parede cheia barra. A porta é aberta e fechada por fichas de verdade."""
    fora, dentro = _vao_no_mundo(planta, oid)
    s, o = _sala(planta), planta["objetos"][oid]
    # controle: a mesma varredura, deslocada para um trecho de parede cheia (50 cm do canto)
    if o["parede"] in ("sul", "norte"):
        f2, d2 = [s["x"] + 50.0, fora[1], fora[2]], [s["x"] + 50.0, dentro[1], dentro[2]]
    else:
        f2, d2 = [fora[0], s["y"] + 50.0, fora[2]], [dentro[0], s["y"] + 50.0, dentro[2]]
    saida = {"angulo_inicial": o["angulo"]}
    fechada, cheia = _medir(p, [_varredura(fora, dentro), _varredura(f2, d2)])
    saida["fechada"] = {"ok": fechada["acertou"] and fechada.get("id") == oid, "barrada_por": fechada.get("id"), "componente": fechada.get("componente")}
    saida["controle_parede_cheia"] = {"ok": cheia["acertou"] and cheia.get("tipo") == "parede", "barrada_por": cheia.get("id")}
    r = _fazer(p, cena, {"pedido": "abra a porta", "operacoes": [{"operacao": "mudar", "id": oid, "angulo": 90}]})
    aberta = _medir(p, [_varredura(fora, dentro)])[0]
    saida["aberta"] = {"ok": r["ok"] and not aberta["acertou"], "ficha_ok": r["ok"], "barrada_por": aberta.get("id") if aberta["acertou"] else None}
    saida["navegacao_aberta"] = medir_navegacao(p, planta)  # A5: com a porta aberta há caminho de fora até a mesa
    if vao_antigo is not None:
        antigo = _medir(p, [_varredura(*vao_antigo)])[0]
        saida["vao_antigo"] = {"ok": antigo["acertou"] and antigo.get("tipo") == "parede", "barrada_por": antigo.get("id")}
    r = _fazer(p, cena, {"pedido": "feche a porta", "operacoes": [{"operacao": "mudar", "id": oid, "angulo": 0}]})
    de_novo = _medir(p, [_varredura(fora, dentro)])[0]
    saida["fechada_de_novo"] = {"ok": r["ok"] and de_novo.get("id") == oid}
    nav = medir_navegacao(p, planta, quero_caminho=False)["caminho"]  # controle: porta fechada, sem caminho até a mesa
    saida["controle_navegacao_fechada"] = {"ok": not nav["ok"], "existe": nav["existe"], "parcial": nav["parcial"], "esperou_s": nav["esperou_s"]}
    return saida


def _pontos_de_andar(p, planta: dict) -> tuple:
    """De onde o personagem sai (ponto de uso de fora da porta) e aonde vai (ao lado da mesa)."""
    porta = _inv(p)["controlados"]["porta1"]["pontos"]["UsoFora"][:3]
    mesa = planta["objetos"]["mesa1"]
    return porta, [mesa["x"] - mesa["largura"] / 2 - 60.0, mesa["y"], _sala(planta)["z"]]


PRAZO_MALHA_S = 5.0  # a malha de navegação do motor é refeita em segundo plano: a medida espera até isto


def medir_navegacao(p, planta: dict, quero_caminho: bool = True) -> dict:
    """A5: há caminho de fora da porta até o lado da mesa; para fora da área navegável, não há.
    A consulta é repetida até a resposta ser a esperada ou o prazo acabar; o tempo esperado fica anotado."""
    s = _sala(planta)
    de, ate = _pontos_de_andar(p, planta)
    longe = [s["x"] + s["largura"] + D.MARGEM_NAV + 800.0, s["y"] + s["comprimento"] / 2, s["z"]]
    t0 = time.monotonic()
    while True:
        bom, ruim = _medir(p, [{"tipo": "caminho", "de": de, "ate": ate}, {"tipo": "caminho", "de": de, "ate": longe}])
        completo = bool(bom.get("existe")) and not bom.get("parcial")
        if completo == quero_caminho or time.monotonic() - t0 > PRAZO_MALHA_S:
            break
        time.sleep(0.25)
    bom["esperou_s"] = round(time.monotonic() - t0, 2)
    return {"caminho": {"ok": bool(bom.get("existe")) and not bom.get("parcial"), **{k: bom.get(k) for k in ("existe", "parcial", "comprimento", "pontos", "esperou_s")}},
            "controle_fora_da_area": {"ok": not ruim.get("existe") or bool(ruim.get("parcial")), "existe": ruim.get("existe"), "parcial": ruim.get("parcial")},
            "de": de, "ate": ate}


def _esperar_play(p, ligado: bool, prazo: float = 20.0) -> None:
    fim = time.monotonic() + prazo
    while p.chamar("play_state")["em_play"] != ligado:
        if time.monotonic() > fim:
            raise RuntimeError("o Play não mudou de estado no prazo")
        time.sleep(0.2)


def _tempo(p) -> float:
    return p.chamar("play_state")["tempo"]


def _esperar_jogo(p, segundos: float) -> None:
    """Espera `segundos` do relógio do JOGO (não do meu)."""
    t0 = _tempo(p)
    fim = time.monotonic() + segundos * 20 + 10
    while _tempo(p) - t0 < segundos:
        if time.monotonic() > fim:
            raise RuntimeError("o jogo está parado")
        time.sleep(0.1)


def _andar(p, de: list, ate: list, prazo_jogo: float) -> dict:
    ini = p.chamar("sim_walk_start", de=de, ate=ate)
    t0 = _tempo(p)
    st = {}
    while _tempo(p) - t0 < prazo_jogo:
        time.sleep(0.2)
        st = p.chamar("sim_walk_state")
        if st["situacao"].upper() == "IDLE" and st["vel"] < 5.0 and _tempo(p) - t0 > 0.5:
            break
    fim = p.chamar("sim_walk_state", amostras_desde=0)
    return {"resposta": ini["resposta"], "partida": ini["partida"], "segundos_de_jogo": round(_tempo(p) - t0, 2),
            **R.chegou(fim["distancia_chao"], fim["situacao"], fim["vel"]), "loc_final": fim["loc"],
            "amostras": fim["amostras"], "erro": fim["erro"]}


def medir_andar(p, planta: dict) -> dict:
    """A6: com o jogo rodando, o Character do motor entra pela porta aberta; com ela fechada, não chega."""
    de, ate = _pontos_de_andar(p, planta)
    saida = {"de": de, "ate": ate}
    p.chamar("walker_place", em=de)
    p.chamar("play_start", simulate=True, full_speed=True)
    try:
        _esperar_play(p, True)
        _esperar_jogo(p, 0.5)
        p.chamar("sim_door", id="porta1", angulo=0.0)
        _esperar_jogo(p, 1.5)  # a malha de navegação é refeita com o jogo rodando
        fechada = _andar(p, de, ate, 8.0)
        saida["controle_porta_fechada"] = {"ok": not fechada["ok"], **{k: v for k, v in fechada.items() if k != "ok"}}  # tem de NÃO chegar
        p.chamar("sim_door", id="porta1", angulo=90.0)
        _esperar_jogo(p, 1.5)
        saida["porta_aberta"] = _andar(p, de, ate, 20.0)
    finally:
        p.chamar("play_stop")
        _esperar_play(p, False)
        p.chamar("walker_remove")
        # pôr e tirar o personagem de teste deixa o level "por salvar" sem diferença nenhuma: volta ao que está salvo
        saida["level_recarregado"] = p.chamar("reload_level")["por_salvar"] == []
    return saida


# --------------------------------------------------------------------------------------------------------- etapas

def etapa_c1(p, cena: str) -> dict:
    saida = {"pecas": {k: v["estado"] for k, v in p.chamar("pieces_build", pecas=P.PECAS)["pecas"].items()}}
    if PL.carregar(C.CENAS, cena)["revisao"] == 0:
        saida["comando"] = _fazer(p, cena, _ficha(1))
        if not saida["comando"]["ok"]:
            return saida
    else:
        saida["comando_ja_aplicado_antes"] = True  # ensaio: só refaz as medidas
    planta = PL.carregar(C.CENAS, cena)
    inv = _inv(p)
    saida["pecas_na_cena"] = {k: v["tipo"] for k, v in inv["controlados"].items()}
    saida["sala"] = medir_sala(p, planta)
    saida["porta"] = medir_porta(p, cena, planta)
    antes_do_play = _inv(p)["controlados"]
    saida["andar"] = medir_andar(p, planta)
    saida["cena_igual_depois_do_play"] = {"ok": _inv(p)["controlados"] == antes_do_play}
    return saida


CODIGO_MANUAL = '''
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "mesa1":
        p = a.get_actor_location()
        a.set_actor_location(unreal.Vector(p.x + 30.0, p.y, p.z), False, True)
cubo = eas.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(330.0, 330.0, 26.0), unreal.Rotator())
cubo.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
cubo.set_actor_scale3d(unreal.Vector(0.5, 0.5, 0.5))
cubo.set_actor_label("FORA_DO_DIRECTOR")
resultado = "ok"
'''


def etapa_manual(p, cena: str) -> dict:
    """Imita uma pessoa mexendo no editor, por fora do Director: empurra a mesa 30 cm e põe um cubo sem etiqueta."""
    antes = _inv(p)
    p.chamar("dev_exec", codigo=CODIGO_MANUAL)
    depois = _inv(p)
    return {"mesa_antes": antes["controlados"]["mesa1"]["loc"], "mesa_depois": depois["controlados"]["mesa1"]["loc"],
            "cubo": [f for f in depois["fora"] if f["rotulo"] == "FORA_DO_DIRECTOR"], "estado": X.estado(cena, p, C.CENAS)["conciliacao"]}


def etapa_c2(p, cena: str) -> dict:
    planta_antes = PL.carregar(C.CENAS, cena)
    antes = _inv(p)
    vao_antigo = _vao_no_mundo(planta_antes, "porta1")
    saida = {"comando": _fazer(p, cena, _ficha(2))}
    if not saida["comando"]["ok"]:
        return saida
    planta = PL.carregar(C.CENAS, cena)
    depois = _inv(p)
    saida["sala"] = medir_sala(p, planta)
    saida["porta"] = medir_porta(p, cena, planta, vao_antigo=vao_antigo)
    mesmos = {pid: antes["controlados"][pid]["caminho"] == depois["controlados"][pid]["caminho"] for pid in antes["controlados"]}
    saida["mesmos_atores"] = {"ok": all(mesmos.values()), "por_peca": mesmos}
    saida["nada_criado_nem_apagado"] = _ok(sorted(antes["controlados"]) == sorted(depois["controlados"]))
    saida["mesa_no_lugar_manual"] = R.mesmo_lugar(antes["controlados"]["mesa1"]["loc"], depois["controlados"]["mesa1"]["loc"])
    saida["mesa_na_planta"] = [planta["objetos"]["mesa1"]["x"], planta["objetos"]["mesa1"]["y"]]
    cubo_a = [f for f in antes["fora"] if f["rotulo"] == "FORA_DO_DIRECTOR"]
    cubo_d = [f for f in depois["fora"] if f["rotulo"] == "FORA_DO_DIRECTOR"]
    saida["cubo_alheio_igual"] = _ok(bool(cubo_a) and cubo_a == cubo_d)
    saida["resto_da_cena_igual"] = _ok(antes["fora"] == depois["fora"])
    saida["porta_onde"] = {"parede": planta["objetos"]["porta1"]["parede"], "loc": depois["controlados"]["porta1"]["loc"], "rot": depois["controlados"]["porta1"]["rot"]}
    return saida


def etapa_c3(p, cena: str) -> dict:
    antes = _inv(p)
    saida = {"comando": _fazer(p, cena, _ficha(3))}
    if not saida["comando"]["ok"]:
        return saida
    depois = _inv(p)
    saida["criados"] = sorted(set(depois["controlados"]) - set(antes["controlados"]))
    saida["so_prato_e_copo_criados"] = _ok(saida["criados"] == ["copo1", "prato1"])
    saida["os_outros_iguais"] = _ok(all(depois["controlados"][k] == v for k, v in antes["controlados"].items()))
    saida["onde"] = {k: depois["controlados"][k]["loc"] for k in saida["criados"]}
    saida["topo_da_mesa"] = depois["controlados"]["mesa1"]["pontos"].get("AncoraTopo")
    return saida


def etapa_fisica(p, cena: str) -> dict:
    """C: 3 s de física; prato e copo ficam. Controle: o copo levado para fora da borda cai. E, parando o Play sem
    incorporar, tudo volta ao lugar salvo."""
    planta = PL.carregar(C.CENAS, cena)
    mesa = planta["objetos"]["mesa1"]
    antes_editor = _inv(p)["controlados"]
    saida = {}
    p.chamar("play_start", simulate=True, full_speed=True)
    try:
        _esperar_play(p, True)
        t0 = p.chamar("sim_read")
        _esperar_jogo(p, 3.0)
        t3 = p.chamar("sim_read")
        saida["tempo_de_jogo"] = [t0["tempo"], t3["tempo"]]
        for oid in ("prato1", "copo1"):
            saida[oid] = {**R.repouso(antes_editor[oid]["loc"], t3["objetos"][oid]["loc"]), "fisica_ligada": t3["objetos"][oid]["fisica"],
                          "no_editor": antes_editor[oid]["loc"], "depois_de_3s": t3["objetos"][oid]["loc"], "velocidade": t3["objetos"][oid]["vel"]}
        fora_da_borda = [mesa["x"] + mesa["largura"] / 2 + 20.0, mesa["y"], t3["objetos"]["copo1"]["loc"][2] + 2.0]
        p.chamar("sim_move", id="copo1", loc=fora_da_borda)
        _esperar_jogo(p, 2.0)
        caido = p.chamar("sim_read")["objetos"]["copo1"]
        saida["controle_copo_fora_da_borda"] = {**R.caiu(fora_da_borda, caido["loc"]), "solto_em": fora_da_borda, "parou_em": caido["loc"]}
    finally:
        p.chamar("play_stop")
        _esperar_play(p, False)
    depois_editor = _inv(p)["controlados"]
    saida["controle_parar_sem_incorporar"] = {"ok": depois_editor == antes_editor, "copo_no_editor": depois_editor["copo1"]["loc"]}
    return saida


def etapa_incorporar(p, cena: str) -> dict:
    """E: no Play o copo é empurrado; `incorporar` grava no cenário salvo onde ele parou."""
    antes = _inv(p)["controlados"]["copo1"]["loc"]
    p.chamar("play_start", simulate=True, full_speed=True)
    _esperar_play(p, True)
    _esperar_jogo(p, 0.5)
    p.chamar("sim_impulse", id="copo1", velocidade=[0.0, 140.0, 0.0])  # desliza uns 15 cm sobre o tampo
    _esperar_jogo(p, 3.0)
    parou = p.chamar("sim_read")["objetos"]["copo1"]
    res = X.incorporar(cena, p, C.CENAS, C.LAB_DIR, PONTOS, ids={"copo1"})
    depois = _inv(p)["controlados"]["copo1"]
    planta = PL.carregar(C.CENAS, cena)["objetos"]["copo1"]
    andou = R.mesmo_lugar(antes, parou["loc"])["distancia_cm"]
    return {"antes": antes, "parou_no_play": parou, "resultado": res, "no_editor_depois": depois["loc"],
            "andou_cm": andou, "o_copo_saiu_do_lugar": _ok(andou > 5.0),
            "gravado": R.mesmo_lugar(parou["loc"], depois["loc"], R.LIM_INCORPORAR_CM),
            "na_planta": [planta["x"], planta["y"], planta["z"]], "sobre": planta["sobre"], "em_play_depois": p.chamar("info")["em_play"],
            "nada_por_salvar": _ok(p.chamar("info")["por_salvar"] == [])}


def etapa_persistencia(cena: str) -> dict:
    """D: salvar, FECHAR o editor, reabrir; a cena tem de ser a mesma, com colisão e tudo."""
    with ponte.Ponte("demo-persistencia") as p:
        antes = _inv(p)
        por_salvar = p.chamar("info")["por_salvar"]
    saida = {"por_salvar_antes_de_fechar": por_salvar, "fechar": lab.fechar()}
    lab.mapa_inicial(PL.carregar(C.CENAS, cena)["nivel"])
    saida["abrir"] = lab.abrir()
    with ponte.Ponte("demo-persistencia") as p:
        saida["level_ao_abrir"] = p.chamar("info")["level"]
        p.chamar("level_ensure", caminho=PL.carregar(C.CENAS, cena)["nivel"])
        depois = _inv(p)
        est = X.estado(cena, p, C.CENAS)
        planta = PL.carregar(C.CENAS, cena)
        campos = ("classe", "caminho", "tipo", "loc", "rot", "escala", "params", "pontos")
        iguais = {pid: all(antes["controlados"][pid][c] == depois["controlados"].get(pid, {}).get(c) for c in campos)
                  for pid in antes["controlados"]}
        saida["inventario_igual"] = {"ok": all(iguais.values()) and len(antes["controlados"]) == len(depois["controlados"]), "por_peca": iguais}
        saida["n_pecas"] = [len(antes["controlados"]), len(depois["controlados"])]
        saida["resto_da_cena_igual"] = _ok(antes["fora"] == depois["fora"])
        saida["planta_igual_ao_unreal"] = _ok(est["diferencas"] == [] and not any(est["conciliacao"].values()))
        saida["diferencas_planta_x_unreal"] = est["diferencas"]
        saida["conciliacao"] = est["conciliacao"]
        saida["sala"] = medir_sala(p, planta)
        fora, dentro = _vao_no_mundo(planta, "porta1")
        fechada = _medir(p, [_varredura(fora, dentro)])[0]
        saida["porta_fechada_barra"] = {"ok": fechada.get("id") == "porta1"}
        saida["malha_de_navegacao"] = _medir(p, [{"tipo": "nav"}])[0]
    return saida


class PonteQueEstraga:
    """Ponte de verdade que, no `apply`, acrescenta uma ação impossível ao fim do lote: as ações boas já foram
    feitas no Unreal quando a ruim falha. Serve para provar a recuperação ao vivo."""

    def __init__(self, p):
        self.p = p

    def chamar(self, nome: str, **args) -> dict:
        if nome == "apply":
            args["acoes"] = list(args["acoes"]) + [{"acao": "criar", "id": "impossivel", "tipo": "x", "classe": "/Game/Director/Pecas/NaoExiste",
                                                   "loc": [0, 0, 0], "rot": [0, 0, 0]}]
        return self.p.chamar(nome, **args)


def etapa_seguranca(p, cena: str) -> dict:
    """F: ficha inválida não toca na cena; falha no meio é desfeita; o projeto do filme segue vivo e sem chamadas."""
    saida = {}
    antes = _inv(p)
    rev = PL.carregar(C.CENAS, cena)["revisao"]
    r = _fazer(p, cena, {"pedido": "encolha a sala para 2 metros", "operacoes": [{"operacao": "mudar_sala", "largura_m": 2.2}]})
    depois = _inv(p)
    saida["ficha_invalida"] = {"ok": (not r["ok"]) and r["motivo"] == "recusado" and depois == antes and PL.carregar(C.CENAS, cena)["revisao"] == rev,
                               "resposta": r}
    r = X.executar(cena, {"pedido": "gire a mesa e abra a porta (com falha provocada)",
                          "operacoes": [{"operacao": "mudar", "id": "mesa1", "giro": 30}, {"operacao": "mudar", "id": "porta1", "angulo": 45}]},
                   PonteQueEstraga(p), C.CENAS, C.LAB_DIR, PONTOS)
    depois = _inv(p)
    saida["falha_no_meio"] = {"ok": (not r["ok"]) and r.get("cena_igual_a_antes") is True and depois["controlados"] == antes["controlados"]
                              and depois["fora"] == antes["fora"] and PL.carregar(C.CENAS, cena)["revisao"] == rev,
                              "resposta": r, "por_salvar": depois["por_salvar"]}
    planta = PL.carregar(C.CENAS, cena)
    saida["sala_ainda_funciona"] = medir_sala(p, planta)
    return saida


def _ok(v) -> dict:
    return {"ok": bool(v)}


def _resumo(d, prefixo: str = "") -> list:
    """Linhas "caminho: ok/FALHOU" para tudo o que tem `ok` dentro do resultado."""
    linhas = []
    if isinstance(d, dict):
        if "ok" in d and prefixo:
            linhas.append(f"{'ok    ' if d['ok'] else 'FALHOU'}  {prefixo}")
        for k, v in d.items():
            if k != "resposta":  # a resposta de uma recusa esperada tem ok=False de propósito
                linhas += _resumo(v, f"{prefixo}.{k}" if prefixo else k)
    return linhas


ETAPAS = {"c1": etapa_c1, "manual": etapa_manual, "c2": etapa_c2, "c3": etapa_c3, "fisica": etapa_fisica,
          "incorporar": etapa_incorporar, "seguranca": etapa_seguranca}
ORDEM = ("c1", "manual", "c2", "c3", "fisica", "incorporar", "seguranca", "persistencia")


def rodar_etapa(etapa: str, cena: str) -> dict:
    t0 = time.time()
    if etapa == "persistencia":
        dados = etapa_persistencia(cena)
    else:
        with ponte.Ponte(f"demo-{etapa}") as p:
            dados = ETAPAS[etapa](p, cena)
    dados = {"etapa": etapa, "cena": cena, "quando": time.strftime("%Y-%m-%d %H:%M:%S"), "segundos": round(time.time() - t0, 1), **dados}
    _gravar(cena, etapa, dados)
    return dados


def main(argv: list) -> None:
    etapa, cena = argv[0], (argv[1] if len(argv) > 1 else "sala_demo")
    if etapa != "tudo":
        dados = rodar_etapa(etapa, cena)
        sys.stdout.buffer.write(("\n".join(_resumo(dados)) + f"\n({etapa}: {dados['segundos']} s)\n").encode("utf-8"))
        return
    # passada completa, numa cena NOVA, na ordem das etapas
    if PL.carregar(C.CENAS, cena)["revisao"] != 0:
        raise SystemExit(f"a cena {cena!r} já existe: a passada completa é numa cena nova")
    linhas = []
    for nome in ORDEM:
        for linha in _resumo(rodar_etapa(nome, cena)):
            linhas.append(f"{linha[:6]}  {nome}.{linha[8:]}")
    falhas = [x for x in linhas if x.startswith("FALHOU")]
    _gravar(cena, "RESUMO", {"cena": cena, "quando": time.strftime("%Y-%m-%d %H:%M:%S"), "itens": len(linhas),
                             "falhas": len(falhas), "linhas": linhas})
    sys.stdout.buffer.write(("\n".join(linhas) + f"\n{len(linhas) - len(falhas)} de {len(linhas)} itens ok\n").encode("utf-8"))


if __name__ == "__main__":
    main(sys.argv[1:])
