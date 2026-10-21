"""Atualiza apenas director-research, com baseline, backup e perfil ocioso; nao altera fila/config."""
import argparse,hashlib,json,re,shutil,sqlite3,time
from pathlib import Path
from contextlib import closing

FONTE=Path(__file__).resolve().parent/'skills/director-research'


def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def arquivos(root):return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def conferir(perfil):
    destino=perfil/'skills/director-research';base=json.loads((FONTE/'BASELINE-0.2.1.json').read_text(encoding='utf-8'))
    esperado=arquivos(FONTE);mudados=[];conflitos=[]
    for rel,p in esperado.items():
        atual=hashfile(destino/rel);novo=hashfile(p)
        if atual!=novo:mudados.append(rel)
        if atual is not None and atual not in (base.get(rel),novo):conflitos.append(rel)
    return {'igual':not mudados,'mudados':mudados,'conflitos_locais':conflitos,
        'extras_preservados':sorted(set(arquivos(destino))-set(esperado))}


def ocioso(perfil):
    db=perfil/'state.db'
    if not db.is_file():raise ValueError('sem banco do perfil para conferir uso; nao instalar por suposicao')
    with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)) as c:
        if c.execute("select count(*) from session_admissions where status in ('queued','started','unknown')").fetchone()[0]:return False
        return not c.execute('select count(*) from session_turn_leases where expires_at>?',(time.time(),)).fetchone()[0]


def aplicar(perfil):
    r=conferir(perfil)
    if r['igual']:return {**r,'instalado':False}
    if r['conflitos_locais']:raise ValueError('skill mudou fora da baseline; compare antes de sobrescrever')
    if not ocioso(perfil):raise ValueError('perfil pesquisador ocupado; nao interromper nem substituir skill em uso')
    destino=(perfil/'skills/director-research').resolve();backup=(perfil/'skill-backups'/('director-research-'+time.strftime('%Y%m%d-%H%M%S'))).resolve()
    assert destino.parent==(perfil/'skills').resolve() and destino.name=='director-research'
    assert (perfil/'skill-backups').resolve() in backup.parents
    for rel,p in arquivos(FONTE).items():
        d=destino/rel
        if hashfile(d)==hashfile(p):continue
        if d.exists():
            b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(d,b)
        d.parent.mkdir(parents=True,exist_ok=True);tmp=d.with_suffix(d.suffix+'.tmp-codex');shutil.copy2(p,tmp);tmp.replace(d)
    return {**conferir(perfil),'instalado':True,'backup':str(backup),'fila_preservada':True,'gateway_reiniciado':False}


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('perfil',nargs='?',default='hermes-dev');a.add_argument('--aplicar',action='store_true');q=a.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]+',q.perfil):raise ValueError('nome de perfil invalido')
    p=Path.home()/'AppData/Local/hermes/profiles'/q.perfil
    if not p.is_dir():raise ValueError('perfil inexistente')
    print(json.dumps(aplicar(p) if q.aplicar else conferir(p),ensure_ascii=True))


if __name__=='__main__':main()
