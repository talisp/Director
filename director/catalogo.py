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
 'cadeira':['chair','chair desk','desk chair','seat','stool','assento','banco','armchair','poltrona'],
 'cama':['bed','singlebed','bedsingle','solteiro'],
 'criado_mudo':['nightstand','bedside','bedside table','cabinetbed','cabinet bed','cabeceira'],
 'estante':['bookcase','bookshelf','shelving'],
 'guarda_roupa':['wardrobe','closet','armario','cabinet','guardaroupa'],
 'escrivaninha':['desk','estudos','study'],
 'mesa':['table'],'sofa':['couch','sofa'],
}
PALAVRAS_COMUNS=set('a o as os de da do das dos e em no na nos nas com para por um uma the of an and in on with to for'.split())
AVISO_CENA='objeto da cena; categoria sugerida pelo nome, conferir antes de usar'
AVISO_PROJETO='asset do projeto; dimensoes ainda nao inspecionadas'


def normalizar(s):
    s=re.sub(r'([a-z])([A-Z])',r'\1 \2',s)
    return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()


def _palavras(s):
    return set(re.sub(r'\d+','',normalizar(s)).split())


def _aliases(texto):
    words=_palavras(texto);cats=[];aliases=[];matches=[]
    for cat,terms in SINONIMOS.items():
        for t in [cat,*terms]:
            p=_palavras(t)
            if p<=words:matches.append((cat,p))
    # 'cabinet bed' e criado-mudo; seus fragmentos nao provam cama nem guarda-roupa.
    for cat,terms in SINONIMOS.items():
        if any(c==cat and not any(p<outro and c2!=cat for c2,outro in matches) for c,p in matches):
            cats.append(cat);aliases.extend([cat,*terms])
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
        if o.get('categoria') in SINONIMOS:
            cats=[o['categoria']];aliases=[o['categoria'],*SINONIMOS[o['categoria']]]
        entries.append({'nome':a['rotulo'],'caminho':a['caminho'],'origem':'cena','estado':'importado',
            'id':a['id'],'na_planta':bool(o),'categoria':cats,'sinonimos':aliases+o.get('apelidos',[]),
            'dimensoes_cm':a.get('dimensoes_cm'),'assets':a['assets'],'classe':a['classe'],
            'aviso':AVISO_CENA})
    for a in snapshot['assets']:
        cats,aliases=_aliases(a['nome'])
        entries.append({**a,'origem':'projeto','estado':'importado','categoria':cats,'sinonimos':aliases,
                        'dimensoes_cm':None,'aviso':AVISO_PROJETO})
    bib=Path(C.BIBLIOTECA)/'indice.json'
    if bib.is_file():entries.extend(json.loads(bib.read_text(encoding='utf-8')).get('itens',[]))
    dados={'gerado_em':dt.datetime.now(dt.timezone.utc).isoformat(),'level':snapshot['level'],'motor':snapshot['motor'],'itens':entries}
    (base/'indice.json').write_text(json.dumps(dados,ensure_ascii=True,indent=2),encoding='utf-8')
    return {'ok':True,'arquivo':str(base/'indice.json'),'total':len(entries),'segundos':round(time.monotonic()-t0,3),'dados':dados}


def consultar(dados,pedido):
    busca=_palavras(pedido.get('texto',''))-PALAVRAS_COMUNS
    categorias_busca=set(_aliases(pedido.get('texto',''))[0])
    expandido=set(busca)
    for cat,terms in SINONIMOS.items():
        if any(_palavras(t)<=busca for t in [cat,*terms]):
            for t in [cat,*terms]:expandido.update(_palavras(t))
    resultados=[]
    for a in dados['itens']:
        if pedido.get('texto','').strip() and not busca:continue
        if categorias_busca and a.get('categoria') and not categorias_busca.intersection(a['categoria']):continue
        descricao=a.get('descricao','')
        # Compativel tambem com indices antigos: orientacao nao identifica o objeto.
        if descricao in (AVISO_CENA,AVISO_PROJETO):descricao=''
        texto=' '.join([a['nome'],descricao,a.get('classe',''),*a.get('categoria',[]),*a.get('sinonimos',[])])
        words=_palavras(texto)
        score=len(busca&words)*3+len(expandido&words)
        if busca and score==0:continue
        if pedido.get('categoria') and pedido['categoria'] not in a.get('categoria',[]):continue
        dims=a.get('dimensoes_cm')
        if pedido.get('maximo_cm'):
            if not dims or any(d>lim for d,lim in zip(dims,pedido['maximo_cm'])):continue
        if pedido.get('minimo_cm'):
            if not dims or any(d<lim for d,lim in zip(dims,pedido['minimo_cm'])):continue
        resultados.append(({'cena':0,'projeto':1,'offline':2}.get(a['origem'],3),-score,a['nome'],a))
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
