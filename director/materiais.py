"""Selecao conservadora de material existente; sem download ou catalogo de servico novo."""
import re,unicodedata
from . import config as C
from .nucleo import executor as X,planta as PL

SINONIMOS={'madeira':{'wood','wooden','timber','madeira'},'azulejo':{'tile','tiles','ceramic','ceramica','azulejo'},
    'branco':{'white','branco','branca'},'clara':{'light','clara','claro'},'metal':{'metal','metallic'},'pintura':{'paint','painted','pintura'}}
IGNORAR={'de','do','da','em','piso','parede','paredes','teto','material'}


def _palavras(s):
    s=re.sub(r'([a-z])([A-Z])',r'\1 \2',s)
    s=''.join(c for c in unicodedata.normalize('NFKD',s.lower()) if not unicodedata.combining(c))
    return set(re.findall('[a-z0-9]+',s))


def candidatos(materiais,descricao):
    termos=_palavras(descricao)-IGNORAR
    if not termos:return []
    grupos=[next((v for k,v in SINONIMOS.items() if t==k or t in v),{t}) for t in termos]
    return sorted([m for m in materiais if all(g & _palavras(m['nome']) for g in grupos)],key=lambda m:m['caminho'])


def executar(cena,pedido,editor):
    p=PL.carregar(C.CENAS,cena)
    if editor.chamar('info')['level']!=p['nivel']:raise ValueError('abra a cena antes de aplicar material')
    from .planejamento import compartilhadas
    efeitos=[]
    for a in compartilhadas(p):
        if pedido['sala'] in a['salas']:
            n=a['salas'].index(pedido['sala'])
            if pedido['alvo'] in ('paredes','parede_'+a['lados'][n]):efeitos.append(a)
    if efeitos and pedido.get('aceitar_compartilhada') is not True:
        return {'ok':False,'motivo':'material_afeta_parede_compartilhada','efeitos':efeitos,'tocou_na_cena':False,
            'proxima_acao':'explique que o mesmo ator muda dos dois lados; aceitar_compartilhada:true somente se essa mudanca estiver autorizada'}
    descricao=pedido['descricao'];path=pedido.get('caminho')
    if not path:
        lista=candidatos(editor.chamar('material_info')['materiais'],descricao)
        if len(lista)!=1:return {'ok':False,'motivo':'material_ausente_ou_ambiguo','candidatos':lista[:8],
            'proxima_acao':'procure no projeto/cache Fab; sem candidato adequado, pedir autorizacao para baixar material licenciado; nao substituir silenciosamente',
            'limite':'busca lexical PT/EN por nome; nao e busca visual nem certificacao semantica','tocou_na_cena':False}
        path=lista[0]['caminho']
    r=editor.chamar('material_info',caminho=path)
    if not r['valido']:return {'ok':False,'motivo':'material_inexistente','tocou_na_cena':False}
    ficha={'pedido':descricao,'operacoes':[{'operacao':'material_sala','id':pedido['sala'],'alvo':pedido['alvo'],'caminho':r['caminho'],'descricao':descricao}]}
    r=X.executar(cena,ficha,editor,C.CENAS,C.LAB_DIR,C.WORK+'/restauracao');r['efeitos_compartilhados']=efeitos
    r['limite_material']='descricao e busca por nome nao comprovam aparencia; conferir visualmente. Colisao e navegacao nao devem mudar'
    return r
