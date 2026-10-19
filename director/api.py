"""Consulta curta de documentacao exportada pelo proprio editor instalado."""
import json,re,unicodedata
from pathlib import Path
from . import config as C

CLASSES=['Actor','StaticMeshActor','StaticMeshComponent','DynamicMeshComponent','EditorActorSubsystem',
'LevelEditorSubsystem','UnrealEditorSubsystem','SystemLibrary','NavigationSystemV1','RecastNavMesh',
'NavModifierVolume','NavModifierComponent','NavMeshResolutionParam','Character','AIController',
'PhysicsSettings','GeometryScript_NewAssetUtils','GeometryScript_Collision','EditorStaticMeshLibrary',
'StaticMeshEditorSubsystem','EditorAssetLibrary','AssetRegistryHelpers','AssetRegistry','StaticMesh',
'BoxSphereBounds','EditorLoadingAndSavingUtils','PythonScriptLibrary','PythonLogOutputEntry','PythonLogOutputType',
'CollisionEnabled','ComponentMobility','TraceTypeQuery','DrawDebugTrace']
ALIASES={'massa':'mass','fisica':'physics','cadeira':'mesh','navegacao':'navigation','amortecimento':'damping','colisao':'collision','salvar':'save','velocidade':'velocity'}
ALIASES.update(atores='actor',ator='actor',componentes='component',componente='component')
IGNORAR={'de','da','do','das','dos','a','o','os','as','no','na','em','para'}


def _normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFKD',texto.lower()) if not unicodedata.combining(c))


def _trecho(doc,palavras,limite=1200):
    """Preserva o trecho que casou, em vez de cortar sempre o comeco da classe."""
    texto=_normalizar(doc)
    pos=min((texto.find(p) for p in palavras if p in texto),default=0)
    inicio=max(0,pos-160)
    return doc[inicio:inicio+limite],inicio>0 or len(doc)>inicio+limite


def caminho():return Path(C.WORK)/'api'/'instalada.json'


def consultar(dados,termo,limite=5):
    palavras=re.findall(r'[\w]+',_normalizar(termo))
    palavras=[ALIASES.get(x,x) for x in palavras if x not in IGNORAR]
    encontrados=[]
    for e in dados['entradas']:
        nome=_normalizar(e['simbolo']);txt=nome+' '+_normalizar(e['doc'])
        compacto=re.sub(r'[^a-z0-9]','',nome)
        def no_nome(x):return x in nome or re.sub(r'[^a-z0-9]','',x) in compacto
        if not palavras or not all(x in txt or no_nome(x) for x in palavras):continue
        score=sum(10 if no_nome(x) else 1 for x in palavras)
        encontrados.append((score,e))
    encontrados.sort(key=lambda x:(-x[0],x[1]['simbolo']))
    resultados=[]
    for _,e in encontrados[:max(1,min(int(limite),10))]:
        trecho,truncado=_trecho(e['doc'],palavras)
        resultados.append({'simbolo':e['simbolo'],'tipo':e['tipo'],'doc':trecho,'texto_truncado':truncado})
    return {'ok':True,'fonte':dados['meta'],'total':len(encontrados),'resultados':resultados,
            'limite':'documentacao real nao prova que uma chamada executa neste contexto; confira no ensaio'}


def cli(args):
    if args and args[0]=='atualizar':
        from .ponte import Ponte
        classes=CLASSES if len(args)==1 else json.loads(Path(args[1]).read_text(encoding='utf-8-sig'))['classes']
        with Ponte('director-api') as p:r=p.chamar('api_export',caminho=str(caminho()),classes=classes)
        return {'ok':True,**r}
    if not caminho().is_file():return {'ok':False,'motivo':'gere a referencia com api atualizar'}
    return consultar(json.loads(caminho().read_text(encoding='utf-8')),' '.join(args))
