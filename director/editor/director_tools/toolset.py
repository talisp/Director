"""Porta única do Director dentro do editor: três ferramentas.

Quem chama é o núcleo (programa), não a LLM. Por isso a interface é pequena e estável: `op(nome, argumentos)` despacha
para as operações de ops.py, que usam a automação do próprio Unreal (ferramenta de Blueprint da Epic, subsistemas do
editor, traçados de colisão, navegação). Acrescentar uma operação não muda o cadastro do toolset.
"""
import importlib
import json
import sys
import traceback
from typing import Any

import unreal

toolset_registry: Any = importlib.import_module("toolset_registry")


def _j(**kw) -> str:
    return json.dumps(kw, ensure_ascii=False, separators=(",", ":"))


@unreal.uclass()
class DirectorTools(unreal.ToolsetDefinition):
    """Director (laboratório): constrói e mede cenários funcionais com peças paramétricas."""

    @toolset_registry.tool_call
    @staticmethod
    def op(name: str, args_json: str) -> str:
        """Executa uma operação do Director.

        Args:
            name: nome da operação (ver `ops` em op("info", "{}")).
            args_json: argumentos da operação, como objeto JSON em texto.

        Returns:
            JSON com `ok` e o resultado; em erro, `ok=false`, `erro` e o rastro.
        """
        try:
            ops = importlib.import_module("director_tools.ops")
            fn = ops.OPS.get(name)
            if fn is None:
                return _j(ok=False, erro=f"operacao_desconhecida: {name}", ops=sorted(ops.OPS))
            res = fn(**json.loads(args_json or "{}"))
            return _j(ok=True, **(res if isinstance(res, dict) else {"valor": res}))
        except Exception as e:  # noqa: BLE001
            return _j(ok=False, erro=f"{type(e).__name__}: {e}", rastro=traceback.format_exc()[-1500:])

    @toolset_registry.tool_call
    @staticmethod
    def reload() -> str:
        """Recarrega do disco só o código das operações (ops.py e o que ele importa), sem reiniciar o editor
        e sem mudar o cadastro do toolset.

        Returns:
            JSON com os módulos recarregados.
        """
        nomes = [m for m in sys.modules if m.startswith("director_tools.") and not m.endswith(".toolset")]
        for m in nomes:
            del sys.modules[m]
        importlib.import_module("director_tools.ops")
        return _j(ok=True, recarregados=sorted(nomes))
