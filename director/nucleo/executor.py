"""Executor: aplica uma ficha numa cena, com registro, ponto de restauração, conferência e recuperação.

O `editor` é qualquer objeto com `chamar(nome, **args) -> dict` (a Ponte de verdade ou um editor de mentira nos
testes). O executor não sabe de agente nem de LLM.

Passos de uma alteração:
 1. linha de INÍCIO no registro da cena (antes de tocar no Unreal);
 2. inventário do Unreal e conciliação (edição manual é adotada; peça apagada à mão faz recusar);
 3. a ficha é conferida e vira a planta nova (recusa aqui não toca em nada);
 4. plano mínimo (só o que mudou);
 5. ponto de restauração: o level é salvo como está e a planta e o arquivo do level são copiados;
 6. aplicar numa transação do editor;
 7. conferir: o inventário tem de bater com a planta nova, e o que não é do Director tem de estar igual;
 8. passou: salva o level, grava a planta, linha de FIM. Falhou: recarrega o level do disco, confere que a cena
    voltou ao que era, linha de FIM com o motivo.
"""
import copy
import os
import shutil
import time

from . import derivar as D
from . import operacoes as OP
from . import pecas as P
from . import plano as PN
from . import planta as PL

PRAZO_NAV_S = 40.0
PRAZO_PLAY_S = 20.0


def _inventario(editor) -> dict:
    return editor.chamar("inventory", variaveis=P.variaveis())


def _esperar_nav(editor, pausa) -> bool:
    """Espera malha disponível, sem construção nem trava nativa, em quatro leituras seguidas.
    IsNavigationBeingBuilt sozinho retorna False durante AsyncLoadLock no UE 5.8.3.
    Prontidão não prova conectividade: isso requer uma consulta de caminho com destinos concretos."""
    pausa(0.5)
    fim = time.monotonic() + PRAZO_NAV_S
    calmas = 0
    while time.monotonic() < fim:
        estado_nav = editor.chamar("measure", consultas=[{"tipo": "nav"}])["medidas"][0]
        calmas = calmas + 1 if estado_nav.get("pronta") is True else 0
        if calmas >= 4:
            return True
        pausa(0.25)
    return False


def _ponto_de_restauracao(raiz_cenas: str, planta: dict, lab_dir: str, pasta_pontos: str) -> str:
    """Copia a planta e o arquivo do level como estão agora. Devolve a pasta (ou "" se não havia o que copiar)."""
    if not pasta_pontos:
        return ""
    destino = os.path.join(pasta_pontos, planta["cena"], time.strftime("%Y%m%d-%H%M%S") + f"-rev{planta['revisao']}")
    copiou = False
    origem_planta = PL.caminho(raiz_cenas, planta["cena"])
    if os.path.exists(origem_planta):
        os.makedirs(destino, exist_ok=True)
        shutil.copy2(origem_planta, os.path.join(destino, "planta.json"))
        copiou = True
    if lab_dir:
        umap = os.path.join(lab_dir, "Content", *planta["nivel"].split("/")[2:]) + ".umap"
        if os.path.exists(umap):
            os.makedirs(destino, exist_ok=True)
            shutil.copy2(umap, os.path.join(destino, os.path.basename(umap)))
            copiou = True
    return destino if copiou else ""


def _recuperar(editor, inv0: dict, motivo: str, **extra) -> dict:
    """Volta o level ao que está salvo no disco e confere que a cena é a de antes."""
    editor.chamar("reload_level")
    inv2 = _inventario(editor)
    igual = inv2["controlados"] == inv0["controlados"] and inv2["fora"] == inv0["fora"]
    return {"ok": False, "motivo": motivo, "recuperado": True, "cena_igual_a_antes": igual, **extra}


def _efetivar(editor, raiz_cenas: str, planta0: dict, planta2: dict, inv0: dict, rel: dict, resumo: list,
              lab_dir: str, pasta_pontos: str, pausa) -> dict:
    alvo = D.derivar(planta2)
    acoes = PN.planejar(alvo, inv0["controlados"])
    if inv0["por_salvar"]:
        s0 = editor.chamar("save")
        if not s0["salvou"] or s0["por_salvar"]:
            return {"ok": False, "motivo": "nao_consegui_salvar_antes", "detalhe": s0, "recuperado": False}
    ponto = _ponto_de_restauracao(raiz_cenas, planta0, lab_dir, pasta_pontos)
    if acoes:
        r = editor.chamar("apply", acoes=acoes)
        if not r["aplicado"]:
            return _recuperar(editor, inv0, "falha_ao_aplicar", erro=r["erro"], ponto_de_restauracao=ponto)
        nav_pronta = _esperar_nav(editor, pausa)
    else:
        nav_pronta = editor.chamar("measure", consultas=[{"tipo": "nav"}])["medidas"][0].get("pronta") is True
    try:
        inv1 = _inventario(editor)
    except Exception as exc:
        return _recuperar(editor, inv0, "erro_ao_conferir", erro=str(exc), ponto_de_restauracao=ponto)
    difs = PN.diferencas(alvo, inv1["controlados"])
    incorporados={a["objeto"]["adotar"] for a in acoes if a.get("objeto",{}).get("adotar")}
    fora_igual = inv1["fora"] == [a for a in inv0["fora"] if a["caminho"] not in incorporados]
    if difs or not fora_igual:
        return _recuperar(editor, inv0, "conferencia_falhou", diferencas=difs[:10], resto_da_cena_igual=fora_igual,
                          ponto_de_restauracao=ponto)
    s = editor.chamar("save")
    if not s["salvou"] or s["por_salvar"]:
        return _recuperar(editor, inv0, "nao_salvou", detalhe=s, ponto_de_restauracao=ponto)
    planta2["revisao"] = planta0["revisao"] + 1
    PL.gravar(raiz_cenas, planta2)
    mesmos = sorted(pid for pid, d in inv1["controlados"].items()
                    if pid in inv0["controlados"] and inv0["controlados"][pid]["caminho"] == d["caminho"])
    return {"ok": True, "revisao": planta2["revisao"], "resumo": resumo,
            "acoes": [[a["acao"], a["id"]] + (sorted(a.get("params", {})) if a["acao"] == "atualizar" else []) for a in acoes],
            "adotados": rel["adotados"], "levados_junto": rel.get("levados_junto", []),
            "estrutura_reposta": rel["estrutura_divergente"], "pecas": len(alvo), "atores_mantidos": mesmos,
            "navegacao_pronta": nav_pronta, "conectividade_verificada": False,
            "ponto_de_restauracao": ponto, "salvou": s["pacotes"]}


def _preparar(editor, raiz_cenas: str, cena: str, removidos: set) -> tuple:
    """Abre a cena, lê o Unreal e concilia. Devolve (planta0, planta1, inv0, rel, recusa ou None)."""
    planta0 = PL.carregar(raiz_cenas, cena)
    if editor.chamar("info")["em_play"]:
        return planta0, None, None, None, "o editor está em Play: pare o Play antes"
    editor.chamar("level_ensure", caminho=planta0["nivel"])
    inv0 = _inventario(editor)
    planta1, rel = PN.conciliar(planta0, inv0["controlados"])
    faltam = [pid for pid in rel["faltando"] if D.dono(planta0, pid) not in removidos]
    if faltam:
        return planta0, planta1, inv0, rel, ("pecas esperadas pela planta nao encontradas no editor: " + ", ".join(faltam)
                                             + ". Confira a planta e o level: pode haver estado desatualizado ou remocao; a causa nao foi determinada")
    if rel["sobrando"]:
        return planta0, planta1, inv0, rel, ("há peças com a etiqueta do Director que a planta não conhece: "
                                             + ", ".join(rel["sobrando"]) + ". Nada foi feito")
    return planta0, planta1, inv0, rel, None


def executar(cena: str, ficha: dict, editor, raiz_cenas: str, lab_dir: str = "", pasta_pontos: str = "", pausa=time.sleep) -> dict:
    """Aplica uma ficha. Devolve sempre um resultado com `ok`; recusa e falha vêm com `motivo`."""
    PL.registrar(raiz_cenas, cena, {"evento": "inicio", "pedido": ficha.get("pedido") if isinstance(ficha, dict) else None,
                                    "operacoes": ficha.get("operacoes") if isinstance(ficha, dict) else None})
    try:
        removidos = {op.get("id") for op in (ficha.get("operacoes") or []) if isinstance(op, dict) and op.get("operacao") == "remover"} \
            if isinstance(ficha, dict) else set()
        planta0, planta1, inv0, rel, recusa = _preparar(editor, raiz_cenas, cena, removidos)
        if recusa:
            res = {"ok": False, "motivo": "recusado", "porque": recusa, "tocou_na_cena": False}
            if rel and (rel["faltando"] or rel["sobrando"]):
                res["diagnostico"] = {"codigo": "planta_editor_divergentes", "planta": PL.caminho(raiz_cenas,cena),
                    "revisao": planta0["revisao"], "nivel": planta0["nivel"],
                    "faltando": rel["faltando"], "sobrando": rel["sobrando"],
                    "proxima_acao": "confira se esta e a planta correspondente ao level; compare uma copia conhecida com o inventario antes de recuperar; nao reconstrua paredes nem contorne a recusa automaticamente"}
        else:
            try:
                planta2, resumo = OP.aplicar_ficha(planta1, ficha)
            except OP.Invalida as e:
                res = {"ok": False, "motivo": "recusado", "porque": str(e), "tocou_na_cena": False}
            else:
                res = _efetivar(editor, raiz_cenas, planta0, planta2, inv0, rel, resumo, lab_dir, pasta_pontos, pausa)
                if res.get("ok"):
                    from director import relatorio
                    alterados = [i for i, o in planta2["objetos"].items() if o != planta0["objetos"].get(i)]
                    res["resultado"] = relatorio.medir(planta2, editor, alterados, solicitado=entrada_publica(ficha))
    except Exception as e:  # noqa: BLE001
        PL.registrar(raiz_cenas, cena, {"evento": "fim", "ok": False, "motivo": "erro", "erro": f"{type(e).__name__}: {e}"[:500]})
        raise
    PL.registrar(raiz_cenas, cena, {"evento": "fim", **{k: v for k, v in res.items() if k != "atores_mantidos"}})
    return res


def entrada_publica(ficha):
    return {"pedido": ficha.get("pedido"), "operacoes": ficha.get("operacoes", [])}


def incorporar(cena: str, editor, raiz_cenas: str, lab_dir: str = "", pasta_pontos: str = "", ids=None, pausa=time.sleep) -> dict:
    """Com o Play rodando: lê onde cada objeto ficou, para o Play e grava esse estado no cenário salvo.
    Sem isto, o que muda no Play se perde quando o Play para (é assim que o Unreal funciona)."""
    PL.registrar(raiz_cenas, cena, {"evento": "inicio", "pedido": "incorporar", "ids": sorted(ids) if ids else None})
    try:
        planta0 = PL.carregar(raiz_cenas, cena)
        lido = editor.chamar("sim_read")["objetos"]
        editor.chamar("play_stop")
        fim = time.monotonic() + PRAZO_PLAY_S
        while editor.chamar("info")["em_play"]:
            if time.monotonic() > fim:
                raise RuntimeError("o Play não parou no prazo")
            pausa(0.3)
        inv0 = _inventario(editor)
        planta1, rel = PN.conciliar(planta0, inv0["controlados"])
        planta2 = copy.deepcopy(planta1)
        resumo = []
        for oid, o in planta2["objetos"].items():
            s = lido.get(oid)
            if s is None or (ids and oid not in ids):
                continue
            if o["tipo"] in OP.OBJETOS:
                novo = {"x": s["loc"][0], "y": s["loc"][1], "z": s["loc"][2], "rot": list(s["rot"])}
                if any(abs(novo[k] - o[k]) > PN.TOL_CM for k in ("x", "y", "z")) or PN._rot_difere(novo["rot"], o["rot"]):
                    o.update(novo)
                    resumo.append(f"{oid} incorporado em {[round(v, 1) for v in s['loc']]}")
                    mesa = planta2["objetos"].get(o.get("sobre") or "")
                    if mesa is not None:
                        topo = planta2["objetos"][mesa["sala"]]["z"] + mesa["altura"]
                        if not OP._na_mesa(mesa, o["x"], o["y"], 0.0) or abs(o["z"] - o["altura"] / 2 - topo) > 2.0:
                            resumo.append(f"{oid} não está mais sobre {o['sobre']}")
                            o["sobre"] = None
            elif o["tipo"] == "asset":
                import math
                m=o['modelo'];es=[o[k]/m['tamanho'][j] for j,k in enumerate(('largura','profundidade','altura'))]
                g=math.radians(s['rot'][1]);cx=m['centro'][0]*es[0];cy=m['centro'][1]*es[1]
                o.update(x=s['loc'][0]+cx*math.cos(g)-cy*math.sin(g),y=s['loc'][1]+cx*math.sin(g)+cy*math.cos(g),
                         z=s['loc'][2]+m['min_z']*es[2],giro=s['rot'][1])
                resumo.append(oid+' incorporado do Play (posicao e giro vertical)')
            elif o["tipo"] == "porta" and "angulo" in s and abs(s["angulo"] - o["angulo"]) > PN.TOL_GRAUS:
                o["angulo"] = s["angulo"]
                resumo.append(f"{oid} incorporada com {s['angulo']:g} graus")
        OP.conferir(planta2)
        res = _efetivar(editor, raiz_cenas, planta0, planta2, inv0, rel, resumo, lab_dir, pasta_pontos, pausa)
        res["lido_no_play"] = {k: v for k, v in lido.items() if not ids or k in ids}
    except Exception as e:  # noqa: BLE001
        PL.registrar(raiz_cenas, cena, {"evento": "fim", "ok": False, "motivo": "erro", "erro": f"{type(e).__name__}: {e}"[:500]})
        raise
    PL.registrar(raiz_cenas, cena, {"evento": "fim", **{k: v for k, v in res.items() if k not in ("atores_mantidos", "lido_no_play")}})
    return res


def estado(cena: str, editor, raiz_cenas: str) -> dict:
    """Só leitura: a planta, o que alguém mudou à mão e o que difere entre a planta e o Unreal."""
    planta0 = PL.carregar(raiz_cenas, cena)
    if editor.chamar("info")["level"] != planta0["nivel"]:
        return {"cena": cena, "planta": PL.caminho(raiz_cenas,cena), "nivel": planta0["nivel"], "revisao": planta0["revisao"], "level_aberto": False, "objetos": sorted(planta0["objetos"])}
    inv = _inventario(editor)
    _, rel = PN.conciliar(planta0, inv["controlados"])
    return {"cena": cena, "planta": PL.caminho(raiz_cenas,cena), "nivel": planta0["nivel"], "revisao": planta0["revisao"], "level_aberto": True, "objetos": sorted(planta0["objetos"]),
            "pecas_no_unreal": len(inv["controlados"]), "outros_atores": len(inv["fora"]),
            "diferencas": PN.diferencas(D.derivar(planta0), inv["controlados"]), "conciliacao": rel,
            "por_salvar": inv["por_salvar"]}
