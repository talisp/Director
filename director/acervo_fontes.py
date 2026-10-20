"""Importa referencias externas normalizadas; nao baixa modelos nem compra pacotes."""
import collections
import hashlib
import json
import math
from pathlib import Path,PurePosixPath
import re
import sys
if __package__:
    from . import acervo as A
else:
    import acervo as A

# Identifica o codigo carregado, nao uma versao do arquivo editada durante a rodada.
IMPORTADOR_SHA=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

TRADUCOES={
    'cabinet':['armario','cabinete'],'cupboard':['armario'],'wardrobe':['guarda roupa','roupeiro'],
    'chair':['cadeira'],'table':['mesa'],'desk':['escrivaninha'],'bed':['cama'],
    'sofa':['sofa'],'door':['porta'],'window':['janela'],'drawer':['gaveta'],
    'refrigerator':['geladeira'],'fridge':['geladeira'],'dishwasher':['lava loucas'],
    'microwave':['micro ondas'],'oven':['forno'],'toilet':['vaso sanitario'],
    'faucet':['torneira'],'trash can':['lixeira'],'basket':['cesto'],'lamp':['luminaria'],
}


def yaml_seguro(texto):
    try:import yaml
    except ImportError:
        deps=Path(A.PADRAO).parent/'dependencias'
        if not (deps/'yaml').is_dir():raise ValueError('instale requirements-acervo.txt; nao usar parser YAML improvisado')
        sys.path.insert(0,str(deps));import yaml
    return yaml.safe_load(texto)


def nome_path(p):
    return re.sub(r'[_-]+',' ',p).strip()


def tags(c,oid,nome,categoria=''):
    A.tag(c,oid,nome,'en','nome_da_fonte')
    if categoria:A.tag(c,oid,nome_path(categoria),'en','categoria_da_fonte')
    words=set(re.findall('[a-z]+',(nome+' '+categoria).lower().replace('_',' ')))
    for termo,pts in TRADUCOES.items():
        if set(termo.split())<=words:
            for pt in pts:A.tag(c,oid,pt,'pt','taxonomia_sugerida_nao_validacao_funcional')


def artvip(info):
    """Uma entrada por USD principal; recursos/originais nao viram novos objetos."""
    arquivos=info['siblings'];pastas={}
    for f in arquivos:
        p=PurePosixPath(f['rfilename'])
        if not str(p).startswith('Articulated_objects/') or p.suffix.lower() not in ('.usd','.usda','.usdc'):continue
        if any(x in ('resource','origin','NVIDIA') for x in p.parts):continue
        if str(p.parent) in pastas:raise ValueError('mais de um USD principal na mesma pasta; revisar agrupamento')
        pastas[str(p.parent)]=str(p)
    resultado=[]
    for pasta,principal in sorted(pastas.items()):
        membros=[{'caminho':f['rfilename'],'bytes':f.get('size'),'sha256':f.get('lfs',{}).get('sha256'),
                  'git_blob':f.get('blobId')} for f in arquivos if f['rfilename'].startswith(pasta+'/')]
        resultado.append({'id':pasta,'nome':nome_path(PurePosixPath(pasta).name),'grupo':PurePosixPath(pasta).parts[1],
                          'categoria':' / '.join(PurePosixPath(pasta).parts[1:-1]),
                          'arquivo_principal':principal,'arquivos':membros})
    return resultado


def caminho_unreal(p):
    p=p.strip().rstrip('.,;')
    if not re.fullmatch(r'/Game/[A-Za-z0-9_./-]+',p) or '..' in p.split('/'):raise ValueError('caminho Unreal invalido')
    return p.rsplit('.',1)[0] if '.' in p.rsplit('/',1)[-1] else p


def paleta(prompt):
    itens=[];rejeitadas=[]
    for linha in prompt.splitlines():
        if not linha.lstrip().startswith('- ') or '/Game/' not in linha or '|' not in linha:continue
        partes=[x.strip() for x in linha.lstrip()[2:].split('|')]
        try:
            # Algumas tarefas publicam nome|dimensoes|path, sem id/categoria.
            if len(partes)==3:partes=[partes[0],nome_path(partes[0]),'',partes[1],partes[2]]
            if len(partes)!=5:raise ValueError('paleta deve ter cinco campos')
            nums=partes[3].removesuffix('m').strip().split('x')
            dims=[float(n)*100 for n in nums]
            if len(dims)!=3 or any(not math.isfinite(n) or n<0 for n in dims):raise ValueError('dimensoes invalidas')
            path=caminho_unreal(partes[4]);pack=path.split('/')[2]
            itens.append({'id_paleta':partes[0],'nome':partes[1],'categoria':partes[2],'dimensoes_cm':dims,
                          'caminho':path,'spawn_path':partes[4],'pacote':pack})
        except (ValueError,IndexError) as exc:rejeitadas.append({'linha':linha,'erro':str(exc)})
    return itens,rejeitadas


def importar(pedido,db=None):
    raiz=Path(pedido['pasta']).absolute();manifest=A.ler(raiz/'manifesto.json')
    info=A.ler(raiz/'artvip-info.json');packs=yaml_seguro((raiz/'code4scene-packs.yaml').read_text(encoding='utf-8'))
    tarefas=A.ler(raiz/'code4scene-paletas.json')
    if packs.get('schema')!='code4scene.packs.v1':raise ValueError('schema Code4Scene desconhecido')
    if info.get('sha')!=manifest['artvip_revision']:raise ValueError('revisao ArtVIP divergente')
    if tarefas['revision']!=manifest['code4scene_revision']:raise ValueError('revisao Code4Scene divergente')
    # Conteudo mantido com hash: evita importar metadados alterados como se fossem a fonte original.
    import hashlib
    for nome,sha in manifest['sha256'].items():
        p=(raiz/nome).resolve()
        if not p.is_relative_to(raiz.resolve()):raise ValueError('manifesto fora da pasta')
        if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('hash divergente: '+nome)
    objetos_art=artvip(info);cont=collections.Counter();erros=[]
    with A.abrir(db,escrita=True) as c:
        cache=A.identidade(manifest,IMPORTADOR_SHA)
        anterior=c.execute('SELECT resultado_json FROM catalogos_importados WHERE chave=?',(cache,)).fetchone()
        if anterior:
            r=json.loads(anterior[0]);r['reutilizado']=True;r['coincidencias_locais']=coincidencias(c);return r
        A.fonte(c,'artvip','https://huggingface.co/datasets/x-humanoid-robomind/ArtVIP',info.get('cardData',{}).get('license','nao_confirmada'))
        A.fonte(c,'code4scene','https://github.com/SimWorld-AI/Code4Scene','consultar_pacote_fab')
        for e in objetos_art:
            oid=A.objeto(c,'artvip',e['id'],e['nome']);tags(c,oid,e['nome'],e['categoria'])
            origem='artvip@'+info['sha']
            for k in ['arquivo_principal','arquivos','grupo','categoria']:
                A.caracteristica(c,oid,k,e[k],'catalogo_remoto_nao_inspecionado',origem)
            A.caracteristica(c,oid,'revisao_remota',info['sha'],'fonte',origem)
            A.caracteristica(c,oid,'dependencias','lista da pasta, sem verificacao de referencias USD/MDL externas','fonte_nao_verificada',origem)
            A.caracteristica(c,oid,'articulacao','declarada pelo dataset; juntas nao inspecionadas','fonte_nao_verificada',origem)
            A.registro(c,'catalogo_externo',oid,e,origem);cont['artvip_objetos']+=1
        pacotes={}
        for p in packs['packs']:
            pid=A.identidade('code4scene',p['folder']);pacotes[p['folder']]=pid
            payload={**p,'checked_at':packs.get('checked_at'),'revision':manifest['code4scene_revision'],
                     'limite':'preco/licenca/compatibilidade historicos da fonte, nao verificados no Fab agora'}
            c.execute('INSERT INTO pacotes VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET nome=excluded.nome,url=excluded.url,licenca=excluded.licenca,dados_json=excluded.dados_json',
                      (pid,'code4scene',p['folder'],p.get('title') or p['folder'],p.get('fab_url'),p.get('license') or 'nao_confirmada',A.dump(payload)))
            A.registro(c,'pacote',pid,payload,'code4scene@'+manifest['code4scene_revision']);cont['code4scene_pacotes']+=1
            if not p.get('fab_url'):cont['pacotes_sem_anuncio']+=1
            if p['folder']=='StarterContent':cont['pacotes_nativos']+=1
        objetos=set();casos=0
        for t in tarefas['tarefas']:
            casos+=1
            if not t['itens']:cont['tarefas_sem_paleta']+=1
            for e in t['itens']:
                if e['pacote'] not in pacotes:
                    erros.append({'caso':t['caso'],'pacote':e['pacote'],'erro':'pacote nao consta da lista; referencia nao importada'});continue
                oid=A.objeto(c,'code4scene',e['caminho'],e['nome'],'asset_referenciado');objetos.add(oid)
                tags(c,oid,e['nome'],e['categoria']);origem='code4scene@'+manifest['code4scene_revision']+':'+t['caso']
                c.execute('INSERT OR IGNORE INTO referencias_pacote VALUES(?,?,?,?)',(oid,pacotes[e['pacote']],e['spawn_path'],origem))
                A.caracteristica(c,oid,'dimensoes_declaradas_cm',e['dimensoes_cm'],'paleta_externa_nao_medida_no_unreal',origem)
                A.registro(c,'referencia_paleta',oid,e,origem);cont['code4scene_referencias']+=1
        cont['code4scene_objetos']=len(objetos);cont['code4scene_tarefas']=casos
        cont['linhas_rejeitadas']=sum(len(t.get('rejeitadas',[])) for t in tarefas['tarefas'])
        A.indexar_busca(c)
        # Coincidencia de pasta nao prova compra, licenca ou equivalencia dos arquivos.
        r={'ok':not (erros or cont['linhas_rejeitadas']),'contagens':dict(cont),'erros':erros,'coincidencias_locais':coincidencias(c),
           'modelos_baixados':0,'reutilizado':False,'limites':['ArtVIP catalogado por arquivos principais, sem teste das articulacoes',
           'Code4Scene referencia packs Fab; compra e importacao nao realizadas','Catalogos nao substituem inspeccao no Unreal']}
        if r['ok']:c.execute('INSERT INTO catalogos_importados VALUES(?,?,?)',(cache,A.dump(r),A.agora()))
        return r


def coincidencias(c):
    rows=c.execute("""SELECT p.chave pacote,i.projeto,i.caminho FROM pacotes p JOIN instalacoes i
       ON substr(i.caminho,1,length('/Game/'||p.chave||'/'))='/Game/'||p.chave||'/'""").fetchall()
    return [{**dict(x),'limite':'apenas caminho coincidente; nao prova posse/licenca nem revisao'} for x in rows]


def baixar(raiz):
    """Somente catalogos publicos, com revisoes fixadas e limite por transferencia."""
    import hashlib
    import tarfile
    import urllib.request
    raiz=Path(raiz).absolute()
    if not Path(raiz.anchor).exists():raise ValueError('volume de catalogos indisponivel')
    def get(url,limite):
        req=urllib.request.Request(url,headers={'User-Agent':'Director-catalogo/1.0'})
        with urllib.request.urlopen(req,timeout=40) as r:
            b=r.read(limite+1)
            if len(b)>limite:raise ValueError('catalogo acima do limite de transferencia')
            return b
    commit=json.loads(get('https://api.github.com/repos/SimWorld-AI/Code4Scene/commits/main',1024*1024))['sha']
    hf=json.loads(get('https://huggingface.co/api/datasets/x-humanoid-robomind/ArtVIP?blobs=true',16*1024*1024))
    rev=hf['sha']
    if not re.fullmatch('[a-f0-9]{40}',commit) or not re.fullmatch('[a-f0-9]{40}',rev):raise ValueError('revisao invalida')
    pasta=raiz/(commit[:12]+'-'+rev[:12]+'-catalogo2');pasta.mkdir(parents=True,exist_ok=True)
    if (pasta/'manifesto.json').is_file():
        m=A.ler(pasta/'manifesto.json')
        for nome,sha in m['sha256'].items():
            if hashlib.sha256((pasta/nome).read_bytes()).hexdigest()!=sha:raise ValueError('snapshot local alterado: '+nome)
        return pasta
    info={k:hf.get(k) for k in ['id','sha','gated','cardData','siblings']}
    (pasta/'artvip-info.json').write_text(A.dump(info),encoding='utf-8')
    tarpath=pasta/'code4scene-fonte.tar.gz'
    if not tarpath.exists():
        anterior=raiz/(commit[:12]+'-'+rev[:12])
        if (anterior/'manifesto.json').is_file():
            m=A.ler(anterior/'manifesto.json');arquivo=anterior/'code4scene-fonte.tar.gz'
            if hashlib.sha256(arquivo.read_bytes()).hexdigest()!=m['sha256'].get(arquivo.name):raise ValueError('cache da fonte alterado')
            import shutil
            shutil.copyfile(arquivo,tarpath)
        else:tarpath.write_bytes(get('https://codeload.github.com/SimWorld-AI/Code4Scene/tar.gz/'+commit,80*1024*1024))
    tarefas=[];packs=None
    with tarfile.open(tarpath,'r:gz') as arc:
        for membro in sorted(arc.getmembers(),key=lambda m:m.name):
            if not membro.isfile():continue
            rel=membro.name.split('/',1)[-1]
            selecionado=rel=='benchmark/packs.yaml' or (rel.startswith('benchmark/public/text-to-scene/') and rel.endswith('/task.yaml'))
            if not selecionado:continue
            if membro.size>4*1024*1024:raise ValueError('arquivo de metadados excedeu 4 MiB')
            texto=arc.extractfile(membro).read().decode('utf-8')
            if rel=='benchmark/packs.yaml':packs=texto;continue
            d=yaml_seguro(texto);prompt=d.get('inputs',{}).get('prompt','')
            itens,rejeitadas=paleta(prompt)
            tarefas.append({'caso':rel,'itens':itens,'rejeitadas':rejeitadas,'pacotes':d.get('assets',{}).get('packs',[])})
    if packs is None or not tarefas:raise ValueError('repositorio sem catalogo esperado')
    (pasta/'code4scene-packs.yaml').write_text(packs,encoding='utf-8')
    (pasta/'code4scene-paletas.json').write_text(A.dump({'revision':commit,'tarefas':tarefas}),encoding='utf-8')
    for nome in ['README.md','Articulated_objects/README.md']:
        from urllib.parse import quote
        b=get('https://huggingface.co/datasets/x-humanoid-robomind/ArtVIP/raw/'+rev+'/'+quote(nome,safe='/'),1024*1024)
        (pasta/('artvip-'+nome.replace('/','-'))).write_bytes(b)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pasta.iterdir() if p.is_file()}
    m={'capturado_em':A.agora(),'normalizador':'catalogo2','code4scene_revision':commit,'artvip_revision':rev,'sha256':hashes,
       'limites':['Metadados e fonte do benchmark; nao contem pacotes Fab nem modelos ArtVIP.',
                 'Arquivo-fonte pode conter rubricas do benchmark; nao fornecer ao agente em teste.',
                 'SQL recebe somente referencias de assets, nunca gabaritos ou prompts completos.']}
    (pasta/'manifesto.json').write_text(A.dump(m),encoding='utf-8')
    return pasta


if __name__=='__main__':
    try:
        if len(sys.argv)==3 and sys.argv[1]=='baixar':r={'pasta':str(baixar(sys.argv[2]))}
        elif len(sys.argv)==2:r=importar(A.ler(sys.argv[1]))
        else:raise ValueError('uso: acervo_fontes.py baixar PASTA_R | PEDIDO.json')
        print(json.dumps(r,ensure_ascii=True))
    except Exception as exc:
        print(json.dumps({'ok':False,'erro':str(exc)},ensure_ascii=True));sys.exit(2)
