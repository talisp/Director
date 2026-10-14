"""Auxiliar de desenvolvimento: `-m director.dev op NOME [json]`, `reload`, ou `py ARQUIVO` (roda o arquivo no editor
do laboratório; o que ele puser na variável `resultado` volta impresso)."""
import json
import sys

from . import ponte

with ponte.Ponte("claude-dev") as p:
    if sys.argv[1] == "op":
        saida = p.chamar(sys.argv[2], **json.loads(sys.argv[3] if len(sys.argv) > 3 else "{}"))
    elif sys.argv[1] == "reload":
        saida = p.recarregar()
    else:
        with open(sys.argv[2], encoding="utf-8") as f:
            saida = p.chamar("dev_exec", codigo=f.read())
    sys.stdout.buffer.write(json.dumps(saida, ensure_ascii=False, indent=1)[:12000].encode("utf-8", "replace") + b"\n")
