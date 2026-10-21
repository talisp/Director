"""Coletores pequenos de fontes publicas. Sem inferencia, cenas ou execucao de receitas.

URLs, selecao e autorizacao sao responsabilidade do piloto chamador. Arquivos e
evidencias ficam em R:; hashes locais nao substituem hash publicado pelo fornecedor.
"""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import urllib.request
from urllib.parse import urlsplit
import zipfile

from . import acervo as A
from .acervo_coleta import trava_escopo,hash_arquivo


def _destino(p):
    p=Path(p).absolute();base=Path(A.PADRAO).absolute().parent.parent.resolve()
    if not p.resolve().is_relative_to(base):raise ValueError('pilotos devem ficar em R:/CINF/BD')
    return p


def baixar(url,destino,*,max_bytes,tamanho=None,sha256=None):
    """Cache com manifesto, limite por arquivo e verificacao em toda reutilizacao."""
    p=_destino(destino)
    if urlsplit(url).scheme!='https':raise ValueError('fonte deve usar HTTPS')
    if type(max_bytes) is not int or not 0<max_bytes<=32*1024*1024:raise ValueError('limite deve ser 1..32 MiB')
    if tamanho is not None and (type(tamanho) is not int or not 0<=tamanho<=max_bytes):raise ValueError('tamanho acima do limite')
    with trava_escopo(None,A.identidade('fonte-publica',str(p))):
        side=p.with_name(p.name+'.procedencia.json')
        if p.exists():
            if not side.is_file():raise ValueError('arquivo existente sem procedencia; revisar antes de reutilizar')
            d=json.loads(side.read_text(encoding='utf-8'))
            atual=hash_arquivo(p)
            if d['url']!=url or atual!=d['sha256'] or (sha256 and atual!=sha256):raise ValueError('cache divergente; nao sobrescrever')
            if p.stat().st_size>max_bytes or (tamanho is not None and p.stat().st_size!=tamanho):raise ValueError('tamanho do cache divergente')
            return {**d,'reutilizado':True}
        if not p.parent.exists():p.parent.mkdir(parents=True,exist_ok=True)
        if shutil.disk_usage(p.parent).free<max_bytes+16*1024*1024:raise ValueError('espaco insuficiente')
        tmp=p.with_name(p.name+'.part');tmpmeta=side.with_name(side.name+'.part')
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Director-piloto/1.0'})
            with urllib.request.urlopen(req,timeout=60) as r,tmp.open('wb') as out:
                total=0
                while b:=r.read(min(1024*1024,max_bytes-total+1)):
                    total+=len(b)
                    if total>max_bytes:raise ValueError('resposta acima do limite')
                    out.write(b)
            h=hash_arquivo(tmp)
            if tamanho is not None and total!=tamanho:raise ValueError('tamanho divergente')
            if sha256 and h!=sha256:raise ValueError('SHA256 remoto divergente')
            d={'url':url,'caminho':str(p),'sha256':h,'bytes':total,'hash_remoto_conferido':bool(sha256),'capturado_em':A.agora()}
            tmpmeta.write_text(A.dump(d),encoding='utf-8')
            os.replace(tmp,p);os.replace(tmpmeta,side)
            return {**d,'reutilizado':False}
        finally:
            for f in (tmp,tmpmeta):
                if f.exists():f.unlink()


def extrair_imagens(arquivo,destino):
    """Somente PNG/JPEG; nao executa instaladores nem extrai caminhos perigosos."""
    raiz=_destino(destino);saidas=[]
    with zipfile.ZipFile(arquivo) as z:
        infos=z.infolist()
        if len(infos)>256 or sum(f.file_size for f in infos)>32*1024*1024:raise ValueError('ZIP acima do limite do piloto')
        vistos=set()
        for f in infos:
            raw=f.orig_filename;n=PurePosixPath(f.filename)
            if n.is_absolute() or '..' in n.parts or '\\' in raw or '\0' in raw or ':' in raw or (f.external_attr>>16)&0o170000==0o120000:
                raise ValueError('caminho ZIP inseguro')
            if f.filename.casefold() in vistos:raise ValueError('caminho ZIP duplicado')
            vistos.add(f.filename.casefold())
        for f in infos:
            if f.is_dir() or PurePosixPath(f.filename).suffix.lower() not in ('.png','.jpg','.jpeg'):continue
            p=raiz/f.filename
            if not p.resolve().is_relative_to(raiz.resolve()):raise ValueError('destino fora da pasta')
            b=z.read(f)  # ZipFile confere CRC; tamanho total ja limitado.
            h=hashlib.sha256(b).hexdigest()
            if p.exists() and hash_arquivo(p)!=h:raise ValueError('imagem local divergente; nao sobrescrever')
            if not p.exists():
                p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as out:out.write(b)
            saidas.append({'caminho':str(p),'sha256':h,'bytes':len(b)})
    if not saidas:raise ValueError('ZIP sem imagens utilizaveis')
    return saidas


def registrar_material(asset,download,imagens,origem,db=None):
    """Metadados declarados e imagens verificadas; nao certifica material Unreal."""
    from PIL import Image
    medidas=[]
    for f in imagens:
        if hash_arquivo(Path(f['caminho']))!=f['sha256']:raise ValueError('imagem mudou antes do registro')
        with Image.open(f['caminho']) as img:
            medidas.append({**f,'pixels':list(img.size),'modo':img.mode});img.verify()
    with A.abrir(db,escrita=True) as c:
        A.fonte(c,'ambientcg','https://ambientcg.com','CC0-1.0')
        oid=A.objeto(c,'ambientcg',asset['assetId'],asset['displayName'],'material')
        A.arquivo(c,download['caminho'],licenca='CC0-1.0',origem=origem,sha_esperado=download['sha256'],objeto_id=oid)
        for f in medidas:A.arquivo(c,f['caminho'],licenca='CC0-1.0',origem=origem,sha_esperado=f['sha256'],objeto_id=oid)
        for t in asset.get('tags',[]):A.tag(c,oid,t,'en','declarado_ambientcg')
        for t in (['madeira'] if asset['assetId'].startswith('Wood') else ['azulejo','ceramica']):A.tag(c,oid,t,'pt','traducao_sugerida')
        A.caracteristica(c,oid,'material_fonte',asset,'declaracao_ambientcg',download['url'])
        A.caracteristica(c,oid,'texturas_pixels',medidas,'Pillow_imagens_verificadas',download['sha256'])
        A.registro(c,'piloto_material',oid,{'download':download,'imagens':medidas,'licenca_url':'https://docs.ambientcg.com/license/'},origem)
        A.indexar_busca(c,[oid])
    return {'objeto':oid,'imagens':len(medidas),'pixels':[m['pixels'] for m in medidas],
            'limite':'baixado e catalogado; nao comprova material aplicado, escala UV ou alteracao da cena'}
