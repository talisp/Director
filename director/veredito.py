"""Veredito em uma linha no topo da resposta: APROVADO/REPROVADO, motivo e proxima acao.

Nasceu do teste de 17/10: o operador leu `ok: true` e disse que o boneco chegou, com
`aprovado: false` enterrado no JSON. O veredito so resume o que a resposta ja mediu;
nao mede nada novo e nao muda `ok` nem `aprovado`.
"""


def _rotas(res):
    falhas = []
    for r in res.get("circulacao", []):
        nome = r.get("nome") or "rota"
        p = r.get("personagem")
        if isinstance(p, dict) and p.get("executado") and not p.get("chegou"):
            falhas.append(f"{nome}: o boneco nao chegou (ficou a {p.get('distancia_cm', '?')} cm do destino)")
            continue
        caminho = r.get("caminho") or {}
        if not caminho.get("existe", True) or caminho.get("parcial"):
            falhas.append(f"{nome}: caminho da navegacao parcial ou inexistente")
        elif not r.get("destino_na_malha", True):
            falhas.append(f"{nome}: o destino fica fora da malha de navegacao")
        elif not (r.get("passagem") or {}).get("livre", True):
            seg = [s for s in (r["passagem"].get("segmentos") or [r["passagem"]]) if s.get("acertou")]
            quem = (seg[0].get("rotulo") or seg[0].get("id")) if seg else "obstaculo"
            tipo = seg[0].get("tipo") if seg else None
            falhas.append(f"{nome}: a capsula do boneco bate em {quem}" + (" (porta)" if tipo == "porta" else ""))
    return falhas


def de_verificacao(res):
    if res.get("aprovado"):
        return {"veredito": "APROVADO", "motivo": "tudo o que foi pedido passou nas medidas desta verificacao",
                "proxima_acao": "relatar citando o escopo_verificado e o nao_verificado"}
    motivos = []
    for p in res.get("problemas", []):
        motivos.append(f"{p.get('ator')}: {p.get('tipo')}" + (f" com {', '.join(p['com'])}" if p.get("com") else ""))
    motivos += [f"envelopes sobrepostos: {a} e {b}" for a, b in res.get("possiveis_penetracoes_envelopes", [])]
    motivos += _rotas(res)
    for f in (res.get("play") or {}).get("fisica", []):
        if not f.get("fisica") and f.get("exige_fisica", True):
            motivos.append(f"{f.get('ator')}: sem fisica ligada no Play")
        elif not f.get("estavel"):
            motivos.append(f"{f.get('ator')}: nao ficou parado no Play (andou {f.get('deslocamento_cm')} cm)")
    if not res.get("objetos"):
        motivos.append("nenhum objeto dos comodos pedidos foi encontrado para verificar")
    if not motivos:
        motivos.append("reprovado por erro na consulta de colisao; veja nao_verificado")
    acao = "corrigir a causa citada e rodar verificar de novo; NAO relatar como aprovado"
    if any(m.endswith("(porta)") for m in motivos):
        acao = "uma porta fechada esta no caminho: abra a porta (mudar angulo) ou mude a rota; depois verificar de novo"
    return {"veredito": "REPROVADO", "motivo": "; ".join(motivos[:6]) + (f" (+{len(motivos) - 6})" if len(motivos) > 6 else ""),
            "proxima_acao": acao}


def de_planejamento(res):
    if res.get("ok"):
        v = res.get("verificacao2d") or {}
        dims = res.get("dimensoes_cm")
        return {"veredito": "APROVADO", "motivo": f"proposta de {dims[0]} x {dims[1]} cm aprovada pelo solver e pelo filtro 2D ({v.get('criterio', 'circulacao')})",
                "proxima_acao": "aplicar com objeto/fazer e provar com verificar (simular e rotas); a proposta ainda nao foi testada no Unreal"}
    motivo = res.get("motivo")
    detalhe = res.get("detalhe") or res.get("porque") or motivo or "falha sem detalhe"
    acoes = {
        "filtro2d_reprovou": "aumente o tamanho maximo, tire ou diminua o objeto citado, ou aumente segundos/tentativas; nao mude a cena para testar tamanhos (use sala + minimo_cm/maximo_cm)",
        "impossivel_no_modelo": "nao cabe: aumente o tamanho maximo ou tire um objeto; os que nao cabem nem sozinhos estao em nao_cabem_sozinhos",
        "sem_prova_no_prazo": "aumente segundos; nada foi provado",
        "modelo_invalido": "confira medidas e campos do pedido",
        "medidas internas nao confirmadas": "abra a cena no editor e rode de novo, ou teste um tamanho hipotetico com minimo_cm/maximo_cm",
    }
    return {"veredito": "REPROVADO", "motivo": detalhe,
            "proxima_acao": acoes.get(motivo, "leia o motivo antes de tentar de novo; nao repita o mesmo pedido")}


def com_veredito(modo, res):
    """Devolve a resposta com veredito, motivo e proxima_acao como primeiras chaves."""
    if not isinstance(res, dict):
        return res
    if res.get("motivo") == "erro":
        v = {"veredito": "ERRO", "motivo": res.get("porque", "erro sem detalhe"),
             "proxima_acao": "nada foi provado; leia o erro, confira o estado da cena antes de repetir"}
    else:
        v = de_verificacao(res) if modo == "verificar" else de_planejamento(res)
    saida = dict(v)
    if res.get("motivo") is not None:
        saida["codigo"] = res["motivo"]
    saida.update({k: x for k, x in res.items() if k not in v})
    return saida
