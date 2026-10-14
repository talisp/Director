"""Projeto de laboratório do Unreal: criar, abrir, fechar e ver o estado.

Uso (na raiz da pasta do Director):
  venv\\Scripts\\python.exe -m director.lab criar | abrir | fechar | estado

O laboratório é um projeto novo e enxuto (modelo em branco de Blueprint da Epic), com o servidor de ferramentas
numa porta própria. O editor do projeto do filme não é tocado.
"""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

from . import config as C

MODELO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(C.EDITOR_EXE)))), "Templates", "TP_BlankBP")

UPROJECT = {
    "FileVersion": 3,
    "EngineAssociation": "5.8",
    "Category": "",
    "Description": "Laboratorio do Director (cenarios funcionais). Nao e o projeto do filme.",
    "Modules": [],
    "Plugins": [
        {"Name": "ModelingToolsEditorMode", "Enabled": True, "TargetAllowList": ["Editor"]},
        {"Name": "ModelContextProtocol", "Enabled": True},
        {"Name": "EditorToolset", "Enabled": True},
        {"Name": "GeometryScripting", "Enabled": True},
    ],
}

MCP_INI = f"""[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]
ServerUrlPath=/mcp
ServerPortNumber={C.LAB_PORTA}
bAutoStartServer=True
bEnableToolSearch=True
"""

# A malha de navegação é refeita com o jogo rodando (porta que abre e fecha muda por onde se anda).
NAV_INI = """
[/Script/NavigationSystem.RecastNavMesh]
RuntimeGeneration=Dynamic
"""

MAPAS_INI = """
[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap={mapa}
GameDefaultMap={mapa}
"""


def criar() -> dict:
    """Cria o projeto se ele não existe. Não sobrescreve um laboratório que já existe."""
    if os.path.exists(C.LAB_UPROJECT):
        return {"ok": True, "criado": False, "projeto": C.LAB_UPROJECT}
    os.makedirs(os.path.join(C.LAB_DIR, "Config"), exist_ok=True)
    os.makedirs(os.path.join(C.LAB_DIR, "Content"), exist_ok=True)
    for nome in ("DefaultEditor.ini", "DefaultGame.ini", "DefaultInput.ini"):
        shutil.copyfile(os.path.join(MODELO, "Config", nome), os.path.join(C.LAB_DIR, "Config", nome))
    with open(os.path.join(MODELO, "Config", "DefaultEngine.ini"), encoding="utf-8") as f:
        engine = f.read().replace("GameDefaultMap=/Engine/Maps/Templates/OpenWorld", "GameDefaultMap=/Engine/Maps/Entry")
    with open(os.path.join(C.LAB_DIR, "Config", "DefaultEngine.ini"), "w", encoding="utf-8") as f:
        f.write(engine + NAV_INI)
    with open(os.path.join(C.LAB_DIR, "Config", "DefaultEditorPerProjectUserSettings.ini"), "w", encoding="utf-8") as f:
        f.write(MCP_INI)
    with open(C.LAB_UPROJECT, "w", encoding="utf-8") as f:
        json.dump(UPROJECT, f, indent="\t")
    return {"ok": True, "criado": True, "projeto": C.LAB_UPROJECT}


def mapa_inicial(mapa: str) -> None:
    """Faz o editor do laboratório abrir direto na cena (mapa = /Game/Director/Cenas/X.X)."""
    caminho = os.path.join(C.LAB_DIR, "Config", "DefaultEngine.ini")
    with open(caminho, encoding="utf-8") as f:
        linhas = [x for x in f.read().splitlines() if not x.startswith(("EditorStartupMap=", "GameDefaultMap="))]
    saida = []
    for x in linhas:
        saida.append(x)
        if x.strip() == "[/Script/EngineSettings.GameMapsSettings]":
            saida += [f"EditorStartupMap={mapa}", f"GameDefaultMap={mapa}"]
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(saida) + "\n")


def _responde(prazo_s: float = 3.0) -> bool:
    corpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                   "clientInfo": {"name": "director-lab", "version": "0.1"}}}).encode()
    req = urllib.request.Request(C.LAB_URL, data=corpo, headers={"Content-Type": "application/json",
                                                                 "Accept": "application/json, text/event-stream"})
    try:
        with urllib.request.urlopen(req, timeout=prazo_s) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def _pid_vivo(pid: int) -> bool:
    saida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    return str(pid) in saida and "UnrealEditor" in saida


def _ler_estado() -> dict:
    try:
        with open(C.LAB_ESTADO, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def estado() -> dict:
    e = _ler_estado()
    pid = e.get("pid")
    vivo = bool(pid) and _pid_vivo(pid)
    return {"pid": pid if vivo else None, "processo_vivo": vivo, "responde": _responde(), "porta": C.LAB_PORTA,
            "projeto": C.LAB_UPROJECT, "projeto_existe": os.path.exists(C.LAB_UPROJECT)}


def abrir(prazo_s: float = 900.0) -> dict:
    """Abre o editor do laboratório (se não está aberto) e espera o servidor de ferramentas responder."""
    antes = estado()
    if antes["responde"]:
        return {"ok": True, "ja_aberto": True, **antes}
    if antes["processo_vivo"]:
        raise RuntimeError(f"o editor do laboratório está vivo (pid {antes['pid']}) mas não responde na porta {C.LAB_PORTA}")
    if not os.path.exists(C.LAB_UPROJECT):
        raise RuntimeError("o projeto de laboratório não existe: rode `criar`")
    os.makedirs(C.WORK, exist_ok=True)
    amb = dict(os.environ)
    amb["UE_PYTHONPATH"] = C.EDITOR_PYTHON  # só neste processo: o projeto do filme continua com o dele
    t0 = time.time()
    # -culture=en: a ferramenta de grafos da Epic usa os nomes dos nós em inglês (no editor em português ela falha);
    # -unattended: nenhum diálogo modal (um diálogo trava o servidor de ferramentas).
    p = subprocess.Popen([C.EDITOR_EXE, C.LAB_UPROJECT, "-culture=en", "-unattended"], env=amb, close_fds=True,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    with open(C.LAB_ESTADO, "w", encoding="utf-8") as f:
        json.dump({"pid": p.pid, "aberto_em": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
    while time.time() - t0 < prazo_s:
        if _responde():
            return {"ok": True, "ja_aberto": False, "pid": p.pid, "segundos": round(time.time() - t0, 1)}
        if p.poll() is not None:
            raise RuntimeError(f"o editor do laboratório fechou sozinho (código {p.returncode})")
        time.sleep(3)
    raise RuntimeError(f"o editor do laboratório não respondeu em {prazo_s:.0f} s (pid {p.pid})")


def fechar(prazo_s: float = 120.0, descartar: bool = False) -> dict:
    """Pede ao editor do laboratório para sair e espera o processo acabar. Nunca mata o processo à força.
    Com algo por salvar, o editor recusa (a não ser com descartar=True)."""
    from . import ponte
    e = estado()
    if not e["processo_vivo"] and not e["responde"]:
        return {"ok": True, "ja_fechado": True}
    with ponte.Ponte("lab-fechar") as p:
        por_salvar = p.chamar("info")["por_salvar"]
        if por_salvar and not descartar:
            raise RuntimeError(f"o laboratório tem coisas por salvar: {por_salvar}")
        try:
            p.chamar("quit_editor", descartar=descartar)
        except Exception:  # noqa: BLE001  (o editor pode cair antes de responder: o que vale é o processo sumir)
            pass
    t0 = time.time()
    while time.time() - t0 < prazo_s:
        if not _responde(1.0) and not (e["pid"] and _pid_vivo(e["pid"])):
            return {"ok": True, "ja_fechado": False, "segundos": round(time.time() - t0, 1)}
        time.sleep(2)
    raise RuntimeError("o editor do laboratório não fechou no prazo")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "estado"
    acoes = {"criar": criar, "abrir": abrir, "fechar": fechar, "estado": estado, "fechar-descartando": lambda: fechar(descartar=True)}
    print(json.dumps(acoes[modo](), ensure_ascii=False, indent=1))
