"""Objetos com identidade na planta, reutilizando o executor transacional."""
import json
import math
from . import config as C
from .nucleo import planta as PL,executor,operacoes

MASSAS={'cama':45,'criado_mudo':12,'guarda_roupa':80,'escrivaninha':25,'cadeira':8,'mesa':25,'generico':20,
        'travesseiro':.6,'notebook':2.2,'computador':8,'livro':1,'abajur':2,'objeto_pequeno':1}
# Pecas da construcao: ficam paradas, sem simular fisica (box nao e um movel que cai).
FIXOS=('box','box_chuveiro','chuveiro','vaso_sanitario','pia','bancada','divisoria','parede','bancada_pia')


def _altura_de_apoio(editor,b,sobre,o,folga=2.0,irregular=3.0):
    """Altura real da superficie sob o objeto: raios para baixo no centro e nos quatro cantos.
    O topo da caixa do movel engana (a cabeceira da cama e mais alta que o colchao: visto em 17/10)."""
    g=math.radians(o['giro']);hw,hd=max(o['largura']/2-folga,0),max(o['profundidade']/2-folga,0)
    pts=[(0,0)]+[(sx*hw,sy*hd) for sx in (-1,1) for sy in (-1,1)]
    topo=b.get('z',0)+b['altura']
    qs=[{'tipo':'raio','de':[o['x']+px*math.cos(g)-py*math.sin(g),o['y']+px*math.sin(g)+py*math.cos(g),topo+50],
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
    return max(zs)


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
    sobre=pedido.get('sobre')
    if sobre:
        # Apoiado em outro movel: na altura do tampo, no centro dele se x_m/y_m faltarem.
        b=p['objetos'].get(sobre)
        if not b or b['tipo'] not in operacoes.MOVEIS or b.get('sala')!=sid:
            raise ValueError(f'sobre: {sobre!r} precisa ser um movel registrado na sala {sid}')
        if 'x_m' not in pedido:o['x']=b['x']
        if 'y_m' not in pedido:o['y']=b['y']
        o['z']=_altura_de_apoio(editor,b,sobre,o);o['sobre']=sobre
    fixo=pedido.get('fixo',o['categoria'] in FIXOS)
    if fixo and pedido.get('simular') is True:raise ValueError('fixo e simular ao mesmo tempo: escolha um')
    massa=pedido.get('massa_kg',MASSAS.get(o['categoria'],MASSAS['generico']))
    if not isinstance(massa,(int,float)) or isinstance(massa,bool) or not math.isfinite(massa) or massa<=0: raise ValueError('massa_kg precisa ser positiva e finita')
    o['fisica']={'simular':pedido.get('simular',not fixo),'massa_kg':massa,'amortecimento_linear':pedido.get('amortecimento_linear',.5),
                 'amortecimento_angular':pedido.get('amortecimento_angular',1.0),'subir':pedido.get('subir',False)}
    if acao in ('adotar','duplicar'):
        if not a: raise ValueError('informe ator para adotar/duplicar')
        o[acao]=a['caminho']
        o['apelidos']=[a['rotulo']]
    if modelo.get('converter'):o['converter']=True
    ficha={'pedido':pedido.get('pedido','objeto '+acao),'operacoes':[{'operacao':'registrar_objeto','id':pedido['id'],'modelo_json':json.dumps(o)}]}
    try:operacoes.aplicar_ficha(p,ficha)
    except operacoes.Invalida as exc:return {'ok':False,'motivo':'recusado','porque':str(exc),'objeto_criado':False}
    res=executor.executar(cena,ficha,editor,C.CENAS,C.LAB_DIR,C.WORK+'/restauracao')
    res['fisica']={'simula':o['fisica']['simular'],'fixo':bool(fixo),**({'sobre':sobre} if sobre else {})}
    res['massa']={'kg':massa,'origem':'informada' if 'massa_kg' in pedido else 'perfil_estimado','categoria':o['categoria']}
    if modelo.get('limite'):res['limite_conversao']=modelo['limite']
    return res
