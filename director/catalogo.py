"""Catalogo pequeno consultavel: dados do motor + aliases, sem novo servico/RAG."""
import datetime as dt
import json
from pathlib import Path
import re
import time
import unicodedata
from . import config as C
from .nucleo import planta as PL

SINONIMOS={
 'cadeira':['chair','seat','stool','assento','banco'],
 'cama':['bed','singlebed','bedsingle','solteiro'],
 'criado_mudo':['nightstand','bedside','cabinetbed','cabeceira'],
 'guarda_roupa':['wardrobe','closet','armario','cabinet','guardaroupa'],
 'escrivaninha':['desk','estudos','study'],
 'mesa':['table'],'sofa':['couch','armchair','poltrona','sofa'],
}


def normalizar(s):
    s=re.sub(r'([a-z])([A-Z])',r'\1 \2',s)
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()


def _palavras(s):
    return set(re.sub(r'\d+','',normalizar(s)).split())


def _aliases(texto):
    words=_palavras(texto);cats=[];aliases=[]
    for cat,terms in SINONIMOS.items():
        if any(_palavras(t)<=words for t in [cat,*terms]):cats.append(cat);aliases.extend([cat,*terms])
    return cats,aliases


def atualizar(editor,raiz=None):
    t0=time.monotonic();base=Path(raiz or C.WORK)/'catalogo';base.mkdir(parents=True,exist_ok=True)
    snapshot=editor.chamar('catalog_snapshot')
    nome=snapshot['level'].rsplit('/',1)[-1].removeprefix('L_')
    planta=PL.carregar(C.CENAS,nome)
    entries=[]
    for a in snapshot['atores']:
        o=planta['objetos'].get(a['id'],{})
        cats,aliases=_aliases(a['rotulo']+' '+a['classe']+' '+o.get('categoria',''))
        entries.append({'nome':a['rotulo'],'caminho':a['caminho'],'origem':'cena','estado':'importado',
            'id':a['id'],'na_planta':bool(o),'categoria':cats,'sinonimos':aliases+o.get('apelidos',[]),
            'dimensoes_cm':a.get('dimensoes_cm'),'assets':a['assets'],'classe':a['classe'],
            'descricao':'objeto da cena; categoria sugerida pelo nome, conferir antes de usar'})
    for a in snapshot['assets']:
        cats,aliases=_aliases(a['nome'])
        entries.append({**a,'origem':'projeto','estado':'importado','categoria':cats,'sinonimos':aliases,
                        'dimensoes_cm':None,'descricao':'asset do projeto; dimensoes ainda nao inspecionadas'})
    bib=Path(C.WORK)/'biblioteca'/'indice.json'
    if bib.is_file():entries.extend(json.loads(bib.read_text(encoding='utf-8')).get('itens',[]))
    dados={'gerado_em':dt.datetime.now(dt.timezone.utc).isoformat(),'level':snapshot['level'],'motor':snapshot['motor'],'itens':entries}
    (base/'indice.json').write_text(json.dumps(dados,ensure_ascii=True,indent=2),encoding='utf-8')
    return {'ok':True,'arquivo':str(base/'indice.json'),'total':len(entries),'segundos':round(time.monotonic()-t0,3),'dados':dados}


def consultar(dados,pedido):
    busca=_palavras(pedido.get('texto',''))
    expandido=set(busca)
    for cat,terms in SINONIMOS.items():
        if any(_palavras(t)<=busca for t in [cat,*terms]):
            for t in [cat,*terms]:expandido.update(_palavras(t))
    resultados=[]
    for a in dados['itens']:
        texto=' '.join([a['nome'],a.get('descricao',''),a.get('classe',''),*a.get('categoria',[]),*a.get('sinonimos',[])])
        words=_palavras(texto)
        score=len(busca&words)*3+len(expandido&words)
        if busca and score==0:continue
        if pedido.get('categoria') and pedido['categoria'] not in a.get('categoria',[]):continue
        dims=a.get('dimensoes_cm')
        if pedido.get('maximo_cm'):
            if not dims or any(d>lim for d,lim in zip(dims,pedido['maximo_cm'])):continue
        resultados.append((a['origem']!='cena',-score,a['nome'],a))
    resultados.sort(key=lambda x:x[:3]);lim=min(int(pedido.get('limite',8)),50)
    return {'ok':True,'resultados':[x[3] for x in resultados[:lim]],'total':len(resultados),'limitado':len(resultados)>lim,
        'pesquisado':{'cena':dados.get('level'),'origens':sorted({a['origem'] for a in dados['itens']})},
        'limite':'categoria por sinonimos nao comprova equivalencia funcional; candidatos requerem inspecao'}


def cli(args,editor):
    if args and args[0]=='consultar' and len(args)==2:
        pedido=json.loads(Path(args[1]).read_text(encoding='utf-8-sig'))
    else:pedido={'texto':' '.join(args)}
    r=atualizar(editor)
    return consultar(r['dados'],pedido)
