"""Confere/reaplica a correcao local do Hermes apenas na base auditada; nao reinicia agentes."""
import argparse,datetime,hashlib,json,shutil,subprocess
from pathlib import Path

PASTA=Path(__file__).parent/'correcoes'
BACKUPS=Path('R:/CINF/BD/Director/backups-hermes-rota')


def _git(repo,*args,entrada=None):
    # Nao usar stdin text no Windows: traduz LF para CRLF antes do git apply.
    r=subprocess.run(['git','-C',str(repo),*args],capture_output=True,
                     input=entrada.encode('utf-8') if entrada is not None else None)
    r.stdout=r.stdout.decode('utf-8',errors='replace');r.stderr=r.stderr.decode('utf-8',errors='replace')
    return r


def conferir(repo,aplicar=False):
    repo=Path(repo).resolve();m=json.loads((PASTA/'rota-native.json').read_text(encoding='utf-8'))
    arquivos={}
    for rel,hashes in m['arquivos'].items():
        p=(repo/rel).resolve()
        if not p.is_relative_to(repo):raise ValueError('arquivo fora do repositorio')
        atual=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        arquivos[rel]='corrigido' if atual==hashes['depois'] else 'base' if atual==hashes['antes'] else 'conflito'
    if all(v=='corrigido' for v in arquivos.values()):return {'ok':True,'estado':'ja_corrigido','arquivos':arquivos}
    if any(v!='base' for v in arquivos.values()):raise ValueError('mudanca local ou aplicacao parcial; comparar, nao sobrescrever')
    head=_git(repo,'rev-parse','HEAD')
    if head.returncode or head.stdout.strip()!=m['base']:raise ValueError('versao Hermes diferente; revalidar correcao antes de aplicar')
    # Checkout Windows pode converter o patch para CRLF; git apply recebe LF por stdin.
    patch=(PASTA/'rota-native.patch').read_text(encoding='utf-8')
    if _git(repo,'apply','--check','-',entrada=patch).returncode:raise ValueError('patch nao aplica; arquivos preservados')
    if not aplicar:return {'ok':True,'estado':'aplicavel','arquivos':arquivos}
    backup=BACKUPS/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup.mkdir(parents=True)
    for rel in arquivos:
        b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/rel,b)
    if _git(repo,'apply','-',entrada=patch).returncode:raise ValueError('falha na aplicacao; inspecionar backup '+str(backup))
    r=conferir(repo);return {**r,'backup':str(backup),'gateway_reiniciado':False}


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--repo',type=Path,default=Path.home()/'AppData/Local/hermes/hermes-agent')
    a.add_argument('--aplicar',action='store_true');q=a.parse_args()
    print(json.dumps(conferir(q.repo,q.aplicar),ensure_ascii=True))


if __name__=='__main__':main()
