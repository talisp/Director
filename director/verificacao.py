"""Verificacao por escopo com evidencias e limites explicitos."""
import math
import time
from . import config as C, consultas, relatorio
from .nucleo import planta as PL
from .ensaios import diferencas
from .nucleo import pecas as P


def testar_play(editor, rotas, nomes, segundos=3, prazo=15):
    """Reutiliza macros. Sempre para o Play e remove apenas o boneco que criou."""
    if editor.chamar("info")["em_play"]:
        raise ValueError("Play ja ativo; o teste nao interrompe uma simulacao existente")
    posto = iniciou = False
    resultado={"rotas":[],"fisica":[]}
    try:
        if rotas:
            editor.chamar("walker_place", em=rotas[0]["de"])
            posto=True
        resultado["inicio"]=editor.chamar("play_start",simulate=True,full_speed=True)
        iniciou=True
        fim=time.monotonic()+prazo
        while not editor.chamar("play_state")["em_play"]:
            if time.monotonic()>fim: raise TimeoutError("Play nao iniciou")
            time.sleep(.2)
        antes={a["rotulo"]:a for a in editor.chamar("scene_geometry",mundo="jogo")["atores"] if a["rotulo"] in nomes}
        time.sleep(segundos)
        depois={a["rotulo"]:a for a in editor.chamar("scene_geometry",mundo="jogo")["atores"] if a["rotulo"] in nomes}
        for nome,a in antes.items():
            b=depois.get(nome)
            if not b:
                resultado["fisica"].append({"ator":nome,"estavel":False,"motivo":"ator ausente"});continue
            dist=math.dist(a["loc"],b["loc"])
            ang=max(abs((x-y+180)%360-180) for x,y in zip(a["rot"],b["rot"]))
            vel=max(math.dist(c["velocidade"],[0,0,0]) for c in b["componentes_fisicos"])
            angular=max(math.dist(c["velocidade_angular"],[0,0,0]) for c in b["componentes_fisicos"])
            resultado["fisica"].append({"ator":nome,"deslocamento_cm":round(dist,3),"giro_graus":round(ang,3),
                "velocidade":round(vel,3),"velocidade_angular":round(angular,3),"fisica":any(c["fisica"] for c in b["componentes_fisicos"]),
                "estavel":dist<=3 and ang<=2 and vel<1 and angular<1})
        for rota in rotas:
            tolerancia=rota.get("tolerancia_cm",10)
            inicio=editor.chamar("sim_walk_start",de=rota["de"],ate=rota["ate"],raio_chegada=min(tolerancia,8))
            fim=time.monotonic()+prazo
            while True:
                time.sleep(.25)
                estado=editor.chamar("sim_walk_state")
                if estado["situacao"].upper()=="IDLE" or time.monotonic()>fim: break
            resultado["rotas"].append({"nome":rota.get("nome"),"inicio":inicio,"final":estado,
                "chegou":estado["distancia_chao"]<=tolerancia and estado["situacao"].upper()=="IDLE" and estado["vel"]<5})
    finally:
        if iniciou:
            resultado["fim"]=editor.chamar("play_stop")
            fim=time.monotonic()+prazo
            while editor.chamar("play_state")["em_play"]:
                if time.monotonic()>fim: raise TimeoutError("Play nao parou; boneco nao removido durante Play")
                time.sleep(.2)
        if posto: resultado["boneco_removido"]=editor.chamar("walker_remove")
    return resultado


def contencao(ator, sala):
    limites = [sala["x"], sala["y"], sala["x"]+sala["largura"], sala["y"]+sala["comprimento"]]
    excessos = {"oeste": max(0, limites[0]-ator["min"][0]), "leste": max(0, ator["max"][0]-limites[2]),
                "sul": max(0, limites[1]-ator["min"][1]), "norte": max(0, ator["max"][1]-limites[3])}
    return {"envelope_dentro": max(excessos.values()) <= 0.1,
            "excesso_interno_cm": {k: round(v, 3) for k,v in excessos.items()},
            "excesso_exterior_cm": {k: round(max(0,v-sala["parede"]), 3) for k,v in excessos.items()}}


def _area(a, s):
    return max(0,min(a["max"][0],s["x"]+s["largura"])-max(a["min"][0],s["x"])) * max(0,min(a["max"][1],s["y"]+s["comprimento"])-max(a["min"][1],s["y"]))


def _raios_externos(a, s, excessos):
    centro = [(x+y)/2 for x,y in zip(a["min"],a["max"])]
    qs=[]
    for lado, dist in excessos.items():
        if dist <= .1:
            continue
        eixo = 0 if lado in ("oeste", "leste") else 1
        sinal = -1 if lado in ("oeste", "sul") else 1
        de=list(centro); ate=list(centro)
        de[eixo]=(a["min"][eixo]-20) if sinal<0 else (a["max"][eixo]+20)
        qs.append({"tipo":"raio","de":de,"ate":ate})
    return qs


def verificar(cena, pedido, editor, raiz=None):
    raiz=raiz or C.CENAS
    if not isinstance(pedido,dict): raise ValueError("verificar recebe um objeto JSON")
    p=PL.carregar(raiz,cena)
    if editor.chamar("info")["level"] != p["nivel"]:
        raise ValueError("a cena precisa estar aberta; verificar nao troca level")
    salas={i:s for i,s in p["objetos"].items() if s["tipo"]=="sala"}
    if pedido.get("salas"):
        salas={i:salas[i] for i in pedido["salas"]}
    mapa=pedido.get("associacoes",{})
    geo=editor.chamar("scene_geometry",colisoes=True)["atores"]
    rows=[]; problemas=[]
    for a in geo:
        oid=a["id"]; o=p["objetos"].get(oid,{})
        # Atores externos permanecem listados mesmo quando nao sao moveis candidatos.
        if oid and o.get("tipo") in ("sala","porta","janela") or a.get("tipo") in ("piso","parede","nav"):
            continue
        if not o and not any(c["fisica"] or c["movel"] for c in a["componentes_fisicos"]):
            continue
        sid=mapa.get(a["rotulo"]) or mapa.get(a["caminho"]) or o.get("sala")
        inferida=False
        if sid is None and salas:
            sid=max(salas,key=lambda i:_area(a,salas[i])); inferida=True
            if _area(a,salas[sid])==0: sid=None
        if sid not in salas:
            continue
        s=salas[sid]
        # O piso do level e uma superficie de apoio, nao um movel daquele comodo.
        if (a["min"][0] <= s["x"] and a["max"][0] >= s["x"]+s["largura"]
            and a["min"][1] <= s["y"] and a["max"][1] >= s["y"]+s["comprimento"]
            and a["max"][2] <= s["z"]+.1):
            continue
        check=contencao(a,s)
        check.update({"ator":a["rotulo"],"id":oid,"sala":sid,"associacao_inferida":inferida,
                      "min":a["min"],"max":a["max"],"componentes_fisicos":a["componentes_fisicos"]})
        qs=_raios_externos(a,s,check["excesso_exterior_cm"])
        hits=editor.chamar("measure",consultas=qs)["medidas"] if qs else []
        check["raios_externos"]=hits
        check["fora_confirmado_por_raio"]=any(h.get("acertou") and h.get("rotulo")==a["rotulo"] for h in hits)
        centro=[(a["min"][j]+a["max"][j])/2 for j in range(3)]
        apoio=editor.chamar("measure",consultas=[{"tipo":"raio","de":[centro[0],centro[1],a["min"][2]-.2],
                    "ate":[centro[0],centro[1],a["min"][2]-50]}])["medidas"][0]
        check["apoio"]=apoio
        check["apoio_proximo"]=bool(apoio.get("acertou")) and apoio.get("distancia",999)<=3
        if not check["apoio_proximo"]: problemas.append({"ator":a["rotulo"],"tipo":"apoio_nao_confirmado"})
        sobreposicoes=[]
        nativas={path for c in a["componentes_fisicos"] for path in c.get("sobreposicoes_nativas",[])}
        for b in geo:
            if b["caminho"] in nativas and all(min(a["max"][j],b["max"][j])-max(a["min"][j],b["min"][j])>.5 for j in range(3)):
                sobreposicoes.append(b["rotulo"])
        check["sobreposicoes_colisao"]=sobreposicoes
        if sobreposicoes: problemas.append({"ator":a["rotulo"],"tipo":"sobreposicao_colisao", "com":sobreposicoes})
        if not check["envelope_dentro"]:
            problemas.append({"ator":a["rotulo"],"tipo":"fora_do_comodo", "confirmado_por_raio":check["fora_confirmado_por_raio"]})
        rows.append(check)
    pares=[]
    for i,a in enumerate(rows):
        for b in rows[i+1:]:
            if a["sala"]==b["sala"] and all(min(a["max"][j],b["max"][j])-max(a["min"][j],b["min"][j])>.1 for j in range(3)):
                pares.append([a["ator"],b["ator"]])
    circulacao=[]
    for rota in pedido.get("rotas",[]):
        de,ate=rota["de"],rota["ate"]
        raio=rota.get("raio",34); meia=rota.get("meia_altura",88)
        qs=[{"tipo":"varredura","de":[de[0],de[1],de[2]+meia+2],"ate":[ate[0],ate[1],ate[2]+meia+2],"raio":raio,"meia_altura":meia},
            {"tipo":"caminho","de":de,"ate":ate}]
        r=consultas.medir(cena,{"consultas":qs},editor,raiz)
        path=r["medidas"][1]
        pts=path.get("pontos",[])
        passagem=r['medidas'][0]
        linha_direta=passagem
        if path.get('completo') and len(pts)>1:
            segmentos=[{'tipo':'varredura','de':[a[0],a[1],a[2]+meia+2],
                'ate':[b[0],b[1],b[2]+meia+2],'raio':raio,'meia_altura':meia}
                for a,b in zip(pts,pts[1:])]
            medidas=consultas.medir(cena,{'consultas':segmentos},editor,raiz)['medidas']
            passagem={'livre':all(m.get('livre') for m in medidas),'segmentos':medidas,'metodo':'capsula ao longo do caminho nativo'}
        chegou_ao_destino=bool(pts) and math.dist(pts[-1][:2],ate[:2])<=rota.get("tolerancia_cm",10)
        circulacao.append({"nome":rota.get("nome"),"passagem":passagem,"linha_direta":linha_direta,"caminho":path,
            "destino_na_malha":chegou_ao_destino,"personagem":"nao_executado"})
    rotas_ok=all(r["passagem"].get("livre") and r["caminho"].get("completo") and r["destino_na_malha"] for r in circulacao)
    resposta={"ok":True,"aprovado":not problemas and not pares and bool(rows) and rotas_ok,
            "escopo_verificado":["contencao de envelopes fisicos", "raios externos onde ha excesso exterior", "rotas solicitadas sem Play"], "cena":cena,"objetos":rows,
            "problemas":problemas,"possiveis_penetracoes_envelopes":pares,"circulacao":circulacao,
            "fora_da_planta":[{"ator":a["rotulo"],"caminho":a["caminho"]} for a in geo if not a["id"]],
            "nao_verificado":["envelopes sobrepostos nao comprovam intersecao de malhas", "apoio/estabilidade exigem amostras em Play", "foto nao solicitada", "sem baseline nao ha comparacao antes/depois"],
            "relatorio":relatorio.medir(p,editor,list(salas))}
    erros_colisao=[{"ator":r["ator"],"erro":c["sobreposicoes_erro"]} for r in rows for c in r["componentes_fisicos"] if c.get("sobreposicoes_erro")]
    if erros_colisao:
        resposta["nao_verificado"].append({"sobreposicoes_nativas":erros_colisao})
        resposta["aprovado"]=False
    if pedido.get("simular"):
        teste=testar_play(editor,pedido.get("rotas",[]),[r["ator"] for r in rows],segundos=pedido.get("segundos",3))
        resposta["play"]=teste
        for rota,teste_rota in zip(resposta['circulacao'],teste['rotas']):
            rota['personagem']={'executado':True,'chegou':teste_rota['chegou'],'distancia_cm':teste_rota['final']['distancia_chao']}
        resposta["aprovado"] &= all(r["chegou"] for r in teste["rotas"]) and all(r["estavel"] and r["fisica"] for r in teste["fisica"])
        resposta["nao_verificado"][1]="estabilidade medida em Play; apoio ainda requer raio de piso"
    if pedido.get("baseline"):
        import json
        with open(pedido["baseline"],encoding="utf-8-sig") as f: baseline=json.load(f)
        resposta["antes_depois"]=diferencas(baseline,editor.chamar("inventory",variaveis=P.variaveis()))
    if pedido.get("foto"):
        if len(salas)!=1: raise ValueError("foto requer exatamente um comodo")
        from .captura import fotografar
        resposta["foto"]=fotografar(editor,next(iter(salas.values())),pedido["foto"])
    return resposta
