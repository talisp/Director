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
from . import consultas

COMANDOS = {
    "preparar": {"uso": "preparar CENA_NOVA PASTA_SNAPSHOT", "faz": "Prepara copia historica em novo level e planta; nao executa pedido do operador."},
    "verificar": {"uso": "verificar CENA CONSULTAS.json", "faz": "Verifica contencao por geometria fisica, raios externos e rotas; informa limites e objetos fora da planta."},
    "relatorio": {"uso": "relatorio CENA [ID ...]", "faz": "Separa plano e medidas internas reais por raios; nao abre outra cena."},
    "ensaio": {"uso": "ensaio criar NOME PEDIDO.txt | executar ID SCRIPT.py | listar [ID]", "faz": "Registra pedido, copia exata/hash do script, resultado/erro e diferencas do inventario; usa a ponte e trava existentes."},
    "capacidades": {"uso": "capacidades", "faz": "Contrato das fichas, campos e padroes; sem Unreal."},
    "fazer": {"uso": "fazer CENA FICHA.json|-", "faz": "Cria a cena automaticamente se for nova; aplica, confere e salva a ficha."},
    "estado": {"uso": "estado CENA", "faz": "Resumo das diferencas entre planta e Unreal; somente leitura."},
    "observar": {"uso": "observar CENA [ID ...]", "faz": "Objetos planejados e caixas reais; um ID de sala inclui seu conteudo. Nao abre outro level."},
    "medir": {"uso": "medir CENA CONSULTAS.json|-", "faz": "Medidas do motor no level aberto. Coordenadas em cm; tipos: raio, varredura, caminho, nav.",
              "entrada": {"consultas": [{"tipo": "caminho", "de": [200, 200, 1], "ate": [930, 200, 1]}], "mundo": "editor"},
              "capsula": "varredura: raio=34, meia_altura=88 cm; de/ate sao CENTROS. O topo e centro.z + meia_altura. Ajuste ao personagem e ao vao.",
              "criterios": "caminho.completo requer existe e nao parcial; varredura.livre nao prova navegacao. nav.pronta nao prova conectividade."},
    "assets": {"uso": "assets TERMO [TERMO ...]", "faz": "Busca por nomes/caminhos em /Game, sem carregar assets. Use sinonimos, como cadeira chair seat. Nao consulta o Fab externo."},
    "pecas": {"uso": "pecas", "faz": "Cria ou atualiza os Blueprints do Director no laboratorio."},
    "incorporar": {"uso": "incorporar CENA [ID ...]", "faz": "Durante o Play, incorpora as alteracoes fisicas ao cenario salvo."},
}


def _ajuda(comando=None):
    if comando:
        if comando not in COMANDOS:
            return {"ok": False, "motivo": "uso_invalido", "porque": f"comando desconhecido: {comando}"}
        return {"ok": True, "comando": comando, **COMANDOS[comando]}
    return {"ok": True, "ajuda": "python -m director COMANDO --help", "comandos": COMANDOS,
            "laboratorio": "python -m director.lab --help", "projeto": "um unico Director; os ensaios sao cenas"}


def _ler_json(caminho):
    if caminho == "-":
        return json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
    with open(caminho, encoding="utf-8-sig") as f:
        return json.load(f)


def _sair(dados, codigo: int = 0) -> None:
    # JSON ASCII compacto evita perda de acentos na decodificacao do terminal do Hermes no Windows.
    sys.stdout.buffer.write(json.dumps(dados, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n")
    raise SystemExit(codigo)


def main(argv: list) -> None:
    if argv and (argv[0] in ("ajuda", "--help", "-h") or any(a in ("--help", "-h") for a in argv[1:])):
        nome = (argv[1] if len(argv) > 1 else None) if argv[0] in ("ajuda", "--help", "-h") else argv[0]
        ajuda = _ajuda(nome)
        _sair(ajuda, 0 if ajuda["ok"] else 2)
    modo = argv[0] if argv else "capacidades"
    if modo == "ensaio":
        from . import ensaios
        try:
            r = ensaios.cli(argv[1:])
        except Exception as e:
            r = {"ok": False, "motivo": "ensaio", "porque": str(e)}
        _sair(r, 0 if r.get("ok") else 2)
    aridade = {"capacidades": (0, 0), "pecas": (0, 0), "fazer": (2, 2), "estado": (1, 1),
               "observar": (1, None), "medir": (2, 2), "assets": (1, None), "incorporar": (1, None), "relatorio": (1, None), "verificar": (2, 2), "preparar": (2, 2)}
    if modo not in aridade:
        _sair(_ajuda(modo), 2)
    minimo, maximo = aridade[modo]
    n = max(0, len(argv) - 1)
    if n < minimo or (maximo is not None and n > maximo):
        _sair({"ok": False, "motivo": "uso_invalido", **COMANDOS[modo]}, 2)
    if modo == "capacidades":
        _sair({**operacoes.capacidades(), "comandos": COMANDOS})
    try:
        entrada = _ler_json(argv[2]) if modo in ("fazer", "medir", "verificar") else None
    except (ValueError, OSError) as e:
        _sair({"ok": False, "motivo": "entrada_invalida", "porque": str(e), "tocou_na_cena": False}, 2)
    from . import ponte  # só aqui: `capacidades` roda sem o Unreal
    pontos = os.path.join(C.WORK, "restauracao")
    try:
        with ponte.Ponte(f"director-{modo}") as p:
            if modo == "pecas":
                res = p.chamar("pieces_build", pecas=pecas.PECAS)
            elif modo == "preparar":
                from . import preparacao
                res = preparacao.preparar(argv[1],argv[2],p)
            elif modo == "estado":
                res = executor.estado(argv[1], p, C.CENAS)
            elif modo == "observar":
                res = consultas.observar(argv[1], p, C.CENAS, argv[2:])
            elif modo == "relatorio":
                from . import relatorio
                res = relatorio.consultar(argv[1], p, C.CENAS, argv[2:] or None)
            elif modo == "medir":
                res = consultas.medir(argv[1], entrada, p, C.CENAS)
            elif modo == "verificar":
                from . import verificacao
                res = verificacao.verificar(argv[1], entrada, p)
            elif modo == "assets":
                res = p.chamar("assets_find", termos=argv[1:])
            elif modo == "fazer":
                res = executor.executar(argv[1], entrada, p, C.CENAS, C.LAB_DIR, pontos)
            else:
                res = executor.incorporar(argv[1], p, C.CENAS, C.LAB_DIR, pontos, ids=set(argv[2:]) or None)
            _sair(res, 0 if res.get("ok", True) else 2)
    except Exception as e:  # erro estruturado para o agente, sem confundir com sucesso ou com cena intacta
        _sair({"ok": False, "motivo": "erro", "porque": f"{type(e).__name__}: {e}"}, 2)


if __name__ == "__main__":
    main(sys.argv[1:])
