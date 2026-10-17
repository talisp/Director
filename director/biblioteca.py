"""Adaptador local para inspecao pronta (trimesh/Blender); sem banco ou downloader."""
import hashlib,json,subprocess,sys,tempfile,time
from pathlib import Path
from . import config as C,catalogo


def inspecionar(arquivo,blender=None):
    p=Path(arquivo).resolve()
    if not p.is_file():raise FileNotFoundError(p)
    if p.suffix.lower()=='.fbx':
        if not blender:raise ValueError('informe executavel blender para FBX')
        with tempfile.TemporaryDirectory(dir=Path(C.WORK)) as tmp:
            out=Path(tmp)/'resultado.json'
            proc=subprocess.run([blender,'--background','--factory-startup','--python',str(Path(__file__).with_name('offline_blender.py')),'--',str(p),str(out)],capture_output=True,timeout=120)
            if proc.returncode or not out.is_file():raise RuntimeError(proc.stdout.decode(errors='replace')[-1000:]+proc.stderr.decode(errors='replace')[-1000:])
            return json.loads(out.read_text(encoding='utf-8'))
    if p.suffix.lower() not in ('.glb','.gltf'):raise ValueError('prova pequena suporta GLB/GLTF e FBX; outros formatos ainda nao testados')
    import trimesh
    cena=trimesh.load_scene(p,allow_remote=False)
    if cena.bounds is None:raise ValueError('modelo sem geometria')
    ext=cena.extents;cent=cena.bounds.mean(axis=0)
    materiais=[getattr(g.visual,'material',None) for g in cena.geometry.values()]
    return {'dimensoes_cm':[float(ext[i])*100 for i in (0,2,1)],'centro_cm':[float(cent[0])*100,-float(cent[2])*100,float(cent[1])*100],
        'triangulos':sum(len(cena.geometry[cena.graph[n][1]].faces) for n in cena.graph.nodes_geometry),
        'materiais':len({id(x) for x in materiais if x is not None}),
        'unidades':'glTF metros convertidos para cm, XYZ de saida com Z para cima; conferir escala artistica',
        'backend':'trimesh '+trimesh.__version__,'dependencias':'leitura local pelo loader; completude de dependencias nao certificada'}


def indexar(pedido):
    t0=time.monotonic();itens=[];erros=[]
    base=Path(C.WORK)/'biblioteca';base.mkdir(parents=True,exist_ok=True)
    for f in pedido['fontes']:
        for arquivo in f['arquivos']:
            p=Path(arquivo).resolve()
            try:
                d=inspecionar(p,pedido.get('blender'))
                with p.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
                cats,alias=catalogo._aliases(f.get('nome',p.stem))
                itens.append({'nome':f.get('nome',p.stem),'caminho':str(p),'origem':'offline','estado':'baixado_nao_importado',
                    'categoria':cats,'sinonimos':alias,'licenca':f.get('licenca','nao_confirmada'),
                    'proveniencia':f.get('proveniencia'),'preview':f.get('preview'),'bytes':p.stat().st_size,'sha256':sha,
                    'fisica':'nao configurada no Unreal','descricao':'candidato local; conferir forma, escala e adequacao funcional',**d})
            except Exception as e:erros.append({'arquivo':str(p),'erro':str(e)})
    destino=base/'indice.json'
    if destino.is_file() and not pedido.get('substituir',False):
        antigos=json.loads(destino.read_text(encoding='utf-8'))['itens']
        por_path={x['caminho']:x for x in antigos+itens};itens=list(por_path.values())
    total={'itens':itens,'erros':erros,'segundos':round(time.monotonic()-t0,3),'banco':'nao decidido; JSON de prova pequena'}
    if not erros:destino.write_text(json.dumps(total,ensure_ascii=True,indent=2),encoding='utf-8')
    else:(base/'falhas.json').write_text(json.dumps(total,ensure_ascii=True,indent=2),encoding='utf-8')
    return {'ok':not erros,'arquivo':str(base/'indice.json'),'modelos':len(itens),'bytes_modelos':sum(x['bytes'] for x in itens),'segundos':total['segundos'],'erros':erros}


def cli(args):
    if args and args[0]=='indexar':
        pedido=json.loads(Path(args[1]).read_text(encoding='utf-8-sig'))
        exe=Path(C.RAIZ)/'.venv-biblioteca'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
        if not exe.is_file():raise ValueError('instale requirements-biblioteca.txt em .venv-biblioteca')
        r=subprocess.run([str(exe),'-m','director.biblioteca'],input=json.dumps(pedido).encode(),capture_output=True,timeout=180,cwd=C.RAIZ)
        if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-1500:])
        return json.loads(r.stdout)
    d=json.loads((Path(C.WORK)/'biblioteca'/'indice.json').read_text(encoding='utf-8'))
    return catalogo.consultar(d,{'texto':' '.join(args)})


if __name__=='__main__':print(json.dumps(indexar(json.loads(sys.stdin.buffer.read())),ensure_ascii=True))
