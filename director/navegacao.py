"""Navegacao: escopo declarado, backup antes da mudanca e tempo observado."""
import json,time,uuid
from pathlib import Path
from . import config as C


def executar(pedido,editor):
    acao=pedido.get('acao','diagnosticar')
    if acao=='diagnosticar':return {'ok':True,**editor.chamar('nav_config')}
    backup=None
    if acao=='restaurar':backup=json.loads(Path(pedido['backup']).read_text(encoding='utf-8'))
    elif acao!='ajustar':raise ValueError('acao desconhecida')
    pasta=Path(C.WORK)/'navegacao';pasta.mkdir(parents=True,exist_ok=True)
    arquivo=pasta/(uuid.uuid4().hex+'.json')
    antes=editor.chamar('nav_config');antes['criados']=[]
    arquivo.write_text(json.dumps(antes,ensure_ascii=True,indent=2),encoding='utf-8')
    t0=time.monotonic()
    try:
        r=editor.chamar('nav_config',acao=acao,escopo=pedido.get('escopo','regiao'),
            regiao=pedido.get('regiao'),celula_cm=pedido.get('celula_cm',5),altura_cm=pedido.get('altura_cm',2),backup=backup)
    except Exception as exc:
        return {'ok':False,'erro':str(exc),'backup':str(arquivo),'aviso':'pode ter ocorrido mudanca parcial; diagnosticar e restaurar'}
    arquivo.write_text(json.dumps(r.pop('backup'),ensure_ascii=True,indent=2),encoding='utf-8')
    pronta=False
    time.sleep(.3)  # aguarda o quadro que atende o pedido de reconstrucao
    while time.monotonic()-t0<float(pedido.get('prazo_s',20)):
        m=editor.chamar('measure',consultas=[{'tipo':'nav'}])['medidas'][0]
        if m.get('pronta'):pronta=True;break
        time.sleep(.2)
    r.update({'ok':True,'backup':str(arquivo),'tempo_observado_s':round(time.monotonic()-t0,3),
        'pronta':pronta,'conectividade_verificada':False,'restaurado':acao=='restaurar'})
    log=arquivo.with_suffix('.resultado.json');log.write_text(json.dumps(r,ensure_ascii=True,indent=2),encoding='utf-8')
    return r
