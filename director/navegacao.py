"""Navegacao: escopo declarado, backup antes da mudanca e tempo observado."""
import json,math,time,uuid
from pathlib import Path
from . import config as C


def _aguardar(editor,fim):
    calmas=0
    while time.monotonic()<fim:
        m=editor.chamar('measure',consultas=[{'tipo':'nav'}])['medidas'][0]
        calmas=calmas+1 if m.get('pronta') else 0
        if calmas>=2:return True
        time.sleep(min(.2,max(0,fim-time.monotonic())))
    return False


def executar(pedido,editor):
    acao=pedido.get('acao','diagnosticar')
    if acao=='diagnosticar':return {'ok':True,**editor.chamar('nav_config')}
    if acao not in ('ajustar','restaurar','reconstruir'):raise ValueError('acao desconhecida')
    prazo=float(pedido.get('prazo_s',20))
    if not math.isfinite(prazo) or not 0<prazo<=60:raise ValueError('prazo_s deve estar entre 0 e 60 segundos, maior que zero')
    t0=time.monotonic();fim=t0+prazo
    backup=json.loads(Path(pedido['backup']).read_text(encoding='utf-8')) if acao=='restaurar' else None
    antes=editor.chamar('nav_config');antes['criados']=[]
    # Build durante AsyncLoadLock pode ser descartado pelo motor ao terminar a carga.
    if not _aguardar(editor,fim):
        return {'ok':False,'motivo':'navegacao_ocupada','nenhuma_alteracao':True,
                'tempo_observado_s':round(time.monotonic()-t0,3),'conectividade_verificada':False}
    pasta=Path(C.WORK)/'navegacao';pasta.mkdir(parents=True,exist_ok=True)
    arquivo=pasta/(uuid.uuid4().hex+'.json')
    arquivo.write_text(json.dumps(antes,ensure_ascii=True,indent=2),encoding='utf-8')
    try:
        r=editor.chamar('nav_config',acao=acao,escopo=pedido.get('escopo','regiao'),
            regiao=pedido.get('regiao'),celula_cm=pedido.get('celula_cm',5),altura_cm=pedido.get('altura_cm',2),
            tile_cm=pedido.get('tile_cm'),backup=backup)
    except Exception as exc:
        return {'ok':False,'erro':str(exc),'backup':str(arquivo),'aviso':'pode ter ocorrido mudanca parcial; diagnosticar e restaurar'}
    arquivo.write_text(json.dumps(r.pop('backup'),ensure_ascii=True,indent=2),encoding='utf-8')
    time.sleep(min(.3,max(0,fim-time.monotonic())))
    pronta=_aguardar(editor,fim)
    r.update({'ok':True,'backup':str(arquivo),'tempo_observado_s':round(time.monotonic()-t0,3),
        'pronta':pronta,'conectividade_verificada':False,'restaurado':acao=='restaurar'})
    arquivo.with_suffix('.resultado.json').write_text(json.dumps(r,ensure_ascii=True,indent=2),encoding='utf-8')
    return r
