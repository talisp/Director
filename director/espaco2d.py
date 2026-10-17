"""Filtro geometrico offline adaptado de SceneSmith (MIT); ver THIRD_PARTY_NOTICES.md.
Usa Shapely/GEOS, nao implementa outro motor de geometria ou de navegacao.
"""
import json,math,subprocess,sys,time
from pathlib import Path
from . import config as C
from .nucleo import planta as PL,operacoes as OP


def _poligono(o):
    from shapely.geometry import box
    from shapely.affinity import rotate,translate
    p=box(-o['largura']/2,-o['profundidade']/2,o['largura']/2,o['profundidade']/2)
    return translate(rotate(p,o.get('giro',0),origin=(0,0)),o['x'],o['y'])


def zona(a,W,H):
    from shapely.geometry import box
    pos=a['posicao'];w=a['largura'];d=80 if a['tipo']=='porta' else 50
    return box(*{'sul':(pos-w/2,0,pos+w/2,d),'norte':(pos-w/2,H-d,pos+w/2,H),
        'oeste':(0,pos-w/2,d,pos+w/2),'leste':(W-d,pos-w/2,W,pos+w/2)}[a['parede']])


def avaliar(pedido):
    from shapely.geometry import box
    from shapely.ops import unary_union
    import shapely
    t0=time.monotonic();W,H=pedido['dimensoes_cm'];raio=pedido.get('raio_cm',34)
    if any(isinstance(v,bool) or not math.isfinite(v) or v<=0 for v in (W,H,raio)):raise ValueError('dimensoes e raio positivos e finitos')
    piso=box(0,0,W,H);interno=piso.buffer(-raio)
    objetos=pedido.get('objetos',[]);polys=[(o,_poligono(o)) for o in objetos]
    inflados=[p.buffer(raio,quad_segs=32) for _,p in polys]
    def regioes(g):
        if g.is_empty:return []
        if g.geom_type=='Polygon':return [g] if g.area>1e-6 else []
        return [p for filho in getattr(g,'geoms',[]) for p in regioes(filho)]
    def livre(ignorar=None):
        pp=[p for i,p in enumerate(inflados) if i!=ignorar]
        return interno.difference(unary_union(pp)) if pp else interno
    walk=livre();areas=regioes(walk);n=len(areas)
    bloqueios=[o['id'] for i,(o,_) in enumerate(polys) if len(regioes(livre(i)))==1] if n!=1 else []
    violacoes=[]
    for o,p in polys:
        if not piso.buffer(1e-6).covers(p):violacoes.append({'objeto':o['id'],'tipo':'fora_do_piso'})
    for a in pedido.get('aberturas',[]):
        z0=a.get('peitoril',0) if a['tipo']=='janela' else 0;z1=z0+a['altura'];z=zona(a,W,H)
        for o,p in polys:
            if o.get('z',0)+o['altura']<=z0 or o.get('z',0)>=z1:continue
            inter=z.intersection(p)
            if inter.area<=1e-6:continue
            b=inter.bounds;eixo=1 if a['parede'] in ('sul','norte') else 0
            violacoes.append({'objeto':o['id'],'abertura':a['id'],'tipo':'area_livre_'+a['tipo'],
                'invasao_cm':round(b[eixo+2]-b[eixo],3),'area_cm2':round(inter.area,3)})
    # Acesso: da porta tem de dar para chegar a cada area de uso pedida. Bolsao sem alvo nao reprova.
    alvos=list(pedido.get('alvos',[]))
    portas=[a for a in pedido.get('aberturas',[]) if a['tipo']=='porta']
    acessos=[]
    def regiao_de(caixa):
        alvo=box(*caixa);toca=[i for i,r in enumerate(areas) if r.intersects(alvo) and r.intersection(alvo).area>1]
        return toca
    if alvos and portas:
        entrada=set()
        for a in portas:entrada.update(regiao_de(zona(a,W,H).bounds))
        for t in alvos:
            toca=regiao_de(t['caixa'])
            acessos.append({'id':t['id'],'alcancado':bool(entrada.intersection(toca))})
        aprovado=not violacoes and bool(entrada) and all(a['alcancado'] for a in acessos)
        criterio='porta alcanca cada area de uso; bolsoes sem alvo nao reprovam'
    else:
        aprovado=not violacoes and n==1
        criterio='uma unica regiao livre (sem alvos ou sem porta informados)'
    return {'ok':True,'aprovado':aprovado,'criterio':criterio,'acessos':acessos,'raio_cm':raio,'regioes':n,
        'proporcao_maior_regiao':round(max((p.area for p in areas),default=0)/sum((p.area for p in areas),0),6) if areas else 0,
        'area_livre_cm2':round(walk.area,3),'bloqueadores_individuais':bloqueios,'violacoes':violacoes,
        'segundos':round(time.monotonic()-t0,6),'backend':'Shapely '+shapely.__version__,
        'nao_verificado':['somente pegadas e intervalos de altura informados; atores fora da planta nao sao incluidos',
            'acesso medido so ate as areas de uso informadas; sem alvos, uma regiao conexa nao prova acesso desde a porta',
            'buffer circular aproximado, sem interacao de porta, fisica ou NavMesh; requer verificar no motor']}


def na_planta(planta,sid,extras=None):
    s=planta['objetos'][sid];objetos=[];aberturas=[]
    for oid,o in planta['objetos'].items():
        if o.get('sala')!=sid:continue
        if o['tipo'] in OP.MOVEIS:objetos.append({**o,'id':oid,'x':o['x']-s['x'],'y':o['y']-s['y'],'z':o.get('z',s['z'])-s['z']})
        elif o['tipo'] in OP.VAOS:aberturas.append({**o,'id':oid})
    return {'dimensoes_cm':[s['largura'],s['comprimento']],'objetos':objetos+(extras or []),'aberturas':aberturas}


def executar(pedido):
    try:return avaliar(pedido)
    except ImportError:
        exe=Path(C.RAIZ)/'.venv-planejamento'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
        if not exe.is_file():return {'ok':False,'motivo':'instale requirements-planejamento.txt em .venv-planejamento'}
        r=subprocess.run([str(exe),'-m','director.espaco2d'],input=json.dumps(pedido).encode(),capture_output=True,timeout=30,cwd=C.RAIZ)
        if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-1500:])
        return json.loads(r.stdout)


def cli(args):
    p=PL.carregar(C.CENAS,args[0]);sid=args[1]
    if sid not in p['objetos'] or p['objetos'][sid]['tipo']!='sala':raise ValueError('informe sala existente')
    q=na_planta(p,sid)
    return {'cena':args[0],'sala':sid,**executar(q)}


if __name__=='__main__':print(json.dumps(avaliar(json.loads(sys.stdin.buffer.read())),ensure_ascii=True))
