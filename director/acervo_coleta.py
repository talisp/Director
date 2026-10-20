"""Inventario/inspecao incrementais. Sem inferencia, downloads ou alteracao de cena."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import uuid
from contextlib import contextmanager
from importlib.metadata import version,PackageNotFoundError
from urllib.parse import unquote,urlsplit

if __package__:
    from . import acervo as A
else:
    import acervo as A

VERSAO='1.0.0'
FORMATOS={'.glb','.gltf','.fbx','.obj','.usd','.usda','.usdc','.blend'}


def hash_arquivo(p):
    antes=p.stat()
    with p.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    depois=p.stat()
    if (antes.st_size,antes.st_mtime_ns)!=(depois.st_size,depois.st_mtime_ns):
        raise ValueError('arquivo mudou durante leitura: '+str(p))
    return sha


def gltf_json(p):
    if p.suffix.lower()=='.gltf':
        if p.stat().st_size>32*1024*1024:raise ValueError('JSON glTF acima de 32 MiB')
        d=A.ler(p)
    else:
        with p.open('rb') as f:
            h=f.read(12)
            if len(h)!=12:raise ValueError('GLB truncado')
            magic,v,tamanho=struct.unpack('<4sII',h)
            if magic!=b'glTF' or v!=2 or tamanho!=p.stat().st_size:raise ValueError('cabecalho GLB invalido')
            chunk=f.read(8)
            if len(chunk)!=8:raise ValueError('GLB sem JSON')
            n,tipo=struct.unpack('<I4s',chunk)
            if tipo!=b'JSON' or n>32*1024*1024 or n>tamanho-20:raise ValueError('chunk JSON invalido')
            d=json.loads(f.read(n).decode('utf-8').rstrip(' \x00'))
    if str(d.get('asset',{}).get('version'))!='2.0':raise ValueError('somente glTF 2.0 nesta versao')
    return d


def assinatura_arquivo(p,raiz):
    deps=[]
    if p.suffix.lower() in ('.glb','.gltf'):
        d=gltf_json(p)
        for e in d.get('buffers',[])+d.get('images',[]):
            uri=e.get('uri','')
            if not uri or uri.startswith('data:'):continue
            u=urlsplit(uri)
            if u.scheme or u.netloc or u.query or u.fragment:raise ValueError('dependencia remota/URI nao suportada')
            dep=(p.parent/unquote(u.path)).resolve()
            if not dep.is_relative_to(raiz):raise ValueError('dependencia fora da pasta autorizada')
            if not dep.is_file():raise FileNotFoundError('dependencia ausente: '+str(dep))
            deps.append({'caminho':str(dep),'sha256':hash_arquivo(dep),'bytes':dep.stat().st_size})
    raw={'sha256':hash_arquivo(p),'dependencias':sorted(deps,key=lambda x:x['caminho'])}
    return A.identidade(raw),raw


def inspecionar_gltf(p):
    import trimesh
    d=gltf_json(p);cena=trimesh.load_scene(p,allow_remote=False)
    if cena.bounds is None:raise ValueError('modelo sem geometria')
    return {'estado':'ok','backend':'trimesh '+trimesh.__version__,
            'dimensoes_cm':[float(cena.extents[i])*100 for i in (0,2,1)],
            'caixa_local_gltf_m':cena.bounds.tolist(),'unidades':'glTF metros; dimensoes cm XYZ Z-up; escala artistica nao certificada',
            'malhas':len(cena.geometry),'materiais':len(d.get('materials',[])),
            'esqueletos':[{'nome':s.get('name'),'juntas':len(s.get('joints',[]))} for s in d.get('skins',[])],
            'animacoes':[{'nome':a.get('name'),'canais':len(a.get('channels',[]))} for a in d.get('animations',[])],
            'limites':['bounds iniciais, nao envelope de animacao','colisao/massa/articulacao funcional nao verificadas']}


def worker(p):
    if p.suffix.lower() not in ('.glb','.gltf'):
        return {'estado':'nao_suportado','formato':p.suffix.lower(),'limite':'inventariado; sem inspecao geometrica nesta versao'}
    r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'worker',str(p)],
                     capture_output=True,timeout=60,encoding='utf-8',errors='replace')
    if r.returncode:raise ValueError((r.stderr or r.stdout)[-1800:])
    return json.loads(r.stdout)


def listar_arquivos(raiz):
    encontrados=[];erros=[]
    for pasta,dirs,files in os.walk(raiz,followlinks=False,onerror=lambda e:erros.append(str(e))):
        for d in list(dirs):
            p=Path(pasta,d)
            try:
                if p.is_symlink() or getattr(p.stat(),'st_file_attributes',0)&0x400:dirs.remove(d)
            except OSError as exc:dirs.remove(d);erros.append(str(exc))
        dirs.sort()
        for nome in sorted(files):
            p=Path(pasta,nome)
            if p.suffix.lower() in FORMATOS and not p.is_symlink():encontrados.append(str(p.resolve()))
    return sorted(encontrados),erros


@contextmanager
def trava_escopo(db,escopo):
    # Lock nativo liberado pelo SO inclusive em encerramento abrupto; sem worker/servico.
    base=Path(db or os.environ.get('DIRECTOR_ACERVO_DB',A.PADRAO)).absolute().parent/'travas-coleta'
    base.mkdir(parents=True,exist_ok=True)
    with (base/(escopo+'.lock')).open('a+b') as f:
        if f.tell()==0:f.write(b'0');f.flush()
        f.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:raise ValueError('coleta deste escopo ja esta em andamento') from exc
        try:yield
        finally:
            f.seek(0)
            if os.name=='nt':msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(f.fileno(),fcntl.LOCK_UN)


def rodar(db,escopo,*args,**kwargs):
    with trava_escopo(db,escopo):return _rodar(db,escopo,*args,**kwargs)


def _rodar(db,escopo,coletor,versao,candidatos,assinatura,inspecionar,registrar,
          completo=True,erros_inventario=None,limite=200,forcar=False):
    """Persiste cada item, reaproveita sucesso, retoma falhas sem retry no mesmo lote."""
    if not 1<=limite<=1000:raise ValueError('limite 1..1000')
    rid=uuid.uuid4().hex;vistos=set();n=0;falhas=[]
    cont=dict.fromkeys(['novos','reinspecionados','reutilizados','erros','ausentes','nao_suportados'],0)
    completo=bool(completo and not erros_inventario)
    with A.abrir(db,escrita=True) as c:
        c.execute('INSERT INTO coletas VALUES(?,?,?,?,?,?,?,?)',(rid,escopo,coletor,versao,A.agora(),None,'em_andamento',None));c.commit()
        try:
            for item in candidatos:
                chave=item if isinstance(item,str) else item['chave'];vistos.add(chave)
                antigo=c.execute('SELECT * FROM itens_coleta WHERE escopo=? AND chave=?',(escopo,chave)).fetchone()
                sig=None;oid=None;tentou=False
                try:
                    sig,entrada=assinatura(item)
                    if not forcar and antigo and antigo['presente'] and antigo['assinatura']==sig and antigo['versao']==versao and antigo['estado'] in ('ok','nao_suportado'):
                        cont['reutilizados']+=1;continue
                    if n>=limite:completo=False;break
                    n+=1;tentou=True;d=inspecionar(item)
                    if assinatura(item)[0]!=sig:raise ValueError('entrada mudou durante inspecao')
                    estado=d.get('estado','ok')
                    if estado not in ('ok','nao_suportado'):raise ValueError('retorno do inspetor invalido')
                    dados={'entrada':entrada,'inspecao':d}
                    c.execute('SAVEPOINT item')
                    try:oid=registrar(c,item,entrada,d,rid);c.execute('RELEASE item')
                    except Exception:c.execute('ROLLBACK TO item');c.execute('RELEASE item');raise
                    cont['novos' if antigo is None else 'reinspecionados']+=1
                    if estado=='nao_suportado':cont['nao_suportados']+=1
                except Exception as exc:
                    if not tentou:
                        if n>=limite:completo=False;break
                        n+=1
                    estado='erro';dados={'erro':type(exc).__name__+': '+str(exc)};cont['erros']+=1
                    falhas.append({'chave':chave,**dados});oid=antigo['objeto'] if antigo else None
                c.execute('INSERT OR REPLACE INTO itens_coleta VALUES(?,?,?,?,?,?,?,?,?)',
                          (escopo,chave,oid,sig,versao,estado,1,A.dump(dados),A.agora()))
                c.execute('INSERT INTO inspecoes(coleta,escopo,chave,objeto,assinatura,versao,estado,dados_json,criado_em) VALUES(?,?,?,?,?,?,?,?,?)',
                          (rid,escopo,chave,oid,sig,versao,estado,A.dump(dados),A.agora()));c.commit()
            if completo:
                for r in c.execute('SELECT chave,objeto FROM itens_coleta WHERE escopo=? AND presente=1',(escopo,)).fetchall():
                    if r['chave'] in vistos:continue
                    c.execute('UPDATE itens_coleta SET presente=0,estado=?,atualizado_em=? WHERE escopo=? AND chave=?',('ausente',A.agora(),escopo,r['chave']))
                    if coletor=='arquivos':c.execute('UPDATE arquivos SET presente=0,conferido_em=? WHERE caminho=?',(A.agora(),r['chave']))
                    c.execute('INSERT INTO inspecoes(coleta,escopo,chave,objeto,versao,estado,dados_json,criado_em) VALUES(?,?,?,?,?,?,?,?)',
                              (rid,escopo,r['chave'],r['objeto'],versao,'ausente','{}',A.agora()));cont['ausentes']+=1
            if n:A.indexar_busca(c)
            r={'ok':not(cont['erros'] or erros_inventario),'coleta':rid,'escopo':escopo,'versao':versao,'completo':completo,
               'contagens':cont,'falhas':falhas,'erros_inventario':erros_inventario or []}
            c.execute('UPDATE coletas SET fim=?,estado=?,resumo_json=? WHERE id=?',(A.agora(),'concluida' if r['ok'] and completo else 'parcial',A.dump(r),rid))
            return r
        except BaseException:
            c.rollback();c.execute('UPDATE coletas SET fim=?,estado=? WHERE id=?',(A.agora(),'interrompida',rid));c.commit();raise


def arquivos(pedido,db=None):
    raiz=Path(pedido['pasta']).resolve()
    if not raiz.is_dir():raise ValueError('pasta inexistente; nao marcar registros como ausentes')
    itens,erros=listar_arquivos(raiz)
    def registrar(c,item,entrada,dados,rid):
        oid=A.arquivo(c,item,origem='coleta:'+rid,sha_esperado=entrada['sha256'])
        for k,v in dados.items():A.caracteristica(c,oid,k,v,'inspecao_arquivo',rid)
        return oid
    libs={}
    for lib in ['trimesh','numpy']:
        try:libs[lib]=version(lib)
        except PackageNotFoundError:libs[lib]='nao_instalado'
    versao=VERSAO+':'+A.identidade(hash_arquivo(Path(__file__)),libs,sys.version)[:12]
    return rodar(db,A.identidade('pasta',str(raiz)),'arquivos',versao,itens,
                 lambda p:assinatura_arquivo(Path(p),raiz),lambda p:worker(Path(p)),registrar,
                 erros_inventario=erros,limite=int(pedido.get('limite',200)),forcar=bool(pedido.get('forcar',False)))


def unreal(pedido,db=None,editor=None):
    if __package__:
        from . import config as C
        from .ponte import Ponte
    else:
        # Reutiliza somente a ponte publicada, sem instalar ou modificar seu codigo.
        operador=Path(os.environ.get('DIRECTOR_OPERADOR',str(Path.home()/'Director-publicado')))
        if not (operador/'director/ponte.py').is_file():raise ValueError('informe DIRECTOR_OPERADOR com a instalacao fixa do Director')
        sys.path.insert(0,str(operador))
        from director import config as C
        from director.ponte import Ponte
    if editor is None:
        with Ponte('acervo-coletor') as p:return unreal(pedido,db,p)
    antes=editor.chamar('info')
    if antes['em_play'] or antes['por_salvar']:raise ValueError('Play ou pacotes pendentes; coletor nao salva')
    codigo=Path(__file__).with_name('editor').joinpath('acervo_inspecao.py').read_text(encoding='utf-8')
    pasta=pedido.get('pasta','/Game')
    if pasta!='/Game' and not pasta.startswith('/Game/'):raise ValueError('escopo deve estar em /Game')
    snap=editor.chamar('dev_exec',codigo=codigo+'\nresultado=inventariar('+repr(pasta)+')')['resultado']
    content=Path(C.LAB_DIR)/'Content'
    def sig(item):
        nomes=set();fila=[item['chave']]
        while fila:
            k=fila.pop()
            if k in nomes:continue
            nomes.add(k);fila.extend(snap['grafo'].get(k,[]))
        dados=[]
        for nome in sorted(nomes):
            if not nome.startswith('/Game/'):continue
            base=content/nome[len('/Game/'):];files=[]
            if not base.resolve().is_relative_to(content.resolve()):raise ValueError('pacote fora de Content')
            for ext in ['.uasset','.umap','.uexp','.ubulk']:
                p=base.with_suffix(ext)
                if p.is_file():files.append((str(p),hash_arquivo(p)))
            if not files:raise FileNotFoundError('pacote salvo ausente: '+nome)
            dados.extend(files)
        raw={'pacotes':dados,'motor':snap['motor'],'registro':item};return A.identidade(raw),raw
    def inspecionar(item):
        return editor.chamar('dev_exec',codigo=codigo+'\nresultado=inspecionar('+repr(item['chave'])+','+repr(item['classe'])+')')['resultado']
    def registrar(c,item,entrada,dados,rid):
        oid=A.asset(c,str(Path(C.LAB_UPROJECT).resolve()),item['chave'],item['nome'],'coleta:'+rid)
        A.registro(c,'inspecao_unreal',oid,{'entrada':entrada,'inspecao':dados},'coleta:'+rid)
        for k,v in dados.items():A.caracteristica(c,oid,k,v,'unreal_configurado_nao_simulado',rid)
        return oid
    r=rodar(db,A.identidade('unreal',C.LAB_UPROJECT,pasta),'unreal',VERSAO+':'+hashlib.sha256(codigo.encode()).hexdigest()[:12],
            snap['itens'],sig,inspecionar,registrar,erros_inventario=snap['erros'],
            limite=int(pedido.get('limite',50)),forcar=bool(pedido.get('forcar',False)))
    depois=editor.chamar('info')
    r['preservacao']={'mesmo_level':antes['level']==depois['level'],'sem_play':not depois['em_play'],'mesmas_pendencias':antes['por_salvar']==depois['por_salvar']}
    if not all(r['preservacao'].values()):r['ok']=False
    return r


def executar(pedido,db=None):
    if pedido.get('coletor')=='arquivos':return arquivos(pedido,db)
    if pedido.get('coletor')=='unreal':return unreal(pedido,db)
    raise ValueError('coletor deve ser arquivos ou unreal')


if __name__=='__main__':
    try:
        r=inspecionar_gltf(Path(sys.argv[2])) if len(sys.argv)==3 and sys.argv[1]=='worker' else executar(A.ler(sys.argv[1]))
        print(json.dumps(r,ensure_ascii=True))
    except Exception as exc:
        print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(2)
