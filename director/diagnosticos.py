"""Leitura limitada do log existente do laboratorio; correlacao temporal, nao causal."""
import datetime as dt
from pathlib import Path
import re
import time

PADRAO = re.compile(r'^(?:\[(?P<hora>[^]]+)\]\[\s*\d+\])?(?P<categoria>[\w.]+):\s*(?P<nivel>Warning|Error|Fatal):\s*(?P<mensagem>.*)$')
LIMITE_BYTES = 1024 * 1024


def iniciar(lab_dir):
    pasta = Path(lab_dir)/'Saved/Logs'
    arquivos = [p for p in pasta.glob('*.log') if 'backup-' not in p.name.lower()]
    arquivo = max(arquivos, key=lambda p:p.stat().st_mtime_ns) if arquivos else None
    return {'arquivo': arquivo, 'offset': arquivo.stat().st_size if arquivo else 0,
            'inicio': dt.datetime.now(dt.timezone.utc).isoformat(), 'tempo': time.monotonic()}


def concluir(marca, operacao, mundo=None):
    fim = dt.datetime.now(dt.timezone.utc).isoformat()
    fonte = marca['arquivo']
    base = {'operacao':operacao, 'mundo':mundo or 'nao_informado', 'inicio':marca['inicio'], 'fim':fim,
            'segundos':round(time.monotonic()-marca['tempo'], 4), 'correlacao':'apenas_temporal',
            'limite':'intervalo pode incluir eventos alheios; logs assincronos podem chegar depois', 'grupos':[]}
    if not fonte:
        return {**base, 'coleta':'log_indisponivel'}
    tamanho = fonte.stat().st_size
    if tamanho < marca['offset']:
        return {**base, 'coleta':'log_rotacionado', 'arquivo':str(fonte)}
    inicio = max(marca['offset'], tamanho-LIMITE_BYTES)
    with fonte.open('rb') as stream:
        stream.seek(inicio)
        texto = stream.read(tamanho-inicio).decode('utf-8',errors='replace')
    grupos = {}
    for linha in texto.splitlines():
        m = PADRAO.match(linha)
        if not m:continue
        d = m.groupdict();chave=(d['categoria'],d['nivel'],d['mensagem'])
        if chave not in grupos:
            grupos[chave]={'categoria':d['categoria'], 'nivel':d['nivel'], 'mensagem_original':d['mensagem'],
                           'contagem':0, 'primeira':d['hora'], 'ultima':d['hora']}
        grupos[chave]['contagem']+=1;grupos[chave]['ultima']=d['hora']
    return {**base, 'coleta':'trecho_limitado' if inicio!=marca['offset'] else 'intervalo_lido',
            'arquivo':str(fonte), 'bytes':[inicio,tamanho], 'grupos':list(grupos.values())}


def resumo(coletas):
    grupos=[{**g,'operacao':c['operacao'],'mundo':c['mundo'],'arquivo':c.get('arquivo'),
             'bytes':c.get('bytes'),'intervalo':[c['inicio'],c['fim']],'correlacao':c['correlacao']}
            for c in coletas for g in c['grupos']]
    return {'avisos_erros':sum(g['contagem'] for g in grupos), 'grupos':grupos[:8],
            'grupos_omitidos':max(0,len(grupos)-8),
            'coletas_incompletas':sum(c['coleta']!='intervalo_lido' for c in coletas),
            'limite':'correlacao temporal; zero avisos capturados nao prova ausencia de avisos atrasados nem qualidade aprovada'}
