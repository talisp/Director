"""Consulta curta de documentacao exportada pelo proprio editor instalado."""
import json,re
from pathlib import Path
from . import config as C

CLASSES=['Actor','StaticMeshActor','StaticMeshComponent','DynamicMeshComponent','EditorActorSubsystem',
'LevelEditorSubsystem','UnrealEditorSubsystem','SystemLibrary','NavigationSystemV1','RecastNavMesh',
'NavModifierVolume','NavModifierComponent','NavMeshResolutionParam','Character','AIController',
'PhysicsSettings','GeometryScript_NewAssetUtils','GeometryScript_Collision','EditorStaticMeshLibrary',
'StaticMeshEditorSubsystem','EditorAssetLibrary','AssetRegistryHelpers','AssetRegistry','StaticMesh',
'BoxSphereBounds','EditorLoadingAndSavingUtils','PythonScriptLibrary','PythonLogOutputEntry','PythonLogOutputType']
ALIASES={'massa':'mass','fisica':'physics','cadeira':'mesh','navegacao':'navigation','amortecimento':'damping','colisao':'collision','salvar':'save','velocidade':'velocity'}


def caminho():return Path(C.WORK)/'api'/'instalada.json'


def consultar(dados,termo,limite=5):
    palavras=re.findall(r'[\w]+',termo.lower())
    palavras=[ALIASES.get(x,x) for x in palavras]
    encontrados=[]
    for e in dados['entradas']:
        nome=e['simbolo'].lower();txt=nome+' '+e['doc'].lower()
        if not palavras or not all(x in txt for x in palavras):continue
        score=sum(10 if x in nome else 1 for x in palavras)
        encontrados.append((score,e))
    encontrados.sort(key=lambda x:(-x[0],x[1]['simbolo']))
    return {'ok':True,'fonte':dados['meta'],'total':len(encontrados),'resultados':[
        {'simbolo':e['simbolo'],'tipo':e['tipo'],'doc':e['doc'][:1800],'texto_truncado':len(e['doc'])>1800}
        for _,e in encontrados[:min(int(limite),10)]], 'limite':'documentacao real nao prova que uma chamada executa neste contexto; confira no ensaio'}


def cli(args):
    if args and args[0]=='atualizar':
        from .ponte import Ponte
        classes=CLASSES if len(args)==1 else json.loads(Path(args[1]).read_text(encoding='utf-8-sig'))['classes']
        with Ponte('director-api') as p:r=p.chamar('api_export',caminho=str(caminho()),classes=classes)
        return {'ok':True,**r}
    if not caminho().is_file():return {'ok':False,'motivo':'gere a referencia com api atualizar'}
    return consultar(json.loads(caminho().read_text(encoding='utf-8')),' '.join(args))
