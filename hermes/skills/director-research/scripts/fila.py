#!/usr/bin/env python3
"""Fila persistente para pesquisas do Director; stdlib; nenhuma operação no Director.

Fonte de verdade: <root>/fila.json; espelho humano: <root>/fila.md.
Uso: python fila.py [--root DIR] add URL [URL ...] [--foco TEXTO] | foco URL TEXTO | next | begin URL |
      checkpoint URL "feito: ... | falta: ... | arquivos: ..." | finish URL | partial URL chamadas|ferramenta|decisao|orcamento MOTIVO |
      status | painel | versao
Painel para o Talis (português simples, um bloco por projeto): <root>/PAINEL.md, refeito a cada finish.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_ROOT = Path.home() / "pesquisas-director" / "estudos"
SKILL_DIR = Path(__file__).resolve().parent.parent
STATES = {"PENDENTE", "EM_ANALISE", "CONCLUIDO", "PARCIAL"}
REQUIRED = ["AVALIACAO.md", "analise.md", "evidencias.md", "experimentos.md", "estado.md"]
# repositórios que a pesquisa só lê: a raiz da pesquisa não pode ficar dentro deles, e o git status
# deles é anotado no begin e conferido no finish (medição, não bloqueio)
PROTEGIDOS_NOMES = {"director", "director-publicado", "director-correcoes", "unreal-macros"}
CHECKPOINT_PARTES = ("feito:", "falta:", "arquivos:")
MARCOS_MINIMOS = 3
# os únicos motivos para parar com a fila cheia (16/10: a v0.2 parou duas vezes alegando "limite real de contexto"
# a 200–240 mil de 1 milhão de tokens, com 75 de 200 chamadas usadas)
PARADAS = {"chamadas": "o Hermes avisou que as chamadas desta vez estão acabando",
           "ferramenta": "ferramenta, rede ou disco quebrados, depois de tentar contornar",
           "decisao": "uma decisão que só o Talis pode tomar",
           "orcamento": "o teto autorizado do lote foi atingido; preservar fila e pedir ampliacao antes de continuar"}
PARADA_POR_CONTEXTO = re.compile(r"contexto|tokens|sess[ãa]o (longa|cheia|grande)|cansa", re.I)
PAUSA = re.compile(r"paus|par(ar|ei|ando|ada)\b|interromp|limite|retomar", re.I)
CONTEXTO_NAO_PARA = ("o tamanho do contexto não é motivo para parar (o limite depende do modelo/perfil atual; a decisão sobre "
                     "contexto é do Talis): meça com medir_contexto.py, anote em estado.md e siga. Paradas válidas: "
                     + "; ".join(f"{k} = {v}" for k, v in PARADAS.items()))


def protegidos() -> list[Path]:
    extra = os.environ.get("DIRECTOR_RESEARCH_PROTEGIDOS")  # para os testes; separado por os.pathsep
    if extra is not None:
        return [Path(p).expanduser().resolve() for p in extra.split(os.pathsep) if p]
    return [(Path.home() / n).resolve() for n in ("Director", "Director-publicado", "Director-correcoes", "unreal-macros")]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    p = urlsplit(raw)
    if (p.hostname or "").lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Somente URLs de repositórios github.com são aceitas nesta versão")
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2 or not re.fullmatch(r"[A-Za-z0-9-]+", parts[0]):
        raise ValueError("Formato esperado: https://github.com/owner/repo")
    repo = parts[1][:-4] if parts[1].lower().endswith(".git") else parts[1]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", repo) or repo in {".", ".."}:
        raise ValueError("Nome de repositório inválido")
    return f"https://github.com/{parts[0]}/{repo}", f"{parts[0].lower()}--{repo.lower()}"


def conferir_raiz(root: Path) -> None:
    """A raiz da pesquisa não pode ser nem ficar dentro de um repositório protegido (caminho inteiro, já resolvido)."""
    for anc in (root, *root.parents):
        if anc.name.lower() in PROTEGIDOS_NOMES:
            raise ValueError(f"Raiz de pesquisa dentro de repositório protegido: {anc}")
    for prot in protegidos():
        if root == prot or prot in root.parents:
            raise ValueError(f"Raiz de pesquisa dentro de repositório protegido: {prot}")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".fila-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@contextmanager
def hold_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".fila.lock"
    with open(path, "a+b") as fh:
        fh.seek(0, os.SEEK_END)
        if fh.tell() == 0:
            fh.write(b"x")
            fh.flush()
        fh.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def read_data(root: Path) -> dict:
    p = root / "fila.json"
    if not p.exists():
        return {"version": 1, "items": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("items"), list):
        raise ValueError("Formato fila.json incompatível; não sobrescrevi os dados")
    return data


def markdown(data: dict) -> str:
    rows = [
        "# Fila de pesquisas para o Director", "",
        "> Gerada automaticamente de `fila.json` por `scripts/fila.py`. Não editar a tabela manualmente durante a pesquisa.", "",
        "| # | Repositório | Estado | Etapa / pendência | Adicionado (UTC) | Resultado |",
        "|---:|---|---|---|---|---|",
    ]
    for i, item in enumerate(data["items"], 1):
        phase = (item.get("etapa") or "—").replace("|", "/").replace("\n", " ")[:110]
        folder = f"repositorios/{item['id']}/AVALIACAO.md"
        rows.append(f"| {i} | {item['url']} | {item['estado']} | {phase} | {item['adicionado']} | `{folder}` |")
    if not data["items"]:
        rows.append("| — | Sem repositórios ainda | — | — | — | — |")
    rows.extend(["", "**Próximo:** use `fila.py next`; novas URLs entram com `fila.py add URL`.", ""])
    return "\n".join(rows)


def initialize_files(root: Path):
    for name, content in {
        "indice.md": "# Índice de projetos\n\n| Projeto | Commit | Nota 01 / 06 / 11 / 13 | Aplicabilidade ao Director | Avaliação |\n|---|---|---|---|---|\n",
        "comparativo.md": "# Comparativo entre projetos\n\nAgrupar por critérios 01–17 conforme `references/RUBRICA.md`. Não confundir ausência de evidência com nota zero.\n",
        "sintese-geral.md": "# Síntese geral\n\n## Descobertas que atravessam repositórios\n\n## Técnicas a preservar\n\n## Questões ainda não verificadas\n",
    }.items():
        p = root / name
        if not p.exists():
            atomic_write(p, content)
    (root / "repositorios").mkdir(exist_ok=True)
    (root / "conhecimentos").mkdir(exist_ok=True)
    (root / "laboratorio").mkdir(exist_ok=True)


def save(root: Path, data: dict) -> None:
    atomic_write(root / "fila.json", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    atomic_write(root / "fila.md", markdown(data))


def get(data: dict, url: str) -> dict:
    _, slug = normalize(url)
    for item in data["items"]:
        if item["id"] == slug:
            return item
    raise ValueError("Repositório não está na fila; use 'add' primeiro")


def proximo(data: dict, exceto=None):
    """Ordem: o que está EM_ANALISE, depois o PARCIAL (retomar antes de avançar), depois o primeiro PENDENTE."""
    for estado in ("EM_ANALISE", "PARCIAL", "PENDENTE"):
        item = next((x for x in data["items"] if x["estado"] == estado and x is not exceto), None)
        if item:
            return item
    return None


def versao_da_skill() -> dict:
    """Versão do SKILL.md e hash curto de cada arquivo da skill (para saber com que skill a pesquisa foi feita)."""
    texto = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^version:\s*(\S+)", texto, re.M)
    hashes = {}
    for p in sorted(SKILL_DIR.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            hashes[p.relative_to(SKILL_DIR).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    return {"versao": m.group(1) if m else "?", "hashes": hashes}


def git_status() -> dict:
    """git status --porcelain de cada repositório protegido (linhas), ou o motivo de não ter lido."""
    saida = {}
    for repo in protegidos():
        if not (repo / ".git").exists():
            saida[str(repo)] = {"erro": "não encontrado"}
            continue
        try:
            r = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=60)
            saida[str(repo)] = {"linhas": sorted(r.stdout.splitlines())} if r.returncode == 0 else {"erro": r.stderr.strip()[:200]}
        except (OSError, subprocess.TimeoutExpired) as e:
            saida[str(repo)] = {"erro": str(e)[:200]}
    return saida


def comparar_git(antes: dict, depois: dict) -> list[str]:
    linhas = []
    for repo in sorted(set(antes) | set(depois)):
        a, d = antes.get(repo, {}), depois.get(repo, {})
        if "linhas" not in a or "linhas" not in d:
            linhas.append(f"{repo}: NÃO VERIFICADO ({a.get('erro') or d.get('erro') or 'sem baseline'})")
            continue
        novas = sorted(set(d["linhas"]) - set(a["linhas"]))
        sumiram = sorted(set(a["linhas"]) - set(d["linhas"]))
        if not novas and not sumiram:
            linhas.append(f"{repo}: igual ao início ({len(d['linhas'])} entradas que já existiam)")
        else:
            linhas.append(f"{repo}: MUDOU durante a pesquisa (atribuição indeterminada: outro agente pode ter mexido) — "
                          f"novas: {novas or 'nenhuma'}; sumiram: {sumiram or 'nenhuma'}")
    return linhas


def foco_das_notas(root: Path, url: str) -> list[str]:
    """Linhas de fila-notas.md (formato livre da v0.1) que citam este repositório."""
    p = root / "fila-notas.md"
    if not p.exists():
        return []
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if url.lower() in l.lower()]


def secao(texto: str, titulo: str) -> str:
    """O conteúdo da seção `## titulo` de um Markdown (até a próxima `## `), sem o título."""
    partes = re.split(r"^## +" + re.escape(titulo) + r"[^\n]*\n", texto, maxsplit=1, flags=re.M)
    return partes[1].split("\n## ", 1)[0].strip() if len(partes) > 1 else ""


def painel(root: Path, data: dict) -> str:
    """PAINEL.md: o que o Talis lê para decidir o que copiar, o que inspira e o que dá para usar no Director."""
    linhas = ["# Painel das pesquisas para o Director", "",
              "> Feito por `fila.py` a partir das avaliações. Para cada projeto: o que dá para **copiar**, o que serve de "
              "**inspiração** e o que dá para **usar** no Director, em português simples. Leve para a conversa com o Claude Code.", ""]
    feitos = [x for x in data["items"] if x["estado"] == "CONCLUIDO"]
    for item in feitos:
        av = root / "repositorios" / item["id"] / "AVALIACAO.md"
        texto = av.read_text(encoding="utf-8") if av.is_file() else ""
        linhas += [f"## {item['url'].split('github.com/')[-1]}", ""]
        if item.get("foco"):
            linhas += [f"**O que você pediu:** {item['foco']}", ""]
        para = secao(texto, "Para o Talis")
        linhas += [para or "_(avaliação feita antes da v0.2, sem a seção \"Para o Talis\"; veja a avaliação completa)_", "",
                   f"Avaliação completa: `repositorios/{item['id']}/AVALIACAO.md` · concluído em {item.get('concluido', '?')}", ""]
    if not feitos:
        linhas += ["Nenhum projeto concluído ainda.", ""]
    resto = [x for x in data["items"] if x["estado"] != "CONCLUIDO"]
    if resto:
        linhas += ["## Ainda na fila", "", "| Projeto | Estado | O que você pediu |", "|---|---|---|"]
        for x in resto:
            linhas.append(f"| {x['url'].split('github.com/')[-1]} | {x['estado']} | {(x.get('foco') or '—').replace('|', '/')} |")
        linhas.append("")
    return "\n".join(linhas)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="pasta EXTERNA ao Director")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("init")
    a = sub.add_parser("add"); a.add_argument("urls", nargs="+"); a.add_argument("--foco", default=None)
    c = sub.add_parser("foco"); c.add_argument("url"); c.add_argument("texto")
    sub.add_parser("next")
    sub.add_parser("status")
    sub.add_parser("versao")
    g=sub.add_parser("gargalo");g.add_argument("url");g.add_argument("arquivo",type=Path)
    sub.add_parser("painel")
    for cmd in ("begin", "finish"):
        c = sub.add_parser(cmd); c.add_argument("url")
    c = sub.add_parser("checkpoint"); c.add_argument("url"); c.add_argument("etapa")
    c = sub.add_parser("partial"); c.add_argument("url"); c.add_argument("tipo", help="|".join(PARADAS)); c.add_argument("motivo")
    args = parser.parse_args(argv)
    if args.action == "versao":
        print(json.dumps(versao_da_skill(), ensure_ascii=False, indent=1))
        return 0
    root = args.root.expanduser().resolve()
    conferir_raiz(root)
    with hold_lock(root):
        initialize_files(root)
        data = read_data(root)
        changed = False
        if args.action == "add":
            existing = {x["id"] for x in data["items"]}
            for raw in args.urls:
                url, ident = normalize(raw)
                if ident in existing:
                    if args.foco:
                        item = get(data, url)
                        item.update(foco=args.foco.strip(), atualizado=now())
                        changed = True
                        print("JÁ EXISTE (foco atualizado):", url, "—", item["foco"])
                    else:
                        print("JÁ EXISTE:", url)
                    continue
                novo = {"id": ident, "url": url, "estado": "PENDENTE", "etapa": "Aguardando pesquisa", "adicionado": now(), "atualizado": now()}
                if args.foco:
                    novo["foco"] = args.foco.strip()
                data["items"].append(novo)
                print("ADICIONADO:", url, f"— foco: {novo['foco']}" if args.foco else "")
                existing.add(ident)
                changed = True
        elif args.action == "foco":
            item = get(data, args.url)
            item.update(foco=args.texto.strip(), atualizado=now())
            changed = True
            print("FOCO GRAVADO:", item["url"], "—", item["foco"])
        elif args.action == "gargalo":
            item=get(data,args.url)
            if item['estado']=='CONCLUIDO':raise ValueError('Nao vincular retroativamente estudo concluido; use ficha adicional sem reabrir a fila')
            vinculo=json.loads(args.arquivo.read_text(encoding='utf-8-sig'))
            for k in ('issue','pedido','commit_director','hipotese'):
                if not isinstance(vinculo.get(k),str) or not vinculo[k].strip():raise ValueError('vinculo requer '+k)
            if not re.fullmatch('[0-9a-f]{40}',vinculo['commit_director']):raise ValueError('commit completo do Director obrigatorio')
            item['gargalo']=vinculo;changed=True
            print('GARGALO VINCULADO:',item['url'],vinculo['issue'])
        elif args.action == "next":
            item = proximo(data)
            if item:
                print(f"PRÓXIMO: {item['url']} [{item['estado']}] {item.get('etapa', '')}")
                if item.get("foco"):
                    print("FOCO:", item["foco"])
                if item["estado"] == "PARCIAL":
                    print("RETOMAR: leia o estado.md e os checkpoints deste projeto antes de continuar.")
            else:
                print("FILA VAZIA: nenhum projeto EM_ANALISE, PARCIAL ou PENDENTE.")
        elif args.action == "begin":
            item = get(data, args.url)
            active = next((x for x in data["items"] if x["estado"] == "EM_ANALISE" and x is not item), None)
            if active:
                raise ValueError(f"Já há pesquisa EM_ANALISE: {active['url']}")
            if item["estado"] == "CONCLUIDO":
                raise ValueError("Projeto concluído: não reiniciar sem decisão explícita")
            retomada = item["estado"] in ("EM_ANALISE", "PARCIAL") or bool(item.get("checkpoints"))
            skill = versao_da_skill()
            if retomada and item.get("skill") and item["skill"].get("hashes") != skill["hashes"]:
                mudados = sorted(k for k in set(item["skill"]["hashes"]) | set(skill["hashes"])
                                 if item["skill"]["hashes"].get(k) != skill["hashes"].get(k))
                print(f"AVISO: a skill mudou desde o começo desta pesquisa ({item['skill']['versao']} → {skill['versao']}): "
                      + ", ".join(mudados))
                item.setdefault("skill_anteriores", []).append(item["skill"])
            item.update(estado="EM_ANALISE", atualizado=now(), skill=skill)
            if not item.get("iniciado"):
                item["iniciado"] = now()
            if not item.get("git_inicio"):
                item["git_inicio"] = git_status()
            changed = True
            print("INICIADO/RETOMADO:" if retomada else "INICIADO:", item["url"], f"(skill {skill['versao']})")
            for repo, st in item["git_inicio"].items():
                print(f"BASELINE {repo}: " + (f"{len(st['linhas'])} entradas já existentes" if "linhas" in st else st["erro"]))
            if item.get("foco"):
                print("FOCO:", item["foco"])
            for linha in foco_das_notas(root, item["url"]):
                print("NOTA (fila-notas.md):", linha)
            for cp in item.get("checkpoints", []):
                print(f"CHECKPOINT ANTERIOR {cp['quando']}: {cp['texto']}")
        elif args.action == "checkpoint":
            item = get(data, args.url)
            if item["estado"] != "EM_ANALISE":
                raise ValueError("Somente pesquisa EM_ANALISE aceita checkpoint")
            texto = args.etapa.strip()
            faltam = [p for p in CHECKPOINT_PARTES if p not in texto.lower()]
            if faltam:
                raise ValueError("checkpoint precisa dizer " + ", ".join(CHECKPOINT_PARTES) +
                                 f" (faltou {', '.join(faltam)}). Ex.: \"feito: arquitetura lida | falta: testes | arquivos: estado.md, evidencias.md\"")
            if PAUSA.search(texto) and PARADA_POR_CONTEXTO.search(texto):
                raise ValueError("checkpoint recusado: " + CONTEXTO_NAO_PARA)
            item.setdefault("checkpoints", []).append({"quando": now(), "texto": texto})
            item.update(etapa=texto, atualizado=now())
            changed = True
            print(f"CHECKPOINT {len(item['checkpoints'])}:", item["url"], texto)
            print("CONTINUE: o checkpoint só registra; ele não encerra a sua vez. Chame a próxima ferramenta agora.")
        elif args.action == "finish":
            item = get(data, args.url)
            repo_folder = root / "repositorios" / item["id"]
            missing = [x for x in REQUIRED if not (repo_folder / x).is_file()]
            if missing:
                raise ValueError(f"Arquivos obrigatórios ausentes em {repo_folder}: {', '.join(missing)}")
            from verificar_avaliacao import check, check_experimentos
            errs = check(repo_folder / "AVALIACAO.md") + check_experimentos(repo_folder / "experimentos.md")
            if item.get('gargalo'):
                from verificar_ficha import check as check_ficha
                ficha=repo_folder/'FICHA_OPERADOR.json'
                if not ficha.is_file():errs.append('gargalo exige FICHA_OPERADOR.json')
                else:
                    d=json.loads(ficha.read_text(encoding='utf-8-sig'));errs.extend(check_ficha(d))
                    for k in ('issue','pedido','commit_director'):
                        if d.get(k)!=item['gargalo'][k]:errs.append('ficha diverge do vinculo: '+k)
            if item.get("foco") and "resposta ao foco" not in (repo_folder / "AVALIACAO.md").read_text(encoding="utf-8").lower():
                errs.append(f"o Talis pediu um foco ({item['foco']}); a seção 'Para o Talis' precisa de '**Resposta ao foco:**'")
            if errs:
                raise ValueError("Relatório incompleto: " + "; ".join(errs))
            if item["estado"] != "EM_ANALISE":
                raise ValueError("Só finalizar pesquisa EM_ANALISE")
            n_cp = len(item.get("checkpoints", []))
            git_fim = git_status()
            item.update(estado="CONCLUIDO", atualizado=now(), concluido=now(), etapa="Relatórios completos; avaliação validada",
                        git_fim=git_fim)
            changed = True
            print("CONCLUÍDO:", item["url"])
            if n_cp < MARCOS_MINIMOS:
                print(f"AVISO: só {n_cp} checkpoint(s) nesta pesquisa; o combinado são {MARCOS_MINIMOS} "
                      "(arquitetura, código e testes, evidências). Registre isso em estado.md.")
            atomic_write(root / "PAINEL.md", painel(root, data))
            print("PAINEL atualizado:", root / "PAINEL.md")
            for linha in comparar_git(item.get("git_inicio", {}), git_fim):
                print("GIT", linha)
            nxt = proximo(data)
            if nxt:
                print(f"PRÓXIMO DA FILA: {nxt['url']} [{nxt['estado']}]")
                print(f"FAÇA AGORA somente se ainda couber no lote autorizado: fila.py begin {nxt['url']} — ao atingir o teto, encerre o lote e preserve a fila. Não amplie o orçamento. Dentro do teto, continue a fila. O tamanho do contexto não é motivo de parada. Parar só com "
                      "'partial URL <" + "|".join(PARADAS) + "> MOTIVO'.")
            else:
                print("FILA VAZIA: pode escrever o relatório final ao usuário.")
        elif args.action == "partial":
            item = get(data, args.url)
            if item["estado"] == "CONCLUIDO":
                raise ValueError("Projeto concluído: não transformar em parcial silenciosamente")
            if args.tipo not in PARADAS:
                raise ValueError(f"tipo de parada {args.tipo!r} não existe. Paradas válidas: "
                                 + "; ".join(f"{k} = {v}" for k, v in PARADAS.items()))
            if args.tipo != "orcamento" and PARADA_POR_CONTEXTO.search(args.motivo):
                raise ValueError("partial recusado: " + CONTEXTO_NAO_PARA)
            motivo = f"{args.tipo}: {args.motivo}"
            item.update(estado="PARCIAL", atualizado=now(), etapa=motivo)
            item.setdefault("checkpoints", []).append({"quando": now(), "texto": "PARCIAL: " + motivo})
            changed = True
            print("PARCIAL (o next retoma este antes dos pendentes):", item["url"], motivo)
        elif args.action == "painel":
            atomic_write(root / "PAINEL.md", painel(root, data))
            print("PAINEL:", root / "PAINEL.md")
        elif args.action == "status":
            for i, item in enumerate(data["items"], 1):
                print(f"{i:>3} {item['estado']:<12} {item['url']} — {item.get('etapa', '')}")
            if not data["items"]:
                print("Fila vazia")
        if changed or not (root / "fila.md").exists() or args.action in {"status", "next", "init"}:
            save(root, data)
    print("FILA:", root / "fila.md")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr,'reconfigure'):sys.stderr.reconfigure(encoding='utf-8')
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("ERRO:", exc, file=sys.stderr)
        raise SystemExit(2)
