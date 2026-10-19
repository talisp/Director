"""Objetos com identidade na planta, reutilizando o executor transacional."""
import json
import math
from . import config as C
from .nucleo import planta as PL,executor,operacoes

MASSAS={'cama':45,'criado_mudo':12,'guarda_roupa':80,'escrivaninha':25,'cadeira':8,'mesa':25,'generico':20,
        'travesseiro':.6,'notebook':2.2,'computador':8,'livro':1,'abajur':2,'objeto_pequeno':1}
# Pecas da construcao: ficam paradas, sem simular fisica (box nao e um movel que cai).
FIXOS=('box','box_chuveiro','chuveiro','vaso_sanitario','pia','bancada','divisoria','parede','bancada_pia')


def _altura_de_apoio(editor,b,sobre,o,folga=2.0,irregular=3.0,esperado_z=None):
    """Altura real da superficie sob o objeto: raios para baixo no centro e nos quatro cantos.
    O topo da caixa do movel engana (a cabeceira da cama e mais alta que o colchao: visto em 17/10)."""
    g=math.radians(o['giro']);hw,hd=max(o['largura']/2-folga,0),max(o['profundidade']/2-folga,0)
    pts=[(0,0)]+[(sx*hw,sy*hd) for sx in (-1,1) for sy in (-1,1)]
    inicio=b.get('z',0)+b['altura']+50 if esperado_z is None else esperado_z+max(o.get('altura',0)+2,5)
    qs=[{'tipo':'raio','de':[o['x']+px*math.cos(g)-py*math.sin(g),o['y']+px*math.sin(g)+py*math.cos(g),inicio],
         'ate':[o['x']+px*math.cos(g)-py*math.sin(g),o['y']+px*math.sin(g)+py*math.cos(g),b.get('z',0)]} for px,py in pts]
    med=editor.chamar('measure',consultas=qs)['medidas']
    zs=[]
    for nome,m in zip(('centro','canto sudoeste','canto noroeste','canto sudeste','canto nordeste'),med):
        if not m.get('acertou') or m.get('id')!=sobre:
            raise ValueError(f"sobre {sobre}: o {nome} do objeto nao fica em cima de {sobre} (o raio bateu em {m.get('rotulo') or 'nada'}); mova ou diminua o objeto")
        zs.append(m['ponto'][2])
    if max(zs)-min(zs)>irregular:
        raise ValueError(f'sobre {sobre}: a superficie embaixo do objeto e irregular ({min(zs):.1f} a {max(zs):.1f} cm); '
                         f'mova o objeto para uma parte plana (ex.: longe da cabeceira ou da borda)')
    if esperado_z is not None and abs(max(zs)-esperado_z)>3:raise ValueError('altura de apoio solicitada nao corresponde a superficie medida')
    return max(zs)


def medir_ancora(editor,o,s):
    """Cinco raios na pequena folga entre objeto e suporte; nunca usa bounds como contato."""
    a=o['ancora'];qs=[]
    if a['tipo']=='teto':
        for dx,dy in [(0,0)]+[(x*o['largura']*.45,y*o['profundidade']*.45) for x in (-1,1) for y in (-1,1)]:
            de=[o['x']+dx,o['y']+dy,o['z']+o['altura']+.25];qs.append({'tipo':'raio','de':de,'ate':[de[0],de[1],de[2]+20]})
    else:
        lado=a['lado'];normal={'sul':(0,1),'norte':(0,-1),'oeste':(1,0),'leste':(-1,0)}[lado]
        tx,ty=normal[1],-normal[0]
        for t,z in [(0,.5)]+[(v*.45,w) for v in (-1,1) for w in (.05,.95)]:
            x=o['x']+tx*t*o['largura']-normal[0]*(o['profundidade']/2+.25)
            y=o['y']+ty*t*o['largura']-normal[1]*(o['profundidade']/2+.25)
            qs.append({'tipo':'raio','de':[x,y,o['z']+z*o['altura']],
                'ate':[x-normal[0]*20,y-normal[1]*20,o['z']+z*o['altura']]})
    med=editor.chamar('measure',consultas=qs)['medidas']
    def valido(m):
        return m.get('acertou') and m.get('distancia',999)<=3 and (
            m.get('id')==o['sala']+'.teto' if a['tipo']=='teto' else m.get('tipo')=='parede')
    return {'confirmada':len(med)==5 and all(valido(m) for m in med),'raios':med,'tipo':a['tipo']}


def apoios(cena,pedido,editor):
    """Candidatos por colisao nativa para uma pegada solicitada; nao extrai toda a malha."""
    p=PL.carregar(C.CENAS,cena)
    if editor.chamar('info')['level']!=p['nivel']:raise ValueError('abra a cena antes de consultar apoios')
    oid=pedido['objeto'];b=p['objetos'][oid]
    if b['tipo'] not in operacoes.MOVEIS:raise ValueError('apoio requer movel registrado')
    w,h=pedido['largura_m']*100,pedido['profundidade_m']*100
    if min(w,h)<=0 or not all(math.isfinite(v) for v in (w,h)):raise ValueError('pegada positiva e finita')
    if pedido.get('niveis'):return _apoios_em_niveis(p,b,oid,w,h,pedido,editor)
    candidatos=[];recusados=0
    for dx in (-.3,0,.3):
        for dy in (-.3,0,.3):
            g=math.radians(b['giro']);lx=dx*max(0,b['largura']-w);ly=dy*max(0,b['profundidade']-h)
            o={'x':b['x']+lx*math.cos(g)-ly*math.sin(g),'y':b['y']+lx*math.sin(g)+ly*math.cos(g),
               'giro':b['giro'],'largura':w,'profundidade':h}
            try:z=_altura_de_apoio(editor,b,oid,o)
            except ValueError:recusados+=1;continue
            candidatos.append({'centro_cm':[o['x'],o['y']],'base_z_cm':z,'giro':b['giro']})
    return {'ok':True,'objeto':oid,'pegada_cm':[w,h],'candidatos':candidatos,'recusados':recusados,
        'limite':'amostra 3x3 por colisao visivel de cima; nao enumera prateleiras ocultas, nao comprova estabilidade em Play'}


def _apoios_em_niveis(planta,b,oid,w,h,pedido,editor):
    """Busca pegadas em prateleiras via raios a varias alturas; nao extrai triangulos."""
    altura=pedido.get('altura_m',.05)*100
    if not isinstance(altura,(int,float)) or not math.isfinite(altura) or altura<=0:raise ValueError('altura_m positiva e finita')
    base=b.get('z',planta['objetos'][b['sala']]['z']);passo=max(5,b['altura']/30)
    niveis=[base+b['altura']+altura+5]+[base+b['altura']-n*passo for n in range(1,31) if b['altura']-n*passo>0]
    g=math.radians(b['giro']);c,si=math.cos(g),math.sin(g);amostras=[];qs=[]
    for dx in (-.3,0,.3):
        for dy in (-.3,0,.3):
            lx=dx*max(0,b['largura']-w);ly=dy*max(0,b['profundidade']-h)
            x,y=b['x']+lx*c-ly*si,b['y']+lx*si+ly*c
            pontos=[(x,y)]+[(x+px*c-py*si,y+px*si+py*c) for px in (-w/2+min(2,w/4),w/2-min(2,w/4)) for py in (-h/2+min(2,h/4),h/2-min(2,h/4))]
            for z in niveis:
                amostras.append((x,y,z,pontos))
                qs.extend({'tipo':'raio','de':[px,py,z],'ate':[px,py,base-.1]} for px,py in pontos)
    medidas=editor.chamar('measure',consultas=qs)['medidas'];encontrados={}
    for n,(x,y,z,pontos) in enumerate(amostras):
        hits=medidas[n*5:n*5+5]
        if len(hits)!=5 or not all(m.get('acertou') and m.get('id')==oid and m.get('distancia',0)>.1 and (m.get('normal') or [0,0,0])[2]>.95 for m in hits):continue
        zs=[m['ponto'][2] for m in hits];topo=max(zs)
        if max(zs)-min(zs)>3 or z-topo<altura+1:continue
        key=(round(x,2),round(y,2),round(topo,1))
        encontrados[key]=(pontos,{'centro_cm':[x,y],'base_z_cm':topo,
            'apoio_z_m':(topo-planta['objetos'][b['sala']]['z'])/100,'giro':b['giro']})
    lista=list(encontrados.values());up=[]
    for pontos,r in lista:
        up.extend({'tipo':'raio','de':[x,y,r['base_z_cm']+.1],'ate':[x,y,r['base_z_cm']+altura+1]} for x,y in pontos)
    livres=editor.chamar('measure',consultas=up)['medidas'] if up else []
    candidatos=[r for n,(_,r) in enumerate(lista) if all(not m.get('acertou') for m in livres[n*5:n*5+5])]
    candidatos.sort(key=lambda r:(r['base_z_cm'],r['centro_cm']))
    representantes=[];vistos=set()
    for r in candidatos:
        z=round(r['base_z_cm'],1)
        if z not in vistos:representantes.append(r);vistos.add(z)
    curtos=(representantes+[r for r in candidatos if r not in representantes])[:12]
    return {'ok':True,'objeto':oid,'pegada_cm':[w,h],'altura_cm':altura,'candidatos':curtos,
        'candidatos_totais':len(candidatos),'limitado':len(curtos)<len(candidatos),
        'alturas_cm':sorted({round(r['base_z_cm'],1) for r in candidatos}),'raios':len(qs)+len(up),
        'limite':'amostragem 3x3 e ate 31 alturas por colisao simples; exige normal superior e folga acima. Pode omitir nichos estreitos/entre amostras; nao certifica toda malha nem estabilidade'}


def fazer(cena,pedido,editor):
    p=PL.carregar(C.CENAS,cena)
    if editor.chamar('info')['level']!=p['nivel']: raise ValueError('abra a cena antes de criar/adotar objeto')
    sid=pedido['sala'];s=p['objetos'][sid]
    acao=pedido.get('acao','colocar')
    if acao not in ('colocar','compor','adotar','duplicar'): raise ValueError('acao: colocar, compor, adotar ou duplicar')
    modelo=editor.chamar('object_model',asset=pedido.get('asset',''),ator=pedido.get('ator',''),partes=pedido.get('partes'))
    m=modelo['modelo'];a=modelo.get('ator');es=a['escala'] if a else [1,1,1]
    tam=[m['tamanho'][i]*es[i] for i in range(3)]
    g=a['rot'][1] if a else 0
    if a:
        rad=math.radians(g);cx=m['centro'][0]*es[0];cy=m['centro'][1]*es[1]
        centro=[a['loc'][0]+cx*math.cos(rad)-cy*math.sin(rad),a['loc'][1]+cx*math.sin(rad)+cy*math.cos(rad)]
        base=a['loc'][2]+m['min_z']*es[2]
    else: centro=[s['x']+s['largura']/2,s['y']+s['comprimento']/2];base=s['z']
    o={'tipo':'asset','sala':sid,'modelo':m,'classe':a['classe'] if a else '/Script/Engine.StaticMeshActor',
       'x':s['x']+pedido['x_m']*100 if 'x_m' in pedido else centro[0],
       'y':s['y']+pedido['y_m']*100 if 'y_m' in pedido else centro[1],
       'z':s['z'] if 'x_m' in pedido or 'y_m' in pedido else base,'giro':pedido.get('giro',g),
       'categoria':pedido.get('categoria','generico')}
    for i,k in enumerate(('largura','profundidade','altura')): o[k]=pedido.get(k+'_m',tam[i]/100)*100
    if 'z_m' in pedido:o['z']=s['z']+pedido['z_m']*100
    ancora=pedido.get('na_parede') or ('teto' if pedido.get('no_teto') else None)
    if ancora:
        if pedido.get('sobre'):raise ValueError('escolha ancora ou sobre')
        if ancora=='teto':
            o['ancora']={'tipo':'teto'};o['z']=s['z']+s['altura']-o['altura']-.5
        else:
            if ancora not in operacoes.LADOS:raise ValueError('na_parede: sul, norte, oeste ou leste')
            if 'z_m' not in pedido:raise ValueError('ancora de parede requer z_m da base')
            o['ancora']={'tipo':'parede','lado':ancora};o['giro']={'sul':0,'norte':180,'oeste':-90,'leste':90}[ancora]
            pos=pedido.get('posicao_m',operacoes.lado_cm(s,ancora)/200)*100
            n=o['profundidade']/2+.5
            o['x'],o['y']={'sul':(s['x']+pos,s['y']+n),'norte':(s['x']+pos,s['y']+s['comprimento']-n),
                         'oeste':(s['x']+n,s['y']+pos),'leste':(s['x']+s['largura']-n,s['y']+pos)}[ancora]
    sobre=pedido.get('sobre')
    if sobre:
        # Apoiado em outro movel: na altura do tampo, no centro dele se x_m/y_m faltarem.
        b=p['objetos'].get(sobre)
        if not b or b['tipo'] not in operacoes.MOVEIS or b.get('sala')!=sid:
            raise ValueError(f'sobre: {sobre!r} precisa ser um movel registrado na sala {sid}')
        if 'x_m' not in pedido:o['x']=b['x']
        if 'y_m' not in pedido:o['y']=b['y']
        esperado=s['z']+pedido['apoio_z_m']*100 if 'apoio_z_m' in pedido else None
        o['z']=_altura_de_apoio(editor,b,sobre,o,esperado_z=esperado);o['sobre']=sobre
    fixo=pedido.get('fixo',bool(ancora) or pedido.get('colisao') is False or o['categoria'] in FIXOS)
    if fixo and pedido.get('simular') is True:raise ValueError('fixo e simular ao mesmo tempo: escolha um')
    massa=pedido.get('massa_kg',MASSAS.get(o['categoria'],MASSAS['generico']))
    if not isinstance(massa,(int,float)) or isinstance(massa,bool) or not math.isfinite(massa) or massa<=0: raise ValueError('massa_kg precisa ser positiva e finita')
    o['fisica']={'simular':pedido.get('simular',not fixo),'massa_kg':massa,'amortecimento_linear':pedido.get('amortecimento_linear',.5),
                 'amortecimento_angular':pedido.get('amortecimento_angular',1.0),'subir':pedido.get('subir',False)}
    if 'colisao' in pedido:o['fisica']['colisao']=pedido['colisao']
    if acao in ('adotar','duplicar'):
        if not a: raise ValueError('informe ator para adotar/duplicar')
        o[acao]=a['caminho']
        o['apelidos']=[a['rotulo']]
    if modelo.get('converter'):o['converter']=True
    ficha={'pedido':pedido.get('pedido','objeto '+acao),'operacoes':[{'operacao':'registrar_objeto','id':pedido['id'],'modelo_json':json.dumps(o)}]}
    try:operacoes.aplicar_ficha(p,ficha)
    except operacoes.Invalida as exc:return {'ok':False,'motivo':'recusado','porque':str(exc),'objeto_criado':False}
    if ancora:
        med=medir_ancora(editor,o,s)
        if not med['confirmada']:return {'ok':False,'motivo':'ancora_nao_confirmada_no_editor','apoio':med,'objeto_criado':False}
    res=executor.executar(cena,ficha,editor,C.CENAS,C.LAB_DIR,C.WORK+'/restauracao')
    res['fisica']={'simula':o['fisica']['simular'],'fixo':bool(fixo),**({'sobre':sobre} if sobre else {})}
    res['massa']={'kg':massa,'origem':'informada' if 'massa_kg' in pedido else 'perfil_estimado','categoria':o['categoria']}
    if modelo.get('limite'):res['limite_conversao']=modelo['limite']
    return res
