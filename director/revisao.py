"""Revisao limitada sobre executor existente; notas subjetivas nunca anulam medidas."""
import copy,hashlib,json,math,os
from pathlib import Path
from . import config as C,verificacao as V
from .veredito import de_verificacao
from .nucleo import planta as PL,pecas as P,plano as PN,derivar as D,operacoes as O,executor as X

ITENS=('realismo','funcao','arrumacao','completude','seguiu_pedido','passagem')
COMPLETUDE={'quarto':('porta','janela'),'sala':('porta',),'cozinha':('porta','ventilacao'),'banheiro':('porta','ventilacao')}


def perguntas(planta,tipos,dispensados=()):
    """Convencoes pequenas e explicitas; nao criam conteudo nao pedido."""
    resultado=[]
    for sid,tipo in tipos.items():
        if sid not in planta['objetos'] or planta['objetos'][sid]['tipo']!='sala':raise ValueError('sala inexistente: '+sid)
        presentes={o['tipo'] for o in planta['objetos'].values() if o.get('sala')==sid}
        for item in COMPLETUDE.get(tipo,()):
            atendido=(bool(presentes & {'porta','passagem'}) if item=='porta' else item in presentes)
            if item=='ventilacao':atendido='janela' in presentes
            chave=sid+'.'+item
            if not atendido and chave not in dispensados:
                resultado.append({'id':chave,'sala':sid,'falta':item,'acao':'perguntar',
                    'opcoes':['incluir e verificar','dispensar explicitamente'],
                    'limite':'convencao de completude; nao certifica uso, iluminacao ou ventilacao real'})
    return resultado


def pontuar(notas,medidas,pendencias):
    if not isinstance(notas,dict) or set(notas)!=set(ITENS):raise ValueError('informe as seis notas e justificativas')
    resultado=copy.deepcopy(notas)
    for item,n in resultado.items():
        v=n.get('nota');just=n.get('justificativa')
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=10 or not isinstance(just,str) or not just.strip():
            raise ValueError('nota 0..10 finita e justificativa obrigatorias: '+item)
        n['nota_proposta']=v
    if not medidas.get('aprovado'):
        for item in ('funcao','passagem','seguiu_pedido'):
            resultado[item]['nota']=min(resultado[item]['nota'],3)
            resultado[item]['limite_objetivo']='verificacao geometrica/fisica reprovada ou incompleta'
    if pendencias:
        resultado['completude']['nota']=min(resultado['completude']['nota'],5)
        resultado['completude']['limite_objetivo']='perguntas de completude pendentes'
    return resultado


def _hash(planta):return hashlib.sha256(json.dumps(planta,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _arquivo(cena):return Path(C.ESTADO_DIR)/'revisoes'/cena/'atual.json'


def _gravar(cena,dados):
    f=_arquivo(cena);f.parent.mkdir(parents=True,exist_ok=True);tmp=f.with_suffix('.tmp')
    tmp.write_text(json.dumps(dados,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');os.replace(tmp,f)


def _conferir_atual(cena,editor,esperada=None):
    p=PL.carregar(C.CENAS,cena)
    if editor.chamar('info')['level']!=p['nivel']:raise ValueError('revisao nao abre outra cena')
    if editor.chamar('info')['em_play']:raise ValueError('pare Play antes de revisar')
    if esperada and _hash(p)!=esperada:raise ValueError('cena mudou fora desta revisao; nada sera desfeito automaticamente')
    inv=editor.chamar('inventory',variaveis=P.variaveis())
    if PN.diferencas(D.derivar(p),inv['controlados']):raise ValueError('planta e editor divergem; confira antes de iniciar/corrigir/recuar')
    return p,inv


def avaliar(cena,pedido,editor,tipos=None):
    origem=pedido.get('origem')
    if not isinstance(origem,str) or not origem.strip():raise ValueError('informe origem da avaliacao (sessao/modelo ou usuario)')
    referencias=referencias_layout(pedido.get('referencias_layout',[]))
    p=PL.carregar(C.CENAS,cena)
    pendencias=perguntas(p,tipos if tipos is not None else pedido.get('tipos',{}),pedido.get('dispensados',[]))
    medidas=V.verificar(cena,pedido.get('verificar',{}),editor)
    notas=pontuar(pedido['notas'],medidas,pendencias)
    return {**de_verificacao(medidas),'ok':True,'cena':cena,'origem':origem,'notas':notas,'soma':sum(n['nota'] for n in notas.values()),
        'perguntas':pendencias,'medidas':medidas,'referencias_layout':referencias,
        'limite':'notas de realismo/arrumacao sao opiniao; sucesso de ferramenta nao e PA'}


def referencias_layout(ids,db=None):
    """Referencia solicitada, compacta e somente leitura; nunca altera notas ou cena."""
    if not isinstance(ids,list) or len(ids)>3 or any(not isinstance(i,str) for i in ids):
        raise ValueError('referencias_layout deve conter ate tres IDs do acervo')
    if not ids:return []
    from . import acervo as A
    resultado=[]
    with A.abrir(db) as c:
        for oid in dict.fromkeys(ids):
            row=c.execute('SELECT o.nome,c.valor_json,c.evidencia FROM objetos o JOIN caracteristicas c '
                'ON o.id=c.objeto WHERE o.id=? AND o.fonte=? AND o.tipo=? AND c.nome=?',
                (oid,'spatiallm-dataset','amostra_layout','estatisticas_layout')).fetchone()
            if row is None:raise ValueError('referencia layout ausente ou tipo incorreto: '+oid)
            s=json.loads(row[1])
            resultado.append({'id':oid,'nome':row[0],'fonte':'SpatialLM Dataset / Manycore Research',
                'revisao_fonte':row[2],'licenca':s['licenca_dados'],
                'amostra':{k:s[k] for k in ('quartos_unicos','criterio_dormitorio','dormitorios','dormitorios_com_janela')},
                'distancia_centro_cama_porta_xy':s['distancia_centro_cama_porta_xy'],
                'escopo':s['escopo'],'limite':'referencia estatistica opcional; nao altera notas, nao certifica circulacao e nao obriga janela ou distancia'})
    return resultado


def executar(cena,pedido,editor):
    acao=pedido.get('acao','avaliar')
    if acao=='avaliar':return avaliar(cena,pedido,editor)
    if acao=='estado':
        return {'ok':True,'revisao':json.loads(_arquivo(cena).read_text(encoding='utf-8'))}
    if acao=='iniciar':
        f=_arquivo(cena)
        if f.exists() and json.loads(f.read_text(encoding='utf-8'))['estado']!='encerrada':raise ValueError('ha revisao em andamento; retome-a')
        if not isinstance(pedido.get('pedido'),str) or not pedido['pedido'].strip():raise ValueError('informe pedido humano')
        p,inv=_conferir_atual(cena,editor);r=avaliar(cena,pedido,editor)
        estado={'cena':cena,'pedido':pedido['pedido'],'tipos':pedido.get('tipos',{}),'rodadas':0,
            'dispensados':pedido.get('dispensados',[]),
            'estado':'aguardando_correcao','esperada':_hash(p),'fora':inv['fora'],
            'melhor_planta':p,'melhor_avaliacao':r,'historico':[{'rodada':0,'avaliacao':r}]}
        if not r['perguntas'] and all(n['nota']>=8 for n in r['notas'].values()):estado['estado']='encerrada'
        _gravar(cena,estado);return {'ok':True,'veredito':r['veredito'],'estado':estado['estado'],'avaliacao':r,'rodadas':0}
    estado=json.loads(_arquivo(cena).read_text(encoding='utf-8'))
    if estado['estado']=='encerrada':raise ValueError('revisao encerrada; nao execute outra correcao nela')
    p,inv=_conferir_atual(cena,editor,estado['esperada'])
    if inv['fora']!=estado['fora']:raise ValueError('atores externos mudaram; nao recuar automaticamente')
    if acao=='corrigir':
        if estado['estado']!='aguardando_correcao':raise ValueError('avalie a correcao atual antes de outra')
        if estado['rodadas']>=3:raise ValueError('limite de tres rodadas')
        estado['rodadas']+=1
        estado['estado']='aplicando';_gravar(cena,estado)
        r=X.executar(cena,pedido['ficha'],editor,C.CENAS,C.LAB_DIR,C.WORK+'/restauracao')
        estado['esperada']=_hash(PL.carregar(C.CENAS,cena))
        estado['estado']='aguardando_avaliacao' if r['ok'] else ('encerrada' if estado['rodadas']>=3 else 'aguardando_correcao')
        estado['historico'].append({'rodada':estado['rodadas'],'correcao':r})
        _gravar(cena,estado);return {'ok':r['ok'],'rodadas':estado['rodadas'],'estado':estado['estado'],
            'veredito':'AGUARDANDO_AVALIACAO' if r['ok'] else 'CORRECAO_RECUSADA','correcao':r}
    if acao!='concluir':raise ValueError('acao: avaliar, iniciar, estado, corrigir ou concluir')
    if estado['estado']!='aguardando_avaliacao':raise ValueError('nao ha correcao aguardando avaliacao')
    estado['dispensados']=pedido.get('dispensados',estado.get('dispensados',[]))
    r=avaliar(cena,{**pedido,'dispensados':estado['dispensados']},editor,estado['tipos']);best=estado['melhor_avaliacao']
    piorou=r['soma']<best['soma'] or any(best['notas'][k]['nota']-r['notas'][k]['nota']>=2 for k in ITENS)
    rollback=None;apos_recuo=None
    if piorou:
        alvo=copy.deepcopy(estado['melhor_planta']);O.conferir(alvo)
        rel={'adotados':[],'estrutura_divergente':[]}
        estado['estado']='recuando';_gravar(cena,estado)
        rollback=X._efetivar(editor,C.CENAS,p,alvo,inv,rel,['recuo de rodada que piorou'],C.LAB_DIR,C.WORK+'/restauracao',__import__('time').sleep)
        if not rollback['ok']:raise RuntimeError('recuo falhou; conferir estado antes de continuar: '+str(rollback))
        estado['melhor_planta']=PL.carregar(C.CENAS,cena)
        apos_recuo=V.verificar(cena,pedido.get('verificar',{}),editor)
        if not apos_recuo.get('aprovado'):
            estado['estado']='bloqueada';estado['apos_recuo']=apos_recuo;_gravar(cena,estado)
            raise RuntimeError('inventario recuou, mas verificacao atual reprovou; nao continuar automaticamente')
    else:
        estado['melhor_planta']=p;estado['melhor_avaliacao']=r
    estado['esperada']=_hash(PL.carregar(C.CENAS,cena))
    estado['historico'].append({'rodada':estado['rodadas'],'avaliacao':r,'recuou':piorou,'recuo':rollback})
    melhor=estado['melhor_avaliacao']
    estado['estado']='encerrada' if estado['rodadas']>=3 or (not melhor['perguntas'] and all(n['nota']>=8 for n in melhor['notas'].values())) else 'aguardando_correcao'
    _gravar(cena,estado)
    PL.registrar(C.CENAS,cena,{'evento':'revisao','rodada':estado['rodadas'],'recuou':piorou,'estado':estado['estado']})
    return {**de_verificacao(apos_recuo or r['medidas']),'ok':True,'rodadas':estado['rodadas'],'estado':estado['estado'],'recuou':piorou,
        'recuo':rollback,'avaliacao':r,'melhor_avaliacao':melhor,
        'apos_recuo':apos_recuo,
        'abaixo_do_limite':[k for k,n in melhor['notas'].items() if n['nota']<8]}
