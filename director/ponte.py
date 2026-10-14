"""Ponte protegida até o editor do LABORATÓRIO.

Reaproveita do Antigo Director a trava (base/trava.py) e o cliente do servidor de ferramentas
(base/mcp_client.py). O que é novo:
- trava própria do laboratório (não disputa com o projeto do filme);
- endereço fixo na porta do laboratório: a 8001 (projeto do filme) é recusada;
- antes da primeira chamada, confere que o editor conectado é o projeto de laboratório. Se não for, recusa.
"""
import json
import os
import re

from . import config as C
from .base import mcp_client, trava


class Recusado(RuntimeError):
    """A ponte se recusou a falar com o editor (proteção)."""


def _mesma_pasta(a: str, b: str) -> bool:
    def norm(p):
        return os.path.normcase(os.path.normpath(p)).rstrip("\\/")
    return norm(a) == norm(b)


def conferir_laboratorio(info: dict, lab_dir: str = "") -> None:
    """Recusa qualquer editor cuja pasta de projeto não seja a do laboratório."""
    lab_dir = lab_dir or C.LAB_DIR
    pasta = str(info.get("projeto_dir") or "")
    if not pasta or not _mesma_pasta(pasta, lab_dir):
        raise Recusado(f"o editor conectado não é o laboratório (projeto em {pasta!r}; esperado {lab_dir!r}): nada foi feito")


def conferir_endereco(url: str) -> None:
    if ":8001/" in url or url.rstrip("/").endswith(":8001"):
        raise Recusado("a porta 8001 é a do projeto do filme: o Director não fala com ela")


class Ponte:
    """Uso: `with Ponte("quem") as p: p.chamar("info")`. Pega a trava do laboratório e confere o projeto."""

    def __init__(self, nome: str, url: str = "", cliente=None):
        self.nome = nome
        self.url = url or C.LAB_URL
        conferir_endereco(self.url)
        self.cliente = cliente or mcp_client.Client(url=self.url, timeout=120)
        self._toolset = None
        self._conferido = False

    def __enter__(self):
        os.makedirs(C.WORK, exist_ok=True)
        trava.pegar(C.TRAVA, self.nome, C.TRAVA_LOG)
        return self

    def __exit__(self, *_):
        trava.soltar(C.TRAVA)
        return False

    def _achar_toolset(self) -> str:
        if self._toolset is None:
            # no catálogo o nome vem como "PythonTypes.DirectorTools_0x..." (visto ao vivo em 13/10)
            nomes = re.findall(r"[\w.]*DirectorTools\w*", self.cliente.list_toolsets())
            if not nomes:
                raise Recusado("o DirectorTools não está carregado neste editor")
            self._toolset = sorted(nomes)[-1]
        return self._toolset

    def _op(self, nome: str, args: dict) -> dict:
        res = self.cliente.call(self._achar_toolset(), "op", name=nome, args_json=json.dumps(args, ensure_ascii=False))
        if isinstance(res, str):
            res = json.loads(res)
        return res

    def chamar(self, nome: str, **args) -> dict:
        """Chama uma operação do editor. Erro da operação vira exceção com o texto do editor."""
        if not self._conferido:
            conferir_laboratorio(self._op("info", {}))
            self._conferido = True
        res = self._op(nome, args)
        if not res.get("ok"):
            raise mcp_client.UnrealError(f"{nome}: {res.get('erro')}\n{res.get('rastro', '')}")
        return res

    def recarregar(self) -> dict:
        res = self.cliente.call(self._achar_toolset(), "reload")
        return json.loads(res) if isinstance(res, str) else res

    def script(self, codigo: str):
        """Roda um script solto no editor pela ferramenta da Epic (uso: desenvolvimento e simular uma edição manual
        "por fora do Director"). Também confere o projeto antes."""
        if not self._conferido:
            conferir_laboratorio(self._op("info", {}))
            self._conferido = True
        return self.cliente.script(codigo)
