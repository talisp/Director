"""Ensaios locais rastreaveis. Reutiliza a ponte/trava; nao instala um worker."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata
import uuid

from . import config as C
from .nucleo import pecas as P


def _agora():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _gravar(path, data):
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")


def _pasta(nome, raiz):
    base = Path(raiz).resolve()
    alvo = (base / nome).resolve()
    if alvo.parent != base:
        raise ValueError("identificador de ensaio invalido")
    return alvo


def criar(nome, pedido, raiz=None):
    raiz = raiz or Path(C.WORK) / "ensaios"
    slug = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    slug = re.sub(r"[^a-z0-9_-]+", "-", slug).strip("-")[:64]
    if not slug:
        raise ValueError("informe um nome para o ensaio")
    eid = dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + slug + "-" + uuid.uuid4().hex[:6]
    pasta = _pasta(eid, raiz)
    pasta.mkdir(parents=True, exist_ok=False)
    meta = {"id": eid, "pedido": pedido, "criado_em": _agora(), "formato": 1}
    _gravar(pasta / "ensaio.json", meta)
    return {"ok": True, "id": eid, "criado_em": meta["criado_em"], "pasta": str(pasta)}


def _indice(inv):
    saida = {}
    for oid, ator in inv.get("controlados", {}).items():
        saida["id:" + oid] = ator
    for ator in inv.get("fora", []):
        saida["ator:" + ator["caminho"]] = ator
    return saida


def diferencas(antes, depois):
    a, b = _indice(antes), _indice(depois)
    return {"criados": sorted(b.keys() - a.keys()), "removidos": sorted(a.keys() - b.keys()),
            "alterados": sorted(k for k in a.keys() & b.keys() if a[k] != b[k])}


def executar(eid, arquivo, editor, raiz=None):
    pasta = _pasta(eid, raiz or Path(C.WORK) / "ensaios")
    if not (pasta / "ensaio.json").is_file():
        raise ValueError("ensaio inexistente; use ensaio criar")
    # Qualquer script autorizado pode ser fornecido; sua copia executada fica no ensaio.
    raw = Path(arquivo).read_bytes()
    codigo = raw.decode("utf-8-sig")
    compile(codigo, str(arquivo), "exec")
    run = pasta / ("execucao-" + uuid.uuid4().hex)
    run.mkdir()
    (run / "script.py").write_bytes(raw)
    registro = {"inicio": _agora(), "sha256": hashlib.sha256(raw).hexdigest(),
                "script": "script.py", "ok": False, "executado": False}
    _gravar(run / "resultado.json", registro)
    t0 = time.monotonic()
    antes = depois = None
    try:
        registro["editor"] = editor.chamar("info")
        antes = editor.chamar("inventory", variaveis=P.variaveis())
        registro["executado"] = True
        registro["retorno"] = editor.chamar("dev_exec", codigo=codigo)
        if registro["retorno"].get("resultado") is None:
            registro["aviso_retorno"] = "o script nao definiu resultado; print nao e capturado como retorno. Atribua resultado = {...} para devolver dados; ok so confirma execucao"
        registro["ok"] = True
    except Exception as exc:
        registro["erro"] = {"tipo": type(exc).__name__, "mensagem": str(exc)}
    finally:
        if antes is not None:
            try:
                depois = editor.chamar("inventory", variaveis=P.variaveis())
                registro["mudancas"] = diferencas(antes, depois)
            except Exception as exc:
                registro["observacao_final_erro"] = str(exc)
        registro.update({"fim": _agora(), "segundos": round(time.monotonic() - t0, 3),
                         "antes": antes, "depois": depois,
                         "limite": "inventario nao prova colisao, aparencia nem efeitos fora do level"})
        _gravar(run / "resultado.json", registro)
    return {k: registro[k] for k in ("ok", "executado", "sha256", "segundos", "mudancas", "erro", "aviso_retorno") if k in registro} | {
        "registro": str(run / "resultado.json"), "retorno": registro.get("retorno")}


def listar(eid=None, raiz=None):
    base = Path(raiz or Path(C.WORK) / "ensaios")
    pastas = [_pasta(eid, base)] if eid else sorted(base.glob("*"))
    saida = []
    for pasta in pastas:
        meta = pasta / "ensaio.json"
        if meta.is_file():
            d = json.loads(meta.read_text(encoding="utf-8"))
            d["execucoes"] = []
            for log in sorted(pasta.glob("execucao-*/resultado.json")):
                r = json.loads(log.read_text(encoding="utf-8"))
                d["execucoes"].append({k: r[k] for k in ("ok", "sha256", "mudancas", "inicio") if k in r} | {"registro": str(log)})
            saida.append(d)
    return {"ok": True, "ensaios": saida}


def cli(args):
    if not args or args[0] == "listar":
        return listar(args[1] if len(args) == 2 else None)
    if args[0] == "criar" and len(args) == 3:
        return criar(args[1], Path(args[2]).read_text(encoding="utf-8-sig"))
    if args[0] == "executar" and len(args) == 3:
        from .ponte import Ponte
        with Ponte("ensaio-" + args[1]) as p:
            return executar(args[1], args[2], p)
    raise ValueError("uso: ensaio criar NOME PEDIDO.txt | executar ID SCRIPT.py | listar [ID]")
