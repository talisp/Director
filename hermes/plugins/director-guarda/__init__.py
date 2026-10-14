"""Guarda do operador do Director (complemento do Hermes, perfil `director`).

1. Perguntas: o modelo às vezes manda o argumento `questions` da ferramenta `clarify` como texto (a lista
   inteira entre aspas), ou as opções como objetos ({"label": ...}). O Hermes recusa e o formulário nunca
   chega à pessoa. Aqui o argumento é consertado antes de a ferramenta rodar.
2. Cartão de aprovação: qualquer comando de terminal que possa mudar o Unreal para e pede a aprovação da
   pessoa, com um resumo em português do que vai ser feito. A LLM não consegue pular: quem decide é o Hermes.
   Passam sem cartão só as leituras conhecidas do Director e comandos que não rodam Python nem falam com a rede.
   Sem ninguém para aprovar (modo sem tela), o comando não roda.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, Optional

# ------------------------------------------------------------------------------------------- perguntas (clarify)


def consertar_perguntas(args: Any) -> Optional[dict]:
    """Devolve os argumentos consertados da `clarify`, ou None se já estão certos (ou não dá para consertar)."""
    if not isinstance(args, dict):
        return None
    q = args.get("questions")
    mudou = False
    if isinstance(q, str):
        try:
            q = json.loads(q)
        except ValueError:
            return None
        mudou = True
    if isinstance(q, dict):
        q, mudou = [q], True
    if not isinstance(q, list):
        return None
    novas = []
    for item in q:
        if isinstance(item, str):
            try:
                item, mudou = json.loads(item), True
            except ValueError:
                item, mudou = {"question": item}, True
        if not isinstance(item, dict):
            return None
        item = dict(item)
        ops = item.get("choices")
        if isinstance(ops, str):
            try:
                ops, mudou = json.loads(ops), True
            except ValueError:
                ops = None
        if isinstance(ops, list):
            limpas = []
            for c in ops:
                if isinstance(c, dict):
                    c, mudou = str(c.get("label") or c.get("text") or c.get("value") or "").strip(), True
                limpas.append(c if isinstance(c, str) else str(c))
            item["choices"] = [c for c in limpas if c]
        novas.append(item)
    return {"questions": novas} if mudou else None


# ------------------------------------------------------------------------------------------- cartão de aprovação

_LEITURAS = re.compile(r"-m\s+director(?:\.lab)?\s+(estado|capacidades)\b")
_PYTHON = re.compile(r"(?i)(?:^|[\s/\\\"'&|;(])(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?\b")
_REDE = re.compile(r"(?i)\b(curl|wget|invoke-webrequest|invoke-restmethod|iwr|irm)\b|:80(?:01|11)\b|127\.0\.0\.1|localhost")
# configuração do próprio Hermes (desligar a trava, trocar o modelo, tirar o complemento) e o Unreal direto
_SENSIVEL = re.compile(r"(?i)appdata|[\\/]\.?hermes([\\/]|\b)|config\.ya?ml|\.env\b|\bhermes\b\s+(-p\s+\S+\s+)?(config|plugins|tools|profile|setup)|unrealeditor|\.uproject")
# onde o operador pode escrever arquivos (D40): as fichas e as propostas, dentro de work/ do Director
_PODE_ESCREVER = re.compile(r"(?i)[\\/]work[\\/](fichas|propostas)[\\/]")
_FAZER = re.compile(r"-m\s+director\s+fazer\s+(\S+)\s+(\S+)")

_ROTULO = {"largura_m": "largura", "comprimento_m": "comprimento", "altura_m": "altura", "profundidade_m": "profundidade",
           "diametro_m": "diâmetro", "posicao_m": "posição na parede", "peitoril_m": "altura da base", "x_m": "x", "y_m": "y",
           "angulo": "abertura", "giro": "giro", "parede": "parede", "sobre": "sobre", "sala": "cômodo"}


def _valor(k: str, v: Any) -> str:
    if k.endswith("_m") and isinstance(v, (int, float)):
        return f"{v:g} m"
    if k in ("angulo", "giro") and isinstance(v, (int, float)):
        return f"{v:g}°"
    return str(v)


def _campos(op: dict, fora: tuple) -> str:
    partes = [f"{_ROTULO.get(k, k)} {_valor(k, v)}" for k, v in op.items() if k not in fora]
    return f" ({', '.join(partes)})" if partes else ""


def descrever_operacao(op: Any) -> str:
    if not isinstance(op, dict):
        return f"operação estranha: {op!r}"
    nome, oid = op.get("operacao"), op.get("id")
    fora = ("operacao", "id", "tipo")
    if nome == "criar_sala":
        return f"criar o cômodo «{oid or 'novo'}»{_campos(op, fora)}"
    if nome == "mudar_sala":
        return f"mudar o cômodo «{oid or 'atual'}»{_campos(op, fora)}"
    if nome == "colocar":
        return f"colocar {op.get('tipo', '?')}{' «' + oid + '»' if oid else ''}{_campos(op, fora)}"
    if nome == "mudar":
        return f"mudar «{oid}»{_campos(op, fora)}"
    if nome == "remover":
        return f"tirar «{oid}»"
    return f"operação «{nome}»{_campos(op, ('operacao',))}"


def _ler_ficha(caminho: str, pasta: str) -> Optional[dict]:
    caminho = caminho.strip("\"'")
    if not os.path.isabs(caminho):
        caminho = os.path.join(pasta, caminho)
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


_MEXE_EM_ARQUIVO = re.compile(r"(?i)(?:^|[\s;&|(])(rm|rmdir|del|erase|mv|move|cp|copy|xcopy|robocopy|tee|git|"
                              r"remove-item|move-item|copy-item|set-content|add-content|out-file|new-item)\b|\bsed\s+-i")
_REDIRECAO = re.compile(r"(?<![0-9&<])>{1,2}\s*([\"']?)([^\s\"'&|;]+)")


def _grava_fora_do_lugar(comando: str) -> bool:
    """Redirecionamento (> arquivo) para fora de work/fichas ou work/propostas, ou comando que mexe em arquivos."""
    if _MEXE_EM_ARQUIVO.search(comando):
        return True
    for _, alvo in _REDIRECAO.findall(comando):
        if alvo.startswith("&") or alvo.lower() in ("/dev/null", "nul", "$null"):
            continue
        if not _PODE_ESCREVER.search("/" + alvo.replace("\\", "/")):
            return True
    return False


def precisa_de_aprovacao(comando: str) -> bool:
    if _REDE.search(comando) or _SENSIVEL.search(comando) or _grava_fora_do_lugar(comando):
        return True
    if not _PYTHON.search(comando) and "-m director" not in comando:
        return False
    # roda Python: só passa sem cartão se TODA chamada de Python no comando for uma leitura conhecida
    chamadas = re.split(r"&&|\|\||;|\|", comando)
    for parte in chamadas:
        if (_PYTHON.search(parte) or "-m director" in parte) and not _LEITURAS.search(parte):
            return True
    return False


def resumo_do_comando(comando: str, pasta: str) -> str:
    linhas = []
    m = _FAZER.search(comando)
    if m:
        cena, caminho = m.group(1), m.group(2)
        ficha = _ler_ficha(caminho, pasta)
        linhas.append(f"O operador quer MUDAR a cena «{cena}» no Unreal.")
        if ficha is None:
            linhas.append(f"Não consegui ler a ficha ({caminho}). Na dúvida, recuse.")
        else:
            if ficha.get("pedido"):
                linhas.append(f"Pedido: {ficha['pedido']}")
            linhas.append("O que vai ser feito:")
            for op in ficha.get("operacoes") or []:
                linhas.append(f"  - {descrever_operacao(op)}")
    elif re.search(r"-m\s+director\s+incorporar", comando):
        linhas.append("O operador quer gravar na cena onde os objetos ficaram durante o Play.")
    elif re.search(r"-m\s+director\.lab\s+(abrir|fechar|criar)", comando):
        linhas.append("O operador quer abrir, fechar ou criar o projeto do laboratório no Unreal.")
    elif re.search(r"-m\s+director\s+pecas", comando):
        linhas.append("O operador quer recriar as peças do Director no laboratório.")
    elif _SENSIVEL.search(comando):
        linhas.append("O operador quer rodar um comando que mexe na configuração do Hermes ou abre o Unreal por fora do Director.")
    elif _grava_fora_do_lugar(comando):
        linhas.append("O operador quer apagar, mover ou gravar arquivos fora das pastas de fichas e de propostas.")
    else:
        linhas.append("O operador quer rodar um comando que pode mexer no Unreal (Python ou rede), fora das leituras do Director.")
    linhas.append("")
    linhas.append(f"Comando: {comando}")
    linhas.append("Aprove só se é isso que você quer. Recusar não muda nada.")
    return "\n".join(linhas)


# ------------------------------------------------------------------------------------------- gancho do Hermes


def _pasta_do_comando(args: dict) -> str:
    return args.get("workdir") or args.get("cwd") or os.environ.get("TERMINAL_CWD") or os.getcwd()


def _antes_da_ferramenta(tool_name: str = "", args: Any = None, **_: Any) -> Optional[dict]:
    if tool_name == "clarify":
        novos = consertar_perguntas(args)
        return {"action": "modify", "args": novos} if novos else None
    if tool_name in ("write_file", "patch") and isinstance(args, dict):
        caminho = str(args.get("path") or "").replace("\\", "/")
        if not _PODE_ESCREVER.search(caminho):
            return {"action": "block", "message": (
                f"BLOQUEADO pela guarda do Director: você só pode escrever arquivos em work/fichas/ e work/propostas/ "
                f"(pedido: {caminho or 'sem caminho'}). O código do Director, a configuração do Hermes e o resto ficam "
                "como estão; mudança neles só depois da autorização do Talis, por quem faz a engenharia.")}
        return None
    if tool_name == "terminal" and isinstance(args, dict):
        comando = str(args.get("command") or "")
        if precisa_de_aprovacao(comando):
            # chave única: "sempre aprovar" no cartão nunca vale para outro comando
            chave = f"director-guarda:{uuid.uuid4().hex}"
            return {"action": "approve", "message": resumo_do_comando(comando, _pasta_do_comando(args)), "rule_key": chave}
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _antes_da_ferramenta)
