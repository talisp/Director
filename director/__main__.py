"""Porta única do Director. Entrada e saída em texto (JSON), para qualquer agente ou pessoa.

Na raiz da pasta do Director:
  venv\\Scripts\\python.exe -m director capacidades             o que dá para pedir (operações, campos, tipos de peça)
  venv\\Scripts\\python.exe -m director pecas                   cria ou atualiza as peças no laboratório
  venv\\Scripts\\python.exe -m director fazer CENA FICHA.json   aplica uma ficha ("-" lê a ficha da entrada padrão)
  venv\\Scripts\\python.exe -m director estado CENA             só leitura: planta x Unreal
  venv\\Scripts\\python.exe -m director incorporar CENA [nomes] com o Play rodando: grava no cenário onde os objetos ficaram

`capacidades` não precisa do Unreal. Os outros falam só com o editor do LABORATÓRIO, com a trava dele.
"""
import json
import os
import sys

from . import config as C
from .nucleo import executor, operacoes, pecas


def _sair(dados, codigo: int = 0) -> None:
    sys.stdout.buffer.write(json.dumps(dados, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    raise SystemExit(codigo)


def main(argv: list) -> None:
    modo = argv[0] if argv else "capacidades"
    if modo == "capacidades":
        _sair(operacoes.capacidades())
    from . import ponte  # só aqui: `capacidades` roda sem o Unreal
    pontos = os.path.join(C.WORK, "restauracao")
    with ponte.Ponte(f"director-{modo}") as p:
        if modo == "pecas":
            _sair(p.chamar("pieces_build", pecas=pecas.PECAS))
        if modo == "estado":
            _sair(executor.estado(argv[1], p, C.CENAS))
        if modo == "fazer":
            texto = sys.stdin.buffer.read().decode("utf-8") if argv[2] == "-" else open(argv[2], encoding="utf-8").read()
            try:
                ficha = json.loads(texto)
            except ValueError as e:
                _sair({"ok": False, "motivo": "recusado", "porque": f"a ficha não é JSON válido: {e}", "tocou_na_cena": False}, 2)
            res = executor.executar(argv[1], ficha, p, C.CENAS, C.LAB_DIR, pontos)
            _sair(res, 0 if res["ok"] else 2)
        if modo == "incorporar":
            res = executor.incorporar(argv[1], p, C.CENAS, C.LAB_DIR, pontos, ids=set(argv[2:]) or None)
            _sair(res, 0 if res["ok"] else 2)
    _sair({"ok": False, "porque": f"modo desconhecido: {modo}"}, 2)


if __name__ == "__main__":
    main(sys.argv[1:])
