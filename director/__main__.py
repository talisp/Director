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
    "acervo": {"uso":"acervo iniciar | resumo | buscar TERMO | pedido JSON|- | coletar JSON", "faz":"SQL em R:\\CINF\\BD; coleta incremental de arquivos ou leitura do laboratorio, com historico e retomada. Nao baixa modelos nem altera a cena."},
    "contexto": {"uso": "contexto", "faz": "Leitura: identifica level aberto, cena e fonte de plantas; nao escolhe sala fixa nem troca level."},
    "vincular": {"uso": "vincular PASTA_CENAS", "faz": "Valida todas as plantas no laboratorio salvo, preserva as fontes e ativa estado compartilhado entre checkouts. Nao escolhe maior revisao nem altera atores."},
    "planta2d": {"uso":"planta2d CENA SALA", "faz":"Filtro offline de contencao, areas livres e regioes de passagem; sem Unreal."},
    "api": {"uso":"api atualizar [PEDIDO.json] | api TERMO", "faz":"Exporta referencia instalada e consulta offline em trechos curtos."},
    "biblioteca": {"uso":"biblioteca indexar PEDIDO.json | biblioteca TERMO", "faz":"Inspeciona e consulta arquivos locais sem Unreal; nao decide banco permanente."},
    "navegacao": {"uso":"navegacao [PEDIDO.json]", "faz":"Diagnostica, reconstruir sem mudar perfis, ajustar com escopo/tile_cm explicitos e backup, restaurar incluindo tile. Aguarda carga ate prazo_s (maximo 60); pronta nao prova chegada."},
    "planejar": {"uso": "planejar CENA PEDIDO.json", "faz": "Propoe mobiliario ou salas retangulares com adjacencias no mesmo CP-SAT; devolve ficha_salas sem alterar o editor."},
    "procurar": {"uso": "procurar TERMO [TERMO ...] | procurar consultar PEDIDO.json", "faz": "Atualiza e consulta cena, projeto e indice offline com sinonimos PT/EN; poucos candidatos e cena primeiro."},
    "catalogo": {"uso": "catalogo atualizar", "faz": "Gera indice local dos metadados atuais sem imprimir todo o catalogo."},
    "objeto": {"uso": "objeto CENA PEDIDO.json", "faz": "Adota, duplica, compoe ou coloca StaticMesh com identidade na planta e perfil fisico ajustavel."},
    "apoios": {"uso":"apoios CENA PEDIDO.json", "faz":"Consulta pegada largura_m/profundidade_m em objeto registrado; cinco raios por candidato. niveis:true e altura_m consultam prateleiras internas por amostragem/normal/folga. Retorna apoio_z_m para objeto sobre o apoio; nao certifica toda malha."},
    "revisar": {"uso":"revisar CENA PEDIDO.json", "faz":"Avaliar ou iniciar/corrigir/concluir revisao com seis notas justificadas, medidas frescas, perguntas de completude, tres rodadas e recuo da piora. Nao troca level; correcoes devem passar por este comando para detectar interferencias.",
        "entrada":{"acao":"avaliar | iniciar | corrigir | concluir | estado","origem":"sessao/modelo ou usuario; obrigatorio ao pontuar","pedido":"frase humana; obrigatorio ao iniciar","tipos":{"quarto1":"quarto"},"notas":{k:{"nota":"0..10","justificativa":"frase com evidencia/limite"} for k in ('realismo','funcao','arrumacao','completude','seguiu_pedido','passagem')},"ficha":"somente corrigir; ficha normal","verificar":"opcoes normais de verificar; medidas sempre consultadas de novo","dispensados":["quarto1.janela (somente apos decisao humana)"]}},
    'material':{'uso':'material CENA PEDIDO.json','faz':'Seleciona material existente por nome PT/EN ou caminho explicito, confere classe nativa, aplica e verifica com executor. Sem download automatico. Campos: sala, alvo(piso/teto/parede_norte/sul/leste/oeste/ paredes), descricao, caminho opcional.'},
    "preparar": {"uso": "preparar CENA_NOVA PASTA_SNAPSHOT", "faz": "Prepara copia historica em novo level e planta; nao executa pedido do operador."},
    "verificar": {"uso": "verificar CENA CONSULTAS.json", "faz": "Verifica contencao por geometria fisica, raios externos e rotas; informa limites e objetos fora da planta."},
    "relatorio": {"uso": "relatorio CENA [ID ...]", "faz": "Separa plano e medidas internas reais por raios; nao abre outra cena."},
    "ensaio": {"uso": "ensaio criar NOME PEDIDO.txt | executar ID SCRIPT.py | listar [ID]", "faz": "Registra pedido, copia exata/hash do script, resultado/erro e diferencas do inventario; usa a ponte e trava existentes.",
               "retorno": "No script do editor, atribua resultado = {...}; print sozinho nao e devolvido ao agente. Nao invente chamadas de API: consulte api TERMO antes. Para inventario, use observar/estado/procurar antes de escrever script."},
    "capacidades": {"uso": "capacidades", "faz": "Contrato das fichas, campos e padroes; sem Unreal."},
    "fazer": {"uso": "fazer CENA FICHA.json|-", "faz": "Cria a cena automaticamente se for nova; aplica, confere e salva a ficha."},
    "estado": {"uso": "estado CENA", "faz": "Resumo das diferencas entre planta e Unreal; somente leitura."},
    "observar": {"uso": "observar CENA [ID ...] | observar CENA --texto [SALA] [--real]", "faz": "Objetos planejados e caixas reais; --texto e offline; --texto --real concilia moveis em memoria com o inventario, mantendo estrutura planejada explicita. Nao grava nem abre outro level."},
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
    if argv and any(a in ('--help','-h') for a in argv):
        nome=argv[0] if argv[0] not in ('--help','-h') else None
        r=_ajuda(nome);_sair(r,0 if r['ok'] else 2)
    if argv and argv[0]=='acervo':
        from . import acervo
        try:
            r=acervo.cli(argv[1:]);_sair(r,0 if r.get('ok') else 2)
        except Exception as e:_sair({'ok':False,'porque':str(e)},2)
    if argv and argv[0]=='observar' and '--texto' in argv:
        from . import planta_texto
        try:
            extras=[a for a in argv[3:] if a!='--real']
            if len(argv)<3 or argv[2]!='--texto' or len(extras)>1 or argv.count('--real')>1 or any(a.startswith('--') for a in extras):
                raise ValueError('uso: observar CENA --texto [SALA] [--real]')
            r=planta_texto.cli(argv[1],extras[0] if extras else None,real='--real' in argv);_sair(r)
        except Exception as e:_sair({'ok':False,'porque':str(e)},2)
    if argv and argv[0]=='planta2d':
        from . import espaco2d
        try:
            if len(argv)!=3:raise ValueError('uso: planta2d CENA SALA')
            r=espaco2d.cli(argv[1:]);_sair(r,0 if r.get('ok') else 2)
        except Exception as e:_sair({'ok':False,'porque':str(e)},2)
    if argv and argv[0] == 'vincular':
        from . import estado_local, ponte
        try:
            if len(argv) != 2:raise ValueError('uso: vincular PASTA_CENAS')
            with ponte.Ponte('director-vincular') as p:
                r = estado_local.vincular(argv[1], p, C.LAB_DIR, C.VINCULO_CENAS)
            _sair(r, 0 if r.get('ok') else 2)
        except Exception as e:_sair({'ok':False,'porque':str(e),'vinculo_ativado':False},2)
    if argv and argv[0]=='biblioteca':
        from . import biblioteca
        try:
            r=biblioteca.cli(argv[1:]);_sair(r,0 if r.get('ok') else 2)
        except Exception as e:_sair({'ok':False,'porque':str(e)},2)
    if argv and argv[0]=='api':
        from . import api
        try:
            r=api.cli(argv[1:]);_sair(r,0 if r.get('ok') else 2)
        except Exception as e:_sair({'ok':False,'porque':str(e)},2)
    if argv and argv[0]=='navegacao':
        from . import navegacao,ponte
        try:
            pedido=_ler_json(argv[1]) if len(argv)==2 else {'acao':'diagnosticar'}
            with ponte.Ponte('director-navegacao') as p:r=navegacao.executar(pedido,p)
            _sair(r,0 if r.get('ok') else 2)
        except Exception as e:_sair({'ok':False,'porque':str(e)},2)
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
    aridade = {"contexto": (0, 0), "capacidades": (0, 0), "pecas": (0, 0), "fazer": (2, 2), "estado": (1, 1),
               "observar": (1, None), "medir": (2, 2), "assets": (1, None), "incorporar": (1, None), "relatorio": (1, None), "verificar": (2, 2), "preparar": (2, 2), "objeto": (2, 2), "apoios": (2,2), "revisar": (2,2), "material": (2,2), "procurar": (1,None), "catalogo": (1,1), "planejar": (2,2)}
    if modo not in aridade:
        _sair(_ajuda(modo), 2)
    minimo, maximo = aridade[modo]
    n = max(0, len(argv) - 1)
    if n < minimo or (maximo is not None and n > maximo):
        _sair({"ok": False, "motivo": "uso_invalido", **COMANDOS[modo]}, 2)
    if modo == "capacidades":
        _sair({**operacoes.capacidades(), "comandos": COMANDOS})
    try:
        entrada = _ler_json(argv[2]) if modo in ("fazer", "medir", "verificar", "objeto", "apoios", "revisar", "material", "planejar") else None
    except (ValueError, OSError) as e:
        _sair({"ok": False, "motivo": "entrada_invalida", "porque": str(e), "tocou_na_cena": False}, 2)
    if modo == "planejar" and isinstance(entrada, dict) and (not entrada.get("sala") or any(
            k in entrada for k in ("dimensoes_cm", "minimo_cm", "maximo_cm"))):
        # Tamanho hipotetico: so a planta e o solver, sem abrir a ponte nem tocar na cena.
        from . import planejamento, veredito
        try:
            res = planejamento.planejar(argv[1], entrada, None)
        except Exception as e:
            res = {"ok": False, "motivo": "erro", "porque": f"{type(e).__name__}: {e}"}
        _sair(veredito.com_veredito(modo, res), 0 if res.get("ok") else 2)
    from . import ponte  # só aqui: `capacidades` roda sem o Unreal
    pontos = os.path.join(C.WORK, "restauracao")
    try:
        with ponte.Ponte(f"director-{modo}") as p:
            if modo == "contexto":
                info = p.chamar('info')
                prefixo = '/Game/Director/Cenas/L_'
                cena = info['level'][len(prefixo):] if info['level'].startswith(prefixo) else None
                from .nucleo import planta as PL
                res = {'ok': True, 'level': info['level'], 'cena': cena, 'fonte_plantas': C.CENAS,
                       'planta': PL.caminho(C.CENAS, cena) if cena else None,
                       'planta_existe': bool(cena and os.path.isfile(PL.caminho(C.CENAS, cena))),
                       'em_play': info['em_play'], 'por_salvar': info.get('por_salvar', [])}
            elif modo == "pecas":
                res = p.chamar("pieces_build", pecas=pecas.PECAS)
            elif modo == "procurar":
                from . import catalogo
                res = catalogo.cli(argv[1:],p)
            elif modo == "catalogo":
                from . import catalogo
                if argv[1]!='atualizar':raise ValueError('uso: catalogo atualizar')
                res=catalogo.atualizar(p);res.pop('dados',None)
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
            elif modo == "objeto":
                from . import objetos
                res = objetos.fazer(argv[1],entrada,p)
            elif modo=='apoios':
                from . import objetos
                res=objetos.apoios(argv[1],entrada,p)
            elif modo=='revisar':
                from . import revisao
                res=revisao.executar(argv[1],entrada,p)
            elif modo=='material':
                from . import materiais
                res=materiais.executar(argv[1],entrada,p)
            elif modo == "planejar":
                from . import planejamento
                res = planejamento.planejar(argv[1],entrada,p)
            elif modo == "assets":
                res = p.chamar("assets_find", termos=argv[1:])
            elif modo == "fazer":
                res = executor.executar(argv[1], entrada, p, C.CENAS, C.LAB_DIR, pontos)
            else:
                res = executor.incorporar(argv[1], p, C.CENAS, C.LAB_DIR, pontos, ids=set(argv[2:]) or None)
            if modo in ("planejar", "verificar"):
                from . import veredito
                res = veredito.com_veredito(modo, res)
            from .diagnosticos import resumo
            res['diagnosticos'] = resumo(p.diagnosticos)
            _sair(res, 0 if res.get("ok", True) else 2)
    except Exception as e:  # erro estruturado para o agente, sem confundir com sucesso ou com cena intacta
        res = {"ok": False, "motivo": "erro", "porque": f"{type(e).__name__}: {e}"}
        if 'p' in locals():
            from .diagnosticos import resumo
            res['diagnosticos'] = resumo(p.diagnosticos)
        if modo in ("planejar", "verificar"):
            from . import veredito
            res = veredito.com_veredito(modo, res)
        _sair(res, 2)


if __name__ == "__main__":
    main(sys.argv[1:])
