"""Preparacao explicita de uma cena de auditoria a partir de snapshot existente."""
import json
from pathlib import Path
from . import config as C
from .nucleo import planta as PL


def preparar(cena,pasta,editor):
    PL.nova(cena)
    if Path(PL.caminho(C.CENAS,cena)).exists(): raise ValueError("cena destino ja existe")
    pasta=Path(pasta)
    p=json.loads((pasta/'planta.json').read_text(encoding='utf-8-sig'))
    origem=pasta/(p['nivel'].rsplit('/',1)[1]+'.umap')
    p['cena']=cena;p['nivel']=PL.nova(cena)['nivel']
    r=editor.chamar('level_from_snapshot',arquivo=str(origem.resolve()),caminho=p['nivel'])
    PL.gravar(C.CENAS,p)
    return {'ok':True,'cena':cena,'revisao_origem':p['revisao'],'level':p['nivel'],'snapshot_sha256':r['origem_sha256'],'teste_final_executado':False}
