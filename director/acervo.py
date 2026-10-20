"""Acervo SQLite. Consulta offline e coleta explicita; nao baixa modelos nem executa receitas."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import unicodedata
from contextlib import contextmanager

PADRAO = r'R:\CINF\BD\Director\acervo.sqlite3'
SCHEMA = """
CREATE TABLE IF NOT EXISTS fontes(
 id TEXT PRIMARY KEY, url TEXT NOT NULL, licenca TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS objetos(
 id TEXT PRIMARY KEY, fonte TEXT NOT NULL REFERENCES fontes(id), chave TEXT NOT NULL,
 nome TEXT NOT NULL, tipo TEXT NOT NULL, criado_em TEXT NOT NULL,
 UNIQUE(fonte,chave));
CREATE TABLE IF NOT EXISTS registros(
 id INTEGER PRIMARY KEY, entidade TEXT NOT NULL, chave TEXT NOT NULL,
 hash TEXT NOT NULL, origem TEXT NOT NULL, capturado_em TEXT NOT NULL,
 dados_json TEXT NOT NULL, UNIQUE(entidade,chave,hash,origem));
CREATE TABLE IF NOT EXISTS tags(
 objeto TEXT NOT NULL REFERENCES objetos(id), texto TEXT NOT NULL,
 idioma TEXT NOT NULL, procedencia TEXT NOT NULL,
 PRIMARY KEY(objeto,texto,idioma,procedencia));
CREATE TABLE IF NOT EXISTS caracteristicas(
 objeto TEXT NOT NULL REFERENCES objetos(id), nome TEXT NOT NULL,
 valor_json TEXT NOT NULL, procedencia TEXT NOT NULL, evidencia TEXT NOT NULL,
 PRIMARY KEY(objeto,nome,procedencia,evidencia));
CREATE TABLE IF NOT EXISTS arquivos(
 caminho TEXT PRIMARY KEY, objeto TEXT NOT NULL REFERENCES objetos(id),
 sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, formato TEXT NOT NULL,
 presente INTEGER NOT NULL, conferido_em TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS arquivo_hash ON arquivos(sha256);
CREATE TABLE IF NOT EXISTS instalacoes(
 projeto TEXT NOT NULL, caminho TEXT NOT NULL,
 objeto TEXT NOT NULL REFERENCES objetos(id), origem TEXT NOT NULL,
 observado_em TEXT NOT NULL, PRIMARY KEY(projeto,caminho));
CREATE TABLE IF NOT EXISTS instancias(
 id TEXT PRIMARY KEY, projeto TEXT NOT NULL, nivel TEXT NOT NULL,
 ator TEXT NOT NULL, nome TEXT NOT NULL, camada TEXT NOT NULL,
 definicao_json TEXT NOT NULL, origem TEXT NOT NULL, observado_em TEXT NOT NULL,
 UNIQUE(projeto,nivel,ator,camada));
CREATE TABLE IF NOT EXISTS receitas(
 objeto TEXT PRIMARY KEY REFERENCES objetos(id), instancia TEXT NOT NULL REFERENCES instancias(id),
 definicao_json TEXT NOT NULL, dependencias_json TEXT NOT NULL, origem TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS verificacoes(
 id INTEGER PRIMARY KEY, objeto TEXT NOT NULL REFERENCES objetos(id),
 capacidade TEXT NOT NULL, resultado TEXT NOT NULL
 CHECK(resultado IN ('aprovado','reprovado','nao_aplicavel','nao_testado','erro')),
 evidencia TEXT NOT NULL, versao TEXT NOT NULL, criado_em TEXT NOT NULL);
CREATE VIRTUAL TABLE IF NOT EXISTS busca USING fts5(objeto UNINDEXED,texto,
 tokenize='unicode61 remove_diacritics 2');
CREATE TABLE IF NOT EXISTS coletas(
 id TEXT PRIMARY KEY, escopo TEXT NOT NULL, coletor TEXT NOT NULL,
 versao TEXT NOT NULL, inicio TEXT NOT NULL, fim TEXT, estado TEXT NOT NULL, resumo_json TEXT);
CREATE TABLE IF NOT EXISTS itens_coleta(
 escopo TEXT NOT NULL, chave TEXT NOT NULL, objeto TEXT REFERENCES objetos(id),
 assinatura TEXT, versao TEXT NOT NULL, estado TEXT NOT NULL, presente INTEGER NOT NULL,
 dados_json TEXT NOT NULL, atualizado_em TEXT NOT NULL, PRIMARY KEY(escopo,chave));
CREATE TABLE IF NOT EXISTS inspecoes(
 id INTEGER PRIMARY KEY, coleta TEXT NOT NULL REFERENCES coletas(id),
 escopo TEXT NOT NULL, chave TEXT NOT NULL, objeto TEXT REFERENCES objetos(id),
 assinatura TEXT, versao TEXT NOT NULL, estado TEXT NOT NULL, dados_json TEXT NOT NULL, criado_em TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS inspecoes_item ON inspecoes(escopo,chave);
CREATE INDEX IF NOT EXISTS inspecoes_objeto ON inspecoes(objeto,id);
CREATE TABLE IF NOT EXISTS pacotes(
 id TEXT PRIMARY KEY, fonte TEXT NOT NULL REFERENCES fontes(id), chave TEXT NOT NULL,
 nome TEXT NOT NULL, url TEXT, licenca TEXT NOT NULL, dados_json TEXT NOT NULL,
 UNIQUE(fonte,chave));
CREATE TABLE IF NOT EXISTS referencias_pacote(
 objeto TEXT NOT NULL REFERENCES objetos(id), pacote TEXT NOT NULL REFERENCES pacotes(id),
 caminho TEXT NOT NULL, origem TEXT NOT NULL,
 PRIMARY KEY(objeto,pacote,caminho,origem));
CREATE TABLE IF NOT EXISTS catalogos_importados(
 chave TEXT PRIMARY KEY, resultado_json TEXT NOT NULL, importado_em TEXT NOT NULL);
PRAGMA user_version=3;
"""


def agora():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def dump(d):
    return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def identidade(*partes):
    return hashlib.sha256(dump(partes).encode()).hexdigest()


def ler(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


@contextmanager
def abrir(caminho=None, escrita=False):
    # Preserva letra de unidade mapeada: resolve() converte R: em UNC e produz
    # file://servidor/... que SQLite rejeita como authority nao local.
    p=Path(caminho or os.environ.get('DIRECTOR_ACERVO_DB',PADRAO)).absolute()
    if escrita:
        # Sem fallback para C: se o volume definido estiver indisponivel.
        if not p.anchor or not Path(p.anchor).exists():
            raise ValueError('volume do acervo indisponivel; nao usar outro disco automaticamente')
        p.parent.mkdir(parents=True,exist_ok=True)
    elif not p.is_file():
        raise FileNotFoundError('acervo ainda nao inicializado: '+str(p))
    c=sqlite3.connect(str(p) if escrita else p.as_uri()+'?mode=ro',uri=not escrita,timeout=15)
    c.row_factory=sqlite3.Row
    try:
        c.execute('PRAGMA foreign_keys=ON')
        if escrita:
            versao=c.execute('PRAGMA user_version').fetchone()[0]
            if versao not in (0,1,2,3):raise ValueError('versao de acervo nao suportada')
            c.executescript(SCHEMA)
        yield c
        if escrita:c.commit()
    except BaseException:
        if escrita:c.rollback()
        raise
    finally:c.close()


def fonte(c,chave,url='',licenca='nao_confirmada'):
    c.execute('INSERT OR IGNORE INTO fontes VALUES(?,?,?)',(chave,url,licenca))


def registro(c,entidade,chave,dados,origem):
    raw=dump(dados)
    c.execute('INSERT OR IGNORE INTO registros(entidade,chave,hash,origem,capturado_em,dados_json) VALUES(?,?,?,?,?,?)',
              (entidade,chave,hashlib.sha256(raw.encode()).hexdigest(),origem,agora(),raw))


def objeto(c,src,chave,nome,tipo='modelo'):
    oid=identidade(src,chave)
    c.execute('INSERT OR IGNORE INTO objetos VALUES(?,?,?,?,?,?)',(oid,src,chave,nome,tipo,agora()))
    return oid


def tag(c,oid,texto,idioma='indefinido',procedencia='fonte'):
    if texto and texto.strip():c.execute('INSERT OR IGNORE INTO tags VALUES(?,?,?,?)',(oid,texto.strip(),idioma,procedencia))


def caracteristica(c,oid,nome,valor,procedencia,evidencia):
    if valor is not None:
        c.execute('INSERT OR REPLACE INTO caracteristicas VALUES(?,?,?,?,?)',(oid,nome,dump(valor),procedencia,evidencia))


def indexar_busca(c,objetos=None):
    if objetos is not None:
        for oid in set(objetos):
            c.execute('DELETE FROM busca WHERE objeto=?',(oid,))
            c.execute("""INSERT INTO busca(objeto,texto) SELECT o.id,o.nome||' '||coalesce(group_concat(t.texto,' '),'')
                FROM objetos o LEFT JOIN tags t ON t.objeto=o.id WHERE o.id=? GROUP BY o.id""",(oid,))
        return
    c.execute('DELETE FROM busca')
    c.execute("""INSERT INTO busca(objeto,texto)
      SELECT o.id,o.nome||' '||coalesce(group_concat(t.texto,' '),'')
      FROM objetos o LEFT JOIN tags t ON t.objeto=o.id GROUP BY o.id""")


def hssd(c,pedido):
    p=Path(pedido['indice']).resolve();dados=ler(p)
    fonte(c,'hssd','https://huggingface.co/datasets/hssd/hssd-models','CC-BY-NC-4.0')
    total=0
    for synset,entries in dados.items():
        for e in entries:
            oid=objeto(c,'hssd',e['id'],e['name'])
            tag(c,oid,synset,'wordnet');tag(c,oid,e['name'],'en')
            registro(c,'objeto',oid,e,str(p))
            for k in ['up','front','support_region']:
                if e.get(k):caracteristica(c,oid,k,e[k],'fonte_nao_verificada_no_unreal',str(p))
            total+=1
    return {'entradas':total,'modelos_baixados':0}


def arquivo(c,p,nome=None,licenca='nao_confirmada',origem='',sha_esperado=None,objeto_id=None):
    p=Path(p).resolve()
    if not p.is_file():raise FileNotFoundError(p)
    stat=p.stat()
    with p.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
    if sha_esperado and sha_esperado!=sha:raise ValueError('hash divergente: '+str(p))
    depois=p.stat()
    if (stat.st_size,stat.st_mtime_ns)!=(depois.st_size,depois.st_mtime_ns):raise ValueError('arquivo mudou durante leitura')
    antigo=c.execute('SELECT objeto FROM arquivos WHERE sha256=? LIMIT 1',(sha,)).fetchone()
    fonte(c,'local',licenca='consultar_licenca_declarada_por_objeto')
    if objeto_id:
        if not c.execute('SELECT 1 FROM objetos WHERE id=?',(objeto_id,)).fetchone():raise ValueError('objeto remoto nao encontrado')
        if antigo and antigo[0]!=objeto_id:raise ValueError('hash ja associado a outro objeto; revisar identidade antes de vincular')
    oid=objeto_id or (antigo[0] if antigo else objeto(c,'local',sha,nome or p.stem))
    c.execute('INSERT OR REPLACE INTO arquivos VALUES(?,?,?,?,?,?,?)',(str(p),oid,sha,stat.st_size,p.suffix.lower(),1,agora()))
    registro(c,'arquivo',str(p),{'objeto':oid,'sha256':sha,'bytes':stat.st_size,'licenca':licenca},origem)
    caracteristica(c,oid,'licenca_declarada',licenca,'fonte',origem)
    return oid


def asset(c,projeto,caminho,nome=None,origem='',objeto_id=None):
    if not caminho.startswith(('/Game/','/Engine/')):raise ValueError('caminho de asset invalido')
    anterior=c.execute('SELECT objeto FROM instalacoes WHERE projeto=? AND caminho=?',(projeto,caminho)).fetchone()
    if objeto_id:
        if not c.execute('SELECT 1 FROM objetos WHERE id=?',(objeto_id,)).fetchone():raise ValueError('objeto nao encontrado')
        if anterior and anterior[0]!=objeto_id:raise ValueError('instalacao ja associada a outro objeto; revisar vinculo')
    src='unreal:'+projeto;fonte(c,src,licenca='nao_confirmada_por_asset')
    oid=objeto_id or (anterior[0] if anterior else objeto(c,src,caminho,nome or caminho.rsplit('/',1)[-1]))
    c.execute('INSERT OR REPLACE INTO instalacoes VALUES(?,?,?,?,?)',(projeto,caminho,oid,origem,agora()))
    return oid


def instancia(c,projeto,nivel,ator,nome,camada,definicao,origem):
    iid=identidade(projeto,nivel,ator,camada)
    registro(c,'instancia',iid,definicao,origem)
    c.execute('INSERT INTO instancias VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET '
              'nome=excluded.nome,definicao_json=excluded.definicao_json,origem=excluded.origem,observado_em=excluded.observado_em',
              (iid,projeto,nivel,ator,nome,camada,dump(definicao),origem,agora()))
    return iid


def indice_local(c,pedido):
    p=Path(pedido['indice']).resolve();dados=ler(p);projeto=str(Path(pedido['projeto']).resolve())
    nivel=dados.get('level','');cont={'arquivos':0,'assets':0,'instancias':0};erros=[]
    for e in dados['itens']:
        origem=e.get('origem');oid=None
        if origem=='offline':
            try:oid=arquivo(c,e['caminho'],e['nome'],e.get('licenca','nao_confirmada'),str(p),e.get('sha256'))
            except (OSError,ValueError) as exc:
                erros.append({'caminho':e['caminho'],'erro':str(exc)});continue
            cont['arquivos']+=1
        elif origem=='projeto':
            oid=asset(c,projeto,e['caminho'],e['nome'],str(p));cont['assets']+=1
        elif origem=='cena':
            instancia(c,projeto,nivel,e['id'],e['nome'],'snapshot',e,str(p));cont['instancias']+=1
            # Atores nao se tornam automaticamente modelos pesquisaveis.
            for a in e.get('assets',[]):
                if isinstance(a,str) and a.startswith(('/Game/','/Engine/')):asset(c,projeto,a,origem=str(p))
        if oid:
            registro(c,'objeto',oid,e,str(p))
            for t in e.get('categoria',[])+e.get('sinonimos',[]):tag(c,oid,t,procedencia='indice_local_sugerido')
            for k in ['dimensoes_cm','fisica','triangulos','materiais','backend']:
                caracteristica(c,oid,k,e.get(k),'indice_anterior_nao_revalidado',str(p))
    return {**cont,'erros':erros,'limite':'snapshot historico; nao certifica instalacao atual nem fisica'}


def plantas(c,pedido):
    raiz=Path(pedido['pasta']).resolve();projeto=str(Path(pedido['projeto']).resolve());total=0
    for p in sorted(raiz.glob('*/planta.json')):
        b=p.read_bytes();d=json.loads(b.decode('utf-8-sig'))
        if p.read_bytes()!=b:raise ValueError('planta alterada durante a leitura: '+str(p))
        for ator,o in d['objetos'].items():
            instancia(c,projeto,d['nivel'],ator,ator,'planta_planejada',o,str(p));total+=1
    return {'instancias_planejadas':total,'limite':'planta nao e confirmacao do estado real; nao promove objetos automaticamente'}


def varrer(c,pedido):
    raiz=Path(pedido['pasta']).resolve();lim=int(pedido.get('limite',200))
    if not raiz.is_dir() or not 1<=lim<=1000:raise ValueError('pasta/limite invalido (1..1000)')
    total=0;erros=[]
    # Escopo explicito, sem entrar em links/reparse points nem varrer outros volumes.
    for pasta,dirs,files in os.walk(raiz,followlinks=False):
        dirs[:]=sorted(d for d in dirs if not Path(pasta,d).is_symlink()
                       and not (getattr(Path(pasta,d).stat(),'st_file_attributes',0)&0x400))
        for nome in sorted(files):
            p=Path(pasta,nome)
            if p.suffix.lower() not in ('.glb','.gltf','.fbx','.obj','.usd','.usda','.usdc','.blend') or p.is_symlink():continue
            if total>=lim:return {'arquivos':total,'limitado':True,'erros':erros}
            try:arquivo(c,p,licenca=pedido.get('licenca','nao_confirmada'),origem='varredura:'+str(raiz));total+=1
            except (OSError,ValueError) as exc:erros.append({'caminho':str(p),'erro':str(exc)})
    return {'arquivos':total,'limitado':False,'erros':erros,'limite':'hash e presenca; nao inspeciona malha ou dependencias'}


def promover(c,pedido):
    r=c.execute('SELECT * FROM instancias WHERE id=?',(pedido['instancia'],)).fetchone()
    if not r:raise ValueError('instancia nao encontrada')
    if not pedido.get('origem') or not pedido.get('nome'):raise ValueError('nome e origem obrigatorios')
    fonte(c,'criacao_director',licenca='nao_confirmada_dependencias')
    oid=objeto(c,'criacao_director',pedido.get('chave',r['id']),pedido['nome'],'receita')
    # Dependencias incluem o contexto completo da planta, sem executar nenhuma operacao.
    dependencias={'contexto':r['origem'],'camada':r['camada'],'definicao':json.loads(r['definicao_json'])}
    if r['camada']=='planta_planejada':
        pl=ler(r['origem']);pendentes=[r['ator']];objetos={}
        if pl['objetos'].get(r['ator'])!=json.loads(r['definicao_json']):
            raise ValueError('planta mudou; sincronize antes de promover')
        while pendentes:
            chave=pendentes.pop()
            if chave in objetos:continue
            if chave not in pl['objetos']:raise ValueError('dependencia ausente: '+chave)
            o=pl['objetos'][chave];objetos[chave]=o
            for campo in ['sobre','sala']:
                if o.get(campo):pendentes.append(o[campo])
        dependencias['objetos_contexto']=objetos
    payload={'instancia':r['id'],'definicao':json.loads(r['definicao_json']),'dependencias':dependencias,'origem':pedido['origem']}
    registro(c,'receita',oid,payload,pedido['origem'])
    c.execute('INSERT OR REPLACE INTO receitas VALUES(?,?,?,?,?)',(oid,r['id'],r['definicao_json'],dump(dependencias),pedido['origem']))
    for t in pedido.get('tags',[]):tag(c,oid,t,procedencia='usuario_ou_agente:'+pedido['origem'])
    return {'objeto':oid,'estado':'receita_candidata_nao_testada','limite':'preserva definicao/contexto; nao exporta malha nem torna a receita portavel/executavel automaticamente'}


def buscar(c,pedido):
    if __package__:
        from .catalogo import _aliases,PALAVRAS_COMUNS
    else:
        # Distribuicao congelada em R:, sem depender do checkout de desenvolvimento.
        vocab=ler(Path(__file__).with_name('vocabulario.json'))
        PALAVRAS_COMUNS=set(vocab['palavras_comuns'])
        def _aliases(texto):
            def words(s):
                n=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
                return set(re.findall('[a-z]+',n))
            w=words(texto);matches=[]
            for cat,terms in vocab['sinonimos'].items():
                for term in [cat,*terms]:
                    if words(term)<=w:matches.append((cat,words(term)))
            cats=[cat for cat in vocab['sinonimos'] if any(c==cat and not any(p<outro and c2!=cat for c2,outro in matches) for c,p in matches)]
            return cats,[t for cat in cats for t in [cat,*vocab['sinonimos'][cat]]]
    texto=pedido.get('texto','')
    norm=unicodedata.normalize('NFKD',texto).encode('ascii','ignore').decode().lower()
    termos=set(re.findall('[a-z0-9]+',norm))-PALAVRAS_COMUNS
    if not termos:return {'ok':True,'resultados':[],'motivo':'informe um termo significativo'}
    cats,aliases=_aliases(texto)
    # Preserva sinonimos compostos como frases: 'desk chair' nao prova 'desk'.
    for a in aliases:
        a=unicodedata.normalize('NFKD',a).encode('ascii','ignore').decode().lower()
        frase=' '.join(re.findall('[a-z0-9]+',a))
        if frase:termos.add(frase)
    termos-=PALAVRAS_COMUNS
    if len(termos)>100:raise ValueError('consulta extensa demais')
    limite=int(pedido.get('limite',8))
    if not 1<=limite<=50:raise ValueError('limite deve ser 1..50')
    filtro=pedido.get('disponibilidade')
    if filtro not in (None,'importado_snapshot','baixado','remoto','receita'):raise ValueError('disponibilidade invalida')
    q=' OR '.join('"'+t+'"' for t in sorted(termos))
    rows=c.execute("""SELECT o.*,f.licenca,bm25(busca) AS rank,
       CASE WHEN EXISTS(SELECT 1 FROM instalacoes i WHERE i.objeto=o.id) THEN 'importado_snapshot'
         WHEN EXISTS(SELECT 1 FROM arquivos a WHERE a.objeto=o.id AND presente=1) THEN 'baixado'
         WHEN o.tipo='receita' THEN 'receita' ELSE 'remoto' END AS disponibilidade
       FROM busca JOIN objetos o ON o.id=busca.objeto JOIN fontes f ON f.id=o.fonte
       WHERE busca MATCH ?""",(q,)).fetchall()
    rows=[dict(x) for x in rows if filtro is None or x['disponibilidade']==filtro]
    ordem={'importado_snapshot':0,'baixado':1,'receita':2,'remoto':3}
    rows.sort(key=lambda x:(ordem[x['disponibilidade']],x['rank'],x['id']))
    saida=[]
    for r in rows[:limite]:
        r.pop('rank');r.pop('criado_em')
        r['arquivo_remoto']=f"objects/{r['chave'][0]}/{r['chave']}.glb" if r['fonte']=='hssd' else None
        if r['fonte']=='artvip':
            principal=c.execute("SELECT valor_json FROM caracteristicas WHERE objeto=? AND nome='arquivo_principal' ORDER BY rowid DESC LIMIT 1",(r['id'],)).fetchone()
            r['arquivo_remoto']=json.loads(principal[0]) if principal else None
        if r['fonte']=='code4scene':
            pacote=c.execute('SELECT p.nome,p.url,p.licenca FROM referencias_pacote ref JOIN pacotes p ON p.id=ref.pacote WHERE ref.objeto=? LIMIT 1',(r['id'],)).fetchone()
            r['pacote']=dict(pacote) if pacote else None
        ultima=c.execute('SELECT estado,versao,criado_em FROM inspecoes WHERE objeto=? ORDER BY id DESC LIMIT 1',(r['id'],)).fetchone()
        r['ultima_inspecao']=dict(ultima) if ultima else None
        r['verificacoes']=[dict(v) for v in c.execute(
            'SELECT capacidade,resultado,versao,criado_em FROM verificacoes WHERE objeto=? ORDER BY id DESC LIMIT 3',(r['id'],))]
        r['fisica']='consultar_verificacoes_e_escopo' if r['verificacoes'] else 'nao_certificada';saida.append(r)
    return {'ok':True,'resultados':saida,'total':len(rows),'limitado':len(rows)>limite,
            'limite':'disponibilidade por ultima observacao; licenca/caracteristicas nao equivalem a funcionamento testado'}


def detalhe(c,oid):
    r=c.execute('SELECT o.*,f.licenca FROM objetos o JOIN fontes f ON f.id=o.fonte WHERE o.id=?',(oid,)).fetchone()
    if not r:raise ValueError('objeto nao encontrado')
    dados=dict(r)
    for nome in ['tags','caracteristicas','arquivos','instalacoes','verificacoes','receitas']:
        dados[nome]=[dict(x) for x in c.execute('SELECT * FROM '+nome+' WHERE objeto=?',(oid,))]
    return {'ok':True,'objeto':dados}


def resumo(c):
    tabelas=['objetos','fontes','arquivos','instalacoes','instancias','receitas','tags','verificacoes','registros']
    return {'ok':True,'contagens':{t:c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tabelas},
            'integridade':c.execute('PRAGMA quick_check').fetchone()[0],
            'por_fonte':[dict(x) for x in c.execute('SELECT fonte,count(*) total FROM objetos GROUP BY fonte')]}


def executar(pedido,caminho=None):
    acao=pedido.get('acao','resumo');leitura=acao in ('resumo','buscar','detalhe','instancias')
    if acao in ('planejar_download','baixar','importar','sincronizar','rotular','inspecionar_usd'):
        from . import acervo_operacao
        return acervo_operacao.executar(pedido,caminho)
    with abrir(caminho,escrita=not leitura) as c:
        if acao=='resumo':return resumo(c)
        if acao=='buscar':return buscar(c,pedido)
        if acao=='detalhe':return detalhe(c,pedido['objeto'])
        if acao=='instancias':
            rows=c.execute('SELECT id,nome,projeto,nivel,camada,observado_em FROM instancias WHERE nivel=? ORDER BY nome LIMIT 50',(pedido['nivel'],)).fetchall()
            return {'ok':True,'instancias':[dict(r) for r in rows],'limite':50}
        if acao=='iniciar':return resumo(c)
        funcs={'hssd':hssd,'indice':indice_local,'plantas':plantas,'varrer':varrer,'promover':promover}
        if acao in funcs:r=funcs[acao](c,pedido)
        elif acao=='instalacao':
            if not pedido.get('origem'):raise ValueError('origem obrigatoria')
            oid=asset(c,str(Path(pedido['projeto']).resolve()),pedido['caminho'],origem=pedido['origem'],objeto_id=pedido['objeto'])
            r={'objeto':oid,'limite':'vinculo declarado; ainda depende de verificacao no Unreal'}
        elif acao=='arquivo':
            if not pedido.get('origem'):raise ValueError('origem obrigatoria')
            oid=arquivo(c,pedido['caminho'],pedido.get('nome'),pedido.get('licenca','nao_confirmada'),
                        pedido['origem'],pedido.get('sha256'),pedido.get('objeto'))
            r={'objeto':oid,'limite':'registrado e hasheado; nao importado nem testado no Unreal'}
        elif acao=='tags':
            if not pedido.get('origem'):raise ValueError('origem obrigatoria')
            for t in pedido['tags']:tag(c,pedido['objeto'],t['texto'],t['idioma'],pedido['origem'])
            r={'tags':len(pedido['tags'])}
        elif acao=='verificacao':
            for k in ['evidencia','versao','capacidade']:
                if not pedido.get(k):raise ValueError(k+' obrigatorio')
            c.execute('INSERT INTO verificacoes(objeto,capacidade,resultado,evidencia,versao,criado_em) VALUES(?,?,?,?,?,?)',
                      (pedido['objeto'],pedido['capacidade'],pedido['resultado'],pedido['evidencia'],pedido['versao'],agora()))
            r={'registrado':True}
        else:raise ValueError('acao desconhecida')
        indexar_busca(c)
        return {'ok':not bool(r.get('erros')),**r}


def cli(args):
    if len(args)==2 and args[0]=='fontes':
        if __package__:
            from . import acervo_fontes
        else:
            import acervo_fontes
        return acervo_fontes.importar(ler(args[1]))
    if len(args)==2 and args[0]=='coletar':
        if __package__:
            from . import acervo_coleta
        else:
            import acervo_coleta
        return acervo_coleta.executar(ler(args[1]))
    if len(args)==1 and args[0] in ('iniciar','resumo'):return executar({'acao':args[0]})
    if args and args[0]=='buscar':return executar({'acao':'buscar','texto':' '.join(args[1:])})
    if len(args)==2 and args[0]=='pedido':
        import sys
        pedido=json.load(sys.stdin) if args[1]=='-' else ler(args[1])
        return executar(pedido)
    raise ValueError('uso: acervo iniciar | resumo | buscar TERMO | pedido JSON|- | coletar JSON | fontes JSON')


if __name__=='__main__':
    import sys
    try:
        r=cli(sys.argv[1:]);print(json.dumps(r,ensure_ascii=True));sys.exit(0 if r.get('ok') else 2)
    except Exception as exc:
        print(json.dumps({'ok':False,'porque':str(exc)},ensure_ascii=True));sys.exit(2)
