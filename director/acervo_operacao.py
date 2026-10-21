"""Operacoes explicitas do acervo; sem agente, servico ou execucao de receitas."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import urllib.request
from urllib.parse import quote

from . import acervo as A


def planejar_download(oid, db=None):
    with A.abrir(db) as c:
        d=A.detalhe(c,oid)['objeto']
    valores={v['nome']:json.loads(v['valor_json']) for v in d['caracteristicas']}
    if d['fonte']!='artvip':
        raise ValueError('download automatizado desta entrega aceita ArtVIP; HSSD exige aceite/autenticacao e Fab aquisicao pelo usuario')
    revisao=valores['revisao_remota']
    if len(revisao)!=40 or any(x not in '0123456789abcdef' for x in revisao):raise ValueError('revisao invalida')
    files=[]
    for f in valores['arquivos']:
        p=PurePosixPath(f['caminho'])
        if p.is_absolute() or '..' in p.parts or '\\' in str(p):raise ValueError('caminho remoto invalido')
        if not str(p).startswith(d['chave']+'/'):raise ValueError('arquivo fora do objeto')
        if not isinstance(f.get('bytes'),int) or f['bytes']<0:raise ValueError('tamanho remoto desconhecido')
        files.append({**f,'url':'https://huggingface.co/datasets/x-humanoid-robomind/ArtVIP/resolve/'+revisao+'/'+quote(str(p),safe='/')})
    return {'ok':True,'objeto':oid,'fonte':d['fonte'],'licenca':d['licenca'],'revisao':revisao,
            'principal':valores['arquivo_principal'],'arquivos':files,'bytes':sum(f['bytes'] for f in files),
            'limite':'arquivos da pasta; referencias USD/MDL compartilhadas ainda precisam de verificacao'}


def baixar(pedido,db=None):
    from .acervo_coleta import trava_escopo
    with trava_escopo(db,A.identidade('download',pedido['objeto'])):
        return _baixar(pedido,db)


def _baixar(pedido,db=None):
    plano=planejar_download(pedido['objeto'],db)
    if pedido.get('autorizar_download') is not True:raise ValueError('use planejar_download antes; download exige autorizar_download:true')
    if not pedido.get('origem'):raise ValueError('origem da autorizacao obrigatoria')
    base=Path(A.PADRAO).absolute().parent.parent
    raiz=Path(pedido.get('destino',str(base/'ArtVIP'))).absolute()
    if not raiz.resolve().is_relative_to(base.resolve()):raise ValueError('downloads devem ficar em R:/CINF/BD')
    limite=pedido.get('max_bytes',10*1024*1024)
    if not isinstance(limite,int) or limite<=0 or plano['bytes']>limite:raise ValueError('lote acima do limite autorizado')
    if shutil.disk_usage(base).free<plano['bytes']+16*1024*1024:raise ValueError('espaco insuficiente')
    raiz.mkdir(parents=True,exist_ok=True);saidas=[]
    for f in plano['arquivos']:
        dest=raiz/plano['revisao']/f['caminho']
        if not dest.resolve().is_relative_to(raiz.resolve()):raise ValueError('destino fora da pasta')
        dest.parent.mkdir(parents=True,exist_ok=True)
        esperado=f.get('sha256');blob=f.get('git_blob')
        def conferir(p):
            if p.stat().st_size!=f['bytes']:raise ValueError('tamanho divergente: '+str(p))
            sha=hashlib.sha256(p.read_bytes()).hexdigest()
            if esperado and sha!=esperado:raise ValueError('SHA256 divergente')
            if not esperado:
                if not blob:raise ValueError('hash remoto ausente')
                git=hashlib.sha1(b'blob '+str(f['bytes']).encode()+b'\0'+p.read_bytes()).hexdigest()
                if git!=blob:raise ValueError('hash git divergente')
            return sha
        reutilizado=dest.exists()
        if reutilizado:sha=conferir(dest)
        else:
            # Nao segue instrucoes dos arquivos; baixa bytes com tamanho/hash fixados.
            tmp=dest.with_name(dest.name+'.part')
            try:
                req=urllib.request.Request(f['url'],headers={'User-Agent':'Director-acervo/1.0'})
                with urllib.request.urlopen(req,timeout=60) as r,tmp.open('wb') as out:
                    total=0
                    while b:=r.read(min(1024*1024,f['bytes']-total+1)):
                        total+=len(b)
                        if total>f['bytes']:raise ValueError('resposta maior que tamanho catalogado')
                        out.write(b)
                sha=conferir(tmp);os.replace(tmp,dest)
            finally:
                if tmp.exists():tmp.unlink()
        saidas.append({'caminho':str(dest),'sha256':sha,'bytes':f['bytes'],'reutilizado':reutilizado})
    principal=raiz/plano['revisao']/plano['principal']
    with A.abrir(db,escrita=True) as c:
        A.arquivo(c,principal,licenca=plano['licenca'],origem=pedido['origem'],objeto_id=plano['objeto'])
        A.registro(c,'download',plano['objeto'],{'plano':plano,'arquivos':saidas},pedido['origem']);A.indexar_busca(c,[plano['objeto']])
    return {'ok':True,'objeto':plano['objeto'],'principal':str(principal),'arquivos':saidas,
            'bytes':plano['bytes'],'limite':plano['limite'],
            'registro_sql':{'arquivo_indexado':str(principal),'dependencias':'hashes e caminhos no manifesto de download; nao sao objetos separados'}}


def sincronizar(cena,db=None):
    """Captura da planta salva; nao declara que instancias sejam novos modelos."""
    from . import config as C
    from .nucleo import planta as PL
    p=PL.caminho(C.CENAS,cena)
    d=A.ler(p);projeto=str(Path(C.LAB_UPROJECT).resolve())
    with A.abrir(db,escrita=True) as c:
        modelos=[]
        for ator,o in d['objetos'].items():
            A.instancia(c,projeto,d['nivel'],ator,ator,'planta_planejada',o,p)
            asset=o.get('modelo',{}).get('asset')
            if asset:modelos.append(A.asset(c,projeto,asset,origem='planta:'+p))
        # Ausencia e explicitada, sem apagar versoes nem receitas antigas.
        A.registro(c,'estado_cena',projeto+'|'+d['nivel'],
                   {'atores_atuais':sorted(d['objetos']),'revisao':d['revisao']},p)
        A.indexar_busca(c,modelos)
    return {'ok':True,'instancias':len(d['objetos']),'revisao':d['revisao'],'nivel':d['nivel'],
            'limite':'planta persistida; nao e certificacao fisica nem promocao automatica a receita'}


def apos_operacao(cena,res,db=None):
    if not res.get('ok'):return res
    # Banco indisponivel nao desfaz uma operacao ja salva e aprovada no Unreal.
    try:res['acervo']=sincronizar(cena,db)
    except Exception as exc:
        res['acervo']={'ok':False,'erro':str(exc),'proxima_acao':'sincronizar novamente o acervo; nao repetir a alteracao no Unreal'}
    return res


def rotular(pedido,db=None):
    """Aliases existentes, sem inventar geometria, material ou capacidade funcional."""
    from .catalogo import _aliases
    n=0;sem=[]
    with A.abrir(db,escrita=True) as c:
        rows=c.execute('SELECT id,nome FROM objetos ORDER BY id').fetchall()
        for r in rows:
            cats,aliases=_aliases(r['nome'])
            if not cats:
                sem.append(r['id']);continue
            for t in cats:A.tag(c,r['id'],t.replace('_',' '),'pt','taxonomia_director_sugerida_v1')
            for t in aliases:A.tag(c,r['id'],t,'indefinido','alias_director_sugerido_v1')
            n+=1
        A.indexar_busca(c)
    return {'ok':True,'objetos_rotulados':n,'sem_categoria':len(sem),
            'limite':'categorias sugeridas por aliases; nao e descricao individual validada nem prova de funcao'}


def inspecionar_usd(pedido,db=None,editor=None):
    from .ponte import Ponte
    with A.abrir(db) as c:d=A.detalhe(c,pedido['objeto'])['objeto']
    arquivo=pedido.get('arquivo')
    if not arquivo:
        candidatos=[f['caminho'] for f in d['arquivos'] if f['presente'] and Path(f['caminho']).suffix.lower() in ('.usd','.usda','.usdc')]
        if len(candidatos)!=1:raise ValueError('informe arquivo: esperado um unico USD registrado presente; encontrados '+str(len(candidatos)))
        arquivo=candidatos[0]
    p=Path(arquivo).absolute()
    f=next((f for f in d['arquivos'] if Path(f['caminho']).resolve()==p.resolve()),None)
    if f is None or hashlib.sha256(p.read_bytes()).hexdigest()!=f['sha256']:raise ValueError('USD ausente do acervo ou alterado')
    if p.suffix.lower() not in ('.usd','.usda','.usdc'):raise ValueError('requer USD')
    if editor is None:
        with Ponte('acervo-usd') as ponte:return inspecionar_usd(pedido,db,ponte)
    codigo=Path(__file__).with_name('editor').joinpath('acervo_usd.py').read_text(encoding='utf-8')
    r=editor.chamar('dev_exec',codigo=codigo+'\nresultado=inspecionar('+repr(str(p))+')')['resultado']
    with A.abrir(db,escrita=True) as c:
        A.registro(c,'inspecao_usd_nativa',pedido['objeto'],r,str(p))
        for k,v in r.items():A.caracteristica(c,pedido['objeto'],k,v,'pxr_do_unreal_sem_simulacao',str(p))
    return {'ok':not r['dependencias_ausentes'],**r,'limite':'juntas declaradas em USD nao comprovam articulacao importada ou simulada no Chaos'}


def importar(pedido,db=None,editor=None):
    from .ponte import Ponte
    from . import config as C
    from .acervo_coleta import assinatura_arquivo
    oid=pedido['objeto']
    with A.abrir(db) as c:d=A.detalhe(c,oid)['objeto']
    arquivo=pedido.get('arquivo')
    if not arquivo:
        candidatos=[f['caminho'] for f in d['arquivos'] if f['presente'] and Path(f['caminho']).suffix.lower() in ('.glb','.gltf','.usd','.usda','.usdc')]
        if len(candidatos)!=1:raise ValueError('informe arquivo: esperado um unico modelo registrado presente; encontrados '+str(len(candidatos)))
        arquivo=candidatos[0]
    p=Path(arquivo).absolute()
    atual=next((f for f in d['arquivos'] if Path(f['caminho']).resolve()==p.resolve() and f['presente']),None)
    if atual is None:raise ValueError('arquivo deve estar registrado para este objeto')
    usd=p.suffix.lower() in ('.usd','.usda','.usdc')
    if p.suffix.lower() not in ('.glb','.gltf','.usd','.usda','.usdc'):raise ValueError('requer glTF/GLB ou USD')
    if usd and pedido.get('modo_usd')!='malhas':raise ValueError('USD requer modo_usd:malhas; importa geometria, nao promete hierarquia de atores nem articulacoes Chaos')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=atual['sha256']:raise ValueError('arquivo mudou; reinspecione antes de importar')
    assinatura_arquivo(p,p.parent.resolve())
    destino=pedido['destino']
    import re
    if not re.fullmatch('/Game/Director/Acervo/[A-Za-z0-9_]+',destino):raise ValueError('destino deve ser pasta nova em /Game/Director/Acervo')
    if not pedido.get('origem'):raise ValueError('origem obrigatoria')
    if editor is None:
        with Ponte('acervo-importar') as ponte:return importar(pedido,db,ponte)
    antes=editor.chamar('info')
    if antes['em_play'] or antes['por_salvar']:raise ValueError('editor em Play ou com pacotes pendentes')
    codigo=Path(__file__).with_name('editor').joinpath('acervo_importacao.py').read_text(encoding='utf-8')
    resultado=editor.chamar('dev_exec',codigo=codigo+'\nresultado=importar('+repr(str(p))+','+repr(destino)+',usd='+repr(usd)+')')['resultado']
    depois=editor.chamar('info')
    resultado['preservacao']={'mesmo_level':antes['level']==depois['level'],'sem_play':not depois['em_play'],'sem_pendencias':not depois['por_salvar']}
    if not all(resultado['preservacao'].values()):resultado['ok']=False
    if not resultado.get('ok'):return resultado
    # N meshes pertencem ao mesmo candidato; nenhuma suposicao de mesh unico.
    with A.abrir(db,escrita=True) as c:
        for mesh in resultado['malhas']:A.asset(c,str(Path(C.LAB_UPROJECT).resolve()),mesh['asset'],origem=pedido['origem'],objeto_id=oid)
        A.registro(c,'importacao_unreal',oid,resultado,pedido['origem']);A.indexar_busca(c,[oid])
    return {'objeto':oid,**resultado,'limite':'malhas importadas; nao instancia na cena, nao certifica estabilidade, articulacao ou escala humana'}


def executar(pedido,db=None):
    acao=pedido['acao']
    if acao=='planejar_download':return planejar_download(pedido['objeto'],db)
    if acao=='baixar':return baixar(pedido,db)
    if acao=='importar':return importar(pedido,db)
    if acao=='inspecionar_usd':return inspecionar_usd(pedido,db)
    if acao=='sincronizar':return sincronizar(pedido['cena'],db)
    if acao=='rotular':return rotular(pedido,db)
    raise ValueError('operacao de acervo desconhecida')
