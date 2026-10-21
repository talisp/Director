"""Preparacao sob demanda. O agente pede; coletores medem e persistem.

Nao aceita SQL, URL, destino, dimensoes nem aprovacao fornecidos pelo modelo.
Nao e uma barreira contra programas com acesso direto ao mesmo usuario Windows.
"""
import hashlib
import json
import os
from pathlib import Path

from . import acervo as A
from . import acervo_operacao as O
from .acervo_coleta import hash_arquivo, trava_escopo

VERSAO='2'
LIMITE_PADRAO=10*1024*1024
ASSUNTOS={'resumo','geometria','partes','fisica','animacoes','superficies','importacao','origem','anotacoes'}


def _campos(p,permitidos):
    extras=set(p)-set(permitidos)
    if extras:raise ValueError('campos nao aceitos: '+', '.join(sorted(extras)))


def _texto(v,nome,limite=500):
    if not isinstance(v,str) or not v.strip() or len(v)>limite:raise ValueError(nome+' invalido')
    return v


def _conhecido(c,oid):
    _texto(oid,'objeto',64)
    if not c.execute('SELECT 1 FROM objetos WHERE id=?',(oid,)).fetchone():raise ValueError('objeto nao encontrado; use acervo buscar')


def _persistir(db,jid,oid,pedido,etapa,estado,dados,erro=None,variante=None):
    with A.abrir(db,escrita=True) as c:
        c.execute('''INSERT INTO preparacoes VALUES(?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET variante=excluded.variante,etapa=excluded.etapa,
            estado=excluded.estado,dados_json=excluded.dados_json,erro=excluded.erro,atualizado_em=excluded.atualizado_em''',
            (jid,oid,variante,pedido.get('pedido_id','avulso'),pedido.get('sessao','nao_informada'),
             etapa,estado,A.dump(dados),erro,A.agora()))
        A.registro(c,'etapa_preparacao',jid,{'etapa':etapa,'estado':estado,'erro':erro,
            'variante':variante,'pedido_id':pedido.get('pedido_id','avulso'),
            'sessao':pedido.get('sessao','nao_informada'),'dados':dados},pedido.get('origem','controlador'))


def _assinatura(arquivos):
    # Inclui dependencias, nao apenas o principal. Leitura confere hashes novamente.
    for f in arquivos:
        p=Path(f['caminho'])
        if not p.is_file() or p.stat().st_size!=f['bytes'] or hash_arquivo(p)!=f['sha256']:
            raise ValueError('arquivo ausente ou alterado: '+str(p)+'; preparar novamente apos revisar a origem')
    conteudo=[{k:f[k] for k in ('caminho','sha256','bytes')} for f in arquivos]
    from . import config as C
    build=Path(C.EDITOR_EXE).parents[2]/'Build'/'Build.version'
    return A.identidade(VERSAO,conteudo,hash_arquivo(Path(__file__).with_name('editor')/'acervo_usd.py'),
        hash_arquivo(build) if build.is_file() else None)


def _vigencia(config,catalogo=None):
    try:
        if catalogo is not None and config.get('catalogo')!=catalogo:return 'obsoleta','catalogo/revisao remota mudou; preparar novamente'
        atual=_assinatura(config['arquivos'])
        return ('vigente' if atual==config['assinatura'] else 'obsoleta'),None
    except (OSError,ValueError) as exc:return 'obsoleta',str(exc)


def _metadado(c,vid,assunto,nome,valor,tipo,metodo,evidencia,unidade=None,referencial=None):
    mid=A.identidade(vid,assunto,nome,tipo,metodo,evidencia,valor)
    c.execute('INSERT OR IGNORE INTO metadados VALUES(?,?,?,?,?,?,?,?,?,?,?)',
        (mid,vid,assunto,nome,A.dump(valor),unidade,referencial,tipo,metodo,evidencia,A.agora()))


def _registrar(db,oid,baixado,r,assinatura):
    arquivos=list(baixado['arquivos']);vistos={str(Path(f['caminho']).resolve()) for f in arquivos}
    raiz=Path(A.PADRAO).absolute().parent.parent.resolve()
    for caminho in r.get('layers',[])+r.get('assets',[]):
        dep=Path(caminho)
        if not dep.is_absolute():dep=Path(baixado['principal']).parent/dep
        if not dep.is_file():raise ValueError('dependencia resolvida indisponivel: '+str(dep))
        dep=dep.resolve()
        if not dep.is_relative_to(raiz):raise ValueError('dependencia resolvida fora do armazenamento autorizado')
        if str(dep) not in vistos:
            arquivos.append({'caminho':str(dep),'sha256':hash_arquivo(dep),'bytes':dep.stat().st_size});vistos.add(str(dep))
    assinatura_completa=_assinatura(arquivos)
    config={'arquivos':arquivos,'assinatura':assinatura_completa,'assinatura_base':assinatura,
            'catalogo':A.identidade(O.planejar_download(oid,db)),
            'metodo':'OpenUSD do Unreal; tempo padrao; default/render','coletor':VERSAO,
            'engine':r.get('engine'),'openusd':r.get('openusd')}
    vid=A.identidade(oid,assinatura_completa,r.get('engine'),r.get('openusd'))
    evidencia=A.identidade('inspecao_fonte',vid,r)
    with A.abrir(db,escrita=True) as c:
        c.execute('INSERT OR IGNORE INTO variantes VALUES(?,?,?,?,?)',(vid,oid,assinatura_completa,A.dump(config),A.agora()))
        A.registro(c,'evidencia_preparacao',evidencia,r,'coletor_usd_v'+VERSAO)
        for nome in ('caixa_stage_cm','up_axis','metros_por_unidade','meshes','dependencias_ausentes'):
            if nome in r:_metadado(c,vid,'geometria',nome,r[nome],
                                   'declaracao_fonte' if nome in ('up_axis','metros_por_unidade') else 'medida','OpenUSD',evidencia,
                                   'cm' if nome=='caixa_stage_cm' else None,r.get('caixa_escopo'))
        for j in r.get('partes',[])+r.get('juntas',[]):
            c.execute('INSERT OR REPLACE INTO partes_modelo VALUES(?,?,?,?,?)',
                (vid,j['path'],j.get('pai'),j['tipo'],A.dump({**j,'origem_tipo':'declaracao_fonte','limite':'nao comprova montagem no Unreal ou junta Chaos'})))
        if r.get('transformacoes_referencial'):
            _metadado(c,vid,'partes','transformacoes_referencial',r['transformacoes_referencial'],
                      'configuracao','OpenUSD',evidencia)
        # Nao certifica fisica. Somente teste objetivo de dependencias da fonte.
        resultado='reprovado' if r.get('dependencias_ausentes') else 'aprovado'
        cap=A.identidade(vid,'dependencias_fonte',evidencia)
        c.execute('INSERT OR IGNORE INTO capacidades_modelo VALUES(?,?,?,?,?,?,?,?)',
            (cap,vid,'dependencias_fonte',resultado,A.dump({'tempo':'padrao','formato':'USD'}),'OpenUSD',evidencia,A.agora()))
    return vid


def preparar(p,db=None):
    _campos(p,('acao','objeto','origem','pedido_id','sessao','autorizar_download','importar'))
    oid=_texto(p.get('objeto'),'objeto',64);_texto(p.get('origem'),'origem')
    for k in ('pedido_id','sessao'):
        if k in p:_texto(p[k],k,200)
    if 'importar' in p and not isinstance(p['importar'],bool):raise ValueError('importar deve ser booleano')
    if p.get('autorizar_download') is not True:raise ValueError('preparar requer autorizar_download:true e origem da autorizacao existente')
    # Limite vem do operador/configuracao, nunca e ampliado pelo pedido da LLM.
    limite=int(os.environ.get('DIRECTOR_ACERVO_MAX_BYTES',LIMITE_PADRAO))
    if not 1<=limite<=512*1024*1024:raise ValueError('limite do operador deve ser 1..512 MiB')
    with trava_escopo(db,A.identidade('preparar',oid)):
        plano=O.planejar_download(oid,db)
        if plano['licenca'].lower() not in ('apache-2.0','apache-2.0 declarada','apache2','apache-2.0 (declarada)'):
            raise ValueError('licenca nao reconhecida para preparo automatico; revisar fonte')
        if plano['bytes']>limite:raise ValueError('lote acima do limite do operador; nao baixar, pedir revisao do limite')
        jid=A.identidade('preparar',oid,plano,p.get('pedido_id','avulso'),_assinatura([]))
        with A.abrir(db) as c:
            existe=c.execute("SELECT 1 FROM sqlite_master WHERE name='preparacoes'").fetchone()
            old=c.execute('SELECT * FROM preparacoes WHERE id=?',(jid,)).fetchone() if existe else None
            incerto=c.execute("SELECT id,dados_json FROM preparacoes WHERE objeto=? AND etapa='importando' LIMIT 1",(oid,)).fetchone() if existe else None
        dados=json.loads(old['dados_json']) if old else {}
        # Queda depois do inicio da importacao e ambigua: verificar assets existentes.
        if incerto:
            return {'ok':False,'preparacao':incerto['id'],'estado':'requer_conferencia','destino':json.loads(incerto['dados_json']).get('destino'),
                    'proxima_acao':'conferir pasta nativa e registro antes de repetir; importacao pode ter ocorrido'}
        try:
            _persistir(db,jid,oid,p,'baixando','em_andamento',dados)
            baixado=O.baixar({'objeto':oid,'autorizar_download':True,'origem':p['origem'],'max_bytes':limite},db)
            sig=_assinatura(baixado['arquivos'])
            dados['download']={'bytes':baixado['bytes'],'reutilizados':sum(f['reutilizado'] for f in baixado['arquivos'])}
            with A.abrir(db) as c:
                variantes=c.execute('SELECT id,configuracao_json FROM variantes WHERE objeto=? ORDER BY criado_em DESC',(oid,)).fetchall()
            v=next((v for v in variantes if json.loads(v['configuracao_json']).get('assinatura_base')==sig
                and _vigencia(json.loads(v['configuracao_json']),A.identidade(plano))[0]=='vigente'),None)
            if v:
                vid=v['id'];dados['inspecao_reutilizada']=True
            else:
                _persistir(db,jid,oid,p,'inspecionando','em_andamento',dados)
                r=O.inspecionar_usd({'objeto':oid,'arquivo':baixado['principal']},db)
                if _assinatura(baixado['arquivos'])!=sig:raise ValueError('arquivos mudaram durante inspecao')
                vid=_registrar(db,oid,baixado,r,sig);dados['inspecao_reutilizada']=False
            dados['variante']=vid
            ficha_atual=ficha({'objeto':oid,'assunto':'resumo'},db)
            if ficha_atual['bloqueios']:
                _persistir(db,jid,oid,p,'inspecionado','bloqueado',dados,variante=vid)
                return {'preparacao':jid,**ficha_atual,'ok':False,'proxima_acao':'resolver dependencias; nao importar nem inventar medidas'}
            if p.get('importar'):
                with A.abrir(db) as c:
                    anteriores=c.execute('SELECT etapa,dados_json FROM preparacoes WHERE variante=? ORDER BY atualizado_em DESC',(vid,)).fetchall()
                for anterior in anteriores:
                    if anterior['etapa']=='importando':raise ValueError('importacao anterior incompleta; conferir pasta antes de repetir')
                    registro=json.loads(anterior['dados_json'])
                    if registro.get('importacao'):
                        dados['importacao']=registro['importacao'];break
                if dados.get('importacao'):
                    conferencia=O.conferir_importacao(dados['importacao'])
                    if not conferencia['ok']:raise ValueError('assets alterados; revisar sem sobrescrever: '+A.dump(conferencia))
                    dados['conferencia_importacao']=conferencia
            if p.get('importar') and not dados.get('importacao'):
                # Checkpoint antes da mutacao; nunca reaplica cegamente apos falha SQL/ponte.
                dados['destino']='/Game/Director/Acervo/Preparado_'+vid[:24]
                _persistir(db,jid,oid,p,'importando','em_andamento',dados,variante=vid)
                resultado=O.importar({'objeto':oid,'arquivo':baixado['principal'],'modo_usd':'malhas',
                    'destino':dados['destino'],'origem':p['origem']},db)
                if not resultado.get('ok'):raise ValueError('importacao retornou falha; conferir assets: '+A.dump(resultado))
                dados['importacao']=resultado
            _persistir(db,jid,oid,p,'concluido','concluido',dados,variante=vid)
            return {'ok':True,'preparacao':jid,'download':dados['download'],
                    'inspecao_reutilizada':dados['inspecao_reutilizada'],**ficha({'objeto':oid},db)}
        except Exception as exc:
            # Preserva checkpoint importando inclusive se SQL falhar depois do motor.
            with A.abrir(db) as c:atual=c.execute('SELECT etapa FROM preparacoes WHERE id=?',(jid,)).fetchone()
            etapa=atual['etapa'] if atual else 'inicio'
            _persistir(db,jid,oid,p,etapa,'erro',dados,str(exc),dados.get('variante'))
            return {'ok':False,'preparacao':jid,'etapa':etapa,'erro':str(exc),
                    'proxima_acao':'conferir assets antes de repetir' if etapa=='importando' else 'corrigir causa e repetir preparar; arquivos validos serao reutilizados'}


def ficha(p,db=None):
    _campos(p,('acao','objeto','assunto','parte','limite_partes'));oid=p.get('objeto');assunto=p.get('assunto','resumo')
    if assunto not in ASSUNTOS:raise ValueError('assunto deve ser '+', '.join(sorted(ASSUNTOS)))
    if ('parte' in p or 'limite_partes' in p) and assunto!='partes':raise ValueError('parte/limite_partes requer assunto:partes')
    if 'parte' in p:_texto(p['parte'],'parte',1000)
    limite=p.get('limite_partes',12)
    if type(limite) is not int or not 1<=limite<=50:raise ValueError('limite_partes deve ser 1..50')
    with A.abrir(db) as c:
        _conhecido(c,oid)
        obj=dict(c.execute('SELECT o.id,o.nome,o.fonte,f.licenca FROM objetos o JOIN fontes f ON f.id=o.fonte WHERE o.id=?',(oid,)).fetchone())
        out={'ok':True,'objeto':obj,'variante':None,'validade':'nao_inspecionado','geometria':None,
             'fisica':'nao_testada','bloqueios':[],
             'proxima_acao':'preparar candidato antes de escolher por dimensao/fisica'}
        existe=c.execute("SELECT 1 FROM sqlite_master WHERE name='variantes'").fetchone()
        variantes=c.execute('SELECT * FROM variantes WHERE objeto=? ORDER BY criado_em DESC,rowid DESC',(oid,)).fetchall() if existe else []
        v=variantes[0] if variantes else None
        # Legado permanece visivel, inclusive falhas antigas; nenhuma das ultimas tres oculta outra capacidade.
        out['verificacoes_legadas']=[dict(r) for r in c.execute('''SELECT capacidade,resultado,versao,criado_em FROM verificacoes v
            WHERE objeto=? AND id=(SELECT max(id) FROM verificacoes x WHERE x.objeto=v.objeto AND x.capacidade=v.capacidade)
            ORDER BY capacidade''',(oid,))]
        if out['verificacoes_legadas']:out['limite_legado']='evidencias anteriores sem vinculo de variante; vigencia nao demonstrada'
        if assunto=='anotacoes':
            out['anotacoes']=[{**dict(r),'texto':r['texto'][:1000],'truncado':len(r['texto'])>1000,'validado':False}
                for r in c.execute('SELECT id,texto,origem,criado_em FROM anotacoes_acervo WHERE objeto=? ORDER BY id DESC LIMIT 5',(oid,))] if existe else []
            out['limite_anotacoes']='cinco ultimas; propostas nao validadas, texto limitado a 1000 caracteres'
        if not v:return out
        db_real=db
        try:catalogo=A.identidade(O.planejar_download(oid,db_real))
        except (ValueError,KeyError):catalogo='catalogo_indisponivel'
        for candidato in variantes:
            if _vigencia(json.loads(candidato['configuracao_json']),catalogo)[0]=='vigente':v=candidato;break
        config=json.loads(v['configuracao_json']);validade,motivo=_vigencia(config,catalogo)
        out.update(variante=v['id'],validade=validade,proxima_acao='comparar candidato com pedido; importar se necessario')
        out['limite']='medidas da fonte; nao e prova do ator na cena, apoio, rigidez, Chaos ou articulacao'
        if motivo:out['bloqueios'].append(motivo)
        rows=[dict(r) for r in c.execute('SELECT * FROM metadados WHERE variante=?',(v['id'],))]
        valores={r['nome']:json.loads(r['valor_json']) for r in rows}
        deps=valores.get('dependencias_ausentes',[])
        if deps:
            out['bloqueios'].append({'dependencias_ausentes':deps})
            out['proxima_acao']='resolver dependencias ausentes antes de importar; medidas sao apenas da geometria carregada'
        if validade=='vigente':
            out['geometria']={'caixa_stage_cm':valores.get('caixa_stage_cm'),'up_axis':valores.get('up_axis'),
                'origem':'medida OpenUSD','referencial':'AABB mundial, eixos da fonte, tempo padrao; cm'}
        else:out['proxima_acao']='repreparar/revisar arquivo; medidas historicas nao devem orientar escolha atual'
        if assunto=='geometria':out['metadados']=rows # valor historico identificado pela validade acima
        if assunto=='origem':out['origem']=config
        partes=c.execute('SELECT caminho,pai,tipo,dados_json FROM partes_modelo WHERE variante=? ORDER BY caminho',(v['id'],)).fetchall()
        out['juntas_declaradas']=sum('Joint' in r['tipo'] for r in partes)
        out['partes_totais']=len(partes)
        if assunto=='partes':
            selecionadas=[r for r in partes if r['caminho']==p['parte']] if 'parte' in p else partes[:limite]
            if 'parte' in p and not selecionadas:raise ValueError('parte inexistente nesta variante; consulte assunto:partes')
            out['partes']=[]
            for r in selecionadas:
                d=json.loads(r['dados_json']);resumo={k:r[k] for k in ('caminho','pai','tipo')}
                if 'parte' in p:resumo['dados']=d
                else:
                    resumo['caixa_stage_cm']=d.get('caixa_stage_cm')
                    resumo['corpos_declarados']=d.get('relacoes_fisica_declaradas',{})
                out['partes'].append(resumo)
            out['partes_limitadas']='parte' not in p and len(partes)>limite
            out['transformacoes_referencial']=valores.get('transformacoes_referencial','nao coletado')
            out['limite_partes']='matrizes e atributos completos somente com parte:CAMINHO; fonte declarada, nao montagem Unreal/Chaos validada'
        if assunto in ('resumo','fisica'):
            out['capacidades']=[{**dict(r),'validade':validade} for r in c.execute(
                'SELECT capacidade,resultado,escopo_json,metodo,evidencia FROM capacidades_modelo WHERE variante=?',(v['id'],))]
        if assunto in ('superficies','animacoes'):out[assunto]={'estado':'desconhecido','dados':None}
        if assunto=='importacao':
            out['importacoes']=[{'estado':r['estado'],'etapa':r['etapa'],'atualizado_em':r['atualizado_em'],
                'resultado':json.loads(r['dados_json']).get('importacao')} for r in c.execute(
                'SELECT * FROM preparacoes WHERE variante=? ORDER BY atualizado_em DESC LIMIT 3',(v['id'],))]
            out['limite_importacao']='snapshot; consultar inventario nativo antes de reutilizar assets alterados no editor'
        return out


def executar(p,db=None):
    acao=p['acao']
    if acao=='preparar':return preparar(p,db)
    if acao=='ficha':return ficha(p,db)
    if acao=='anotar':
        _campos(p,('acao','objeto','texto','origem'));_texto(p.get('texto'),'texto',4000);_texto(p.get('origem'),'origem')
        with A.abrir(db,escrita=True) as c:
            _conhecido(c,p.get('objeto'))
            cursor=c.execute('INSERT INTO anotacoes_acervo(objeto,texto,origem,criado_em) VALUES(?,?,?,?)',
                (p['objeto'],p['texto'],p['origem'],A.agora()))
            aid=cursor.lastrowid
        return {'ok':True,'anotacao':aid,'validado':False,'proxima_acao':'conferir ficha com assunto:anotacoes',
                'limite':'anotacao; nao altera medidas nem certifica capacidades'}
    if acao=='preparacao':
        _campos(p,('acao','id'));_texto(p.get('id'),'id',64)
        with A.abrir(db) as c:
            r=c.execute('SELECT * FROM preparacoes WHERE id=?',(p['id'],)).fetchone()
            if not r:raise ValueError('preparacao nao encontrada')
            return {'ok':True,'preparacao':dict(r)}
    raise ValueError('acao desconhecida')
