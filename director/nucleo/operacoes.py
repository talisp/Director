"""Operações do núcleo: o que uma ficha pode pedir. Tudo aqui é conta e regra, sem Unreal e sem LLM.

Uma FICHA é texto estruturado (JSON): {"pedido": "a frase da pessoa", "operacoes": [{"operacao": ..., campos...}]}.
Quem preenche a ficha é a LLM (ou uma pessoa). O núcleo confere cada campo, recusa o que não fecha e devolve a
planta nova. A ficha vale inteira ou não vale: se uma operação é recusada, nada muda.

Medidas na ficha: metros e graus (o que uma pessoa diz). Na planta: centímetros e graus (o que o Unreal usa).
"""
import copy
import math

LADOS = ("sul", "norte", "leste", "oeste")
OPOSTA = {"sul": "norte", "norte": "sul", "leste": "oeste", "oeste": "leste"}
FOLGA_VAO = 10.0  # cm entre um vão e o canto da parede
FOLGA_ENTRE_VAOS = 20.0
FOLGA_MOVEL = 5.0  # cm entre um móvel e a parede
FOLGA_APOIO = 0.1  # cm entre o objeto e o tampo ao colocar (ele assenta sozinho quando a física liga)

PADROES = {
    "sala": {"altura": 270.0, "parede": 15.0},
    "porta": {"largura": 100.0, "altura": 210.0, "angulo": 0.0, "parede": "sul"},
    "janela": {"largura": 120.0, "altura": 110.0, "peitoril": 90.0, "parede": "leste"},
    "mesa": {"largura": 120.0, "profundidade": 80.0, "altura": 75.0, "giro": 0.0},
    "prato": {"diametro": 24.0, "altura": 2.0},
    "copo": {"diametro": 8.0, "altura": 10.0},
}
VAOS = ("porta", "janela")
MOVEIS = ("mesa",)
OBJETOS = ("prato", "copo")
# onde o próximo objeto vai sobre o tampo, em fração da meia largura e da meia profundidade
VAGAS = ((-0.5, 0.0), (0.5, 0.0), (0.0, 0.0), (-0.5, -0.5), (0.5, -0.5), (-0.5, 0.5), (0.5, 0.5), (0.0, -0.5), (0.0, 0.5))


class Invalida(ValueError):
    """A ficha pede algo que não fecha. A mensagem é para a pessoa (ou para a LLM tentar de novo)."""


NUM, TXT = "numero", "texto"
# campo -> (tipo, obrigatório, explicação). É isto que o agente lê em `capacidades`.
OPERACOES: dict = {
    "criar_sala": {
        "descricao": "Cria uma sala retangular (piso, quatro paredes e área onde um personagem pode andar). Cômodo é sala: "
                     "corredor, quarto, banheiro, armário. Para encostar numa sala que já existe, deixe 0,15 m (uma "
                     "parede) entre o lado de dentro de uma e o da outra: a parede fica em comum, e uma porta nela "
                     "é a passagem de um cômodo para o outro.",
        "campos": {"id": (TXT, False, "nome da sala; se faltar, o núcleo dá um (sala1, sala2...)"),
                   "largura_m": (NUM, True, "medida interna no eixo leste-oeste, em metros"),
                   "comprimento_m": (NUM, True, "medida interna no eixo sul-norte, em metros"),
                   "altura_m": (NUM, False, "pé-direito; padrão 2,7"),
                   "x_m": (NUM, False, "canto sudoeste (fixo); padrão 0"), "y_m": (NUM, False, "canto sudoeste; padrão 0")},
    },
    "mudar_sala": {
        "descricao": "Muda as medidas de uma sala. O canto sudoeste fica onde está; móveis e vãos não saem do lugar.",
        "campos": {"id": (TXT, False, "sala; pode faltar se só existe uma"),
                   "largura_m": (NUM, False, ""), "comprimento_m": (NUM, False, ""), "altura_m": (NUM, False, "")},
    },
    "colocar": {
        "descricao": "Coloca uma peça: porta ou janela numa parede; mesa no chão da sala; prato ou copo sobre uma mesa.",
        "campos": {"tipo": (TXT, True, "porta | janela | mesa | prato | copo"),
                   "id": (TXT, False, "nome; se faltar, o núcleo dá um (porta1, mesa1...)"),
                   "sala": (TXT, False, "pode faltar se só existe uma"),
                   "parede": (TXT, False, "porta e janela: sul | norte | leste | oeste"),
                   "posicao_m": (NUM, False, "porta e janela: centro do vão ao longo da parede, a partir do canto oeste "
                                             "(paredes sul e norte) ou sul (leste e oeste); padrão: meio da parede"),
                   "largura_m": (NUM, False, ""), "altura_m": (NUM, False, ""),
                   "peitoril_m": (NUM, False, "janela: altura da base do vão"),
                   "angulo": (NUM, False, "porta: 0 fechada, 90 aberta"),
                   "x_m": (NUM, False, "mesa: posição do centro, medida do canto sudoeste da sala; padrão: meio da sala"),
                   "y_m": (NUM, False, ""), "giro": (NUM, False, "mesa: graus"),
                   "profundidade_m": (NUM, False, "mesa"),
                   "sobre": (TXT, False, "prato e copo: a mesa; pode faltar se só existe uma"),
                   "diametro_m": (NUM, False, "prato e copo")},
    },
    "mudar": {
        "descricao": "Muda uma peça que já existe, pelo nome. Só os campos dados mudam.",
        "campos": {"id": (TXT, True, "nome da peça"),
                   "parede": (TXT, False, "porta e janela: sul | norte | leste | oeste | oposta"),
                   "posicao_m": (NUM, False, ""), "largura_m": (NUM, False, ""), "altura_m": (NUM, False, ""),
                   "peitoril_m": (NUM, False, ""), "angulo": (NUM, False, "porta: 0 fechada, 90 aberta"),
                   "x_m": (NUM, False, "mesa: medido do canto sudoeste da sala"), "y_m": (NUM, False, ""),
                   "giro": (NUM, False, ""), "profundidade_m": (NUM, False, ""), "diametro_m": (NUM, False, "")},
    },
    "remover": {
        "descricao": "Remove uma peça pelo nome (uma sala só sai depois de vazia).",
        "campos": {"id": (TXT, True, "nome da peça")},
    },
}


def capacidades() -> dict:
    """O que o núcleo sabe fazer, em texto simples, para qualquer agente."""
    return {"ficha": {"pedido": "a frase da pessoa (opcional)", "operacoes": "lista de operações, aplicadas em ordem; ou tudo ou nada"},
            "unidades": "metros e graus",
            "operacoes": {nome: {"descricao": o["descricao"],
                                 "campos": {c: {"tipo": t, "obrigatorio": ob, "nota": nota} for c, (t, ob, nota) in o["campos"].items()}}
                          for nome, o in OPERACOES.items()},
            "tipos_de_peca": {t: {k: v for k, v in p.items()} for t, p in PADROES.items()}}


# ------------------------------------------------------------------------------------------------------- conferir a ficha

def _conferir_campos(op: dict) -> dict:
    nome = op.get("operacao")
    if nome not in OPERACOES:
        raise Invalida(f"operação desconhecida: {nome!r}. Existem: {', '.join(OPERACOES)}")
    campos = OPERACOES[nome]["campos"]
    dados = {k: v for k, v in op.items() if k != "operacao" and v is not None}
    for k, v in dados.items():
        if k not in campos:
            raise Invalida(f"{nome}: campo desconhecido {k!r}. Campos: {', '.join(campos)}")
        if campos[k][0] == NUM:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise Invalida(f"{nome}: {k} tem de ser um número (veio {v!r})")
        elif not isinstance(v, str) or not v.strip():
            raise Invalida(f"{nome}: {k} tem de ser um texto (veio {v!r})")
    for k, (_, obrig, _) in campos.items():
        if obrig and k not in dados:
            raise Invalida(f"{nome}: falta o campo {k!r}")
    return dados


def _cm(d: dict, campo: str, padrao=None):
    return float(d[campo]) * 100.0 if campo in d else padrao


def _novo_id(planta: dict, tipo: str) -> str:
    n = 1
    while f"{tipo}{n}" in planta["objetos"]:
        n += 1
    return f"{tipo}{n}"


def _id_livre(planta: dict, d: dict, tipo: str) -> str:
    oid = d.get("id") or _novo_id(planta, tipo)
    if not all(ch.isalnum() or ch == "_" for ch in oid):
        raise Invalida(f"nome inválido: {oid!r} (use letras, números e _)")
    if oid in planta["objetos"]:
        raise Invalida(f"já existe uma peça chamada {oid!r}")
    return oid


def _unico(planta: dict, tipos: tuple, pedido, o_que: str) -> str:
    """Resolve 'a sala' / 'a mesa' quando o nome não veio: só vale se existe exatamente uma."""
    if pedido:
        if pedido not in planta["objetos"] or planta["objetos"][pedido]["tipo"] not in tipos:
            raise Invalida(f"não existe {o_que} chamada {pedido!r}")
        return pedido
    achados = [i for i, o in planta["objetos"].items() if o["tipo"] in tipos]
    if len(achados) != 1:
        raise Invalida(f"diga qual {o_que}: existem {len(achados)} ({', '.join(achados) or 'nenhuma'})")
    return achados[0]


def lado_cm(sala: dict, parede: str) -> float:
    """Comprimento interno da parede."""
    return sala["largura"] if parede in ("sul", "norte") else sala["comprimento"]


# ------------------------------------------------------------------------------------------------------- paredes no chão

EPS = 0.01  # cm: medidas que diferem menos que isto são a mesma


def faixa_da_parede(s: dict, lado: str) -> tuple:
    """Retângulo (x0, y0, x1, y1) que a parede ocupa no chão. As paredes sul e norte cobrem os cantos."""
    t, x, y, L, C = s["parede"], s["x"], s["y"], s["largura"], s["comprimento"]
    return {"sul": (x - t, y - t, x + L + t, y), "norte": (x - t, y + C, x + L + t, y + C + t),
            "oeste": (x - t, y, x, y + C), "leste": (x + L, y, x + L + t, y + C)}[lado]


def _linha(s: dict, lado: str) -> tuple:
    """(chave da faixa, início, fim). Paredes com a mesma chave ocupam a mesma faixa do chão: são a mesma parede.
    Início e fim são no mundo, ao longo da parede (x nas paredes sul e norte, y nas leste e oeste)."""
    x0, y0, x1, y1 = faixa_da_parede(s, lado)
    if lado in ("sul", "norte"):
        return ("x", round(y0, 2), round(y1, 2)), x0, x1
    return ("y", round(x0, 2), round(x1, 2)), y0, y1


def vao_no_mundo(planta: dict, o: dict) -> tuple:
    """(chave da faixa, início, fim) do vão de uma porta ou janela, no mundo."""
    s = planta["objetos"][o["sala"]]
    chave, _, _ = _linha(s, o["parede"])
    centro = (s["x"] if o["parede"] in ("sul", "norte") else s["y"]) + o["posicao"]
    return chave, centro - o["largura"] / 2, centro + o["largura"] / 2


def trechos_de_parede(planta: dict) -> list:
    """As paredes que vão para o Unreal. Paredes de salas diferentes na mesma faixa (salas encostadas a uma parede de
    distância) viram uma parede só, a parede em comum; uma porta nela é a passagem de uma sala para a outra.
    Cada trecho: {sala, lado, chave, ini, fim, altura, vaos: [id]}. O trecho é da primeira sala (em
    ordem alfabética) que tem parede nele; onde as salas têm alturas diferentes, a parede tem a da mais alta."""
    objs = planta["objetos"]
    sids = sorted(i for i, o in objs.items() if o["tipo"] == "sala")
    em_pe = [(sid, faixa_da_parede(objs[sid], l)) for sid in sids for l in ("leste", "oeste")]
    linhas = {}
    for sid in sids:
        for lado in LADOS:
            chave, a, b = _linha(objs[sid], lado)
            if lado in ("sul", "norte"):
                # o canto que a parede sul ou norte cobre sai se a parede leste ou oeste de outra sala já passa por ali
                t, (_, y0, _, y1) = objs[sid]["parede"], faixa_da_parede(objs[sid], lado)
                for outra, (fx0, fy0, fx1, fy1) in em_pe:
                    if outra != sid and fy0 <= y0 + EPS and y1 <= fy1 + EPS:
                        if fx0 <= a + EPS and a + t <= fx1 + EPS:
                            a += t
                        if fx0 <= b - t + EPS and b <= fx1 + EPS:
                            b -= t
            linhas.setdefault(chave, []).append((sid, lado, a, b))
    trechos = []
    for chave, membros in linhas.items():
        pontos = []
        for p in sorted(p for m in membros for p in (m[2], m[3])):
            if not pontos or p - pontos[-1] > EPS:
                pontos.append(p)
        atual = None
        for a, b in zip(pontos, pontos[1:]):
            cobrem = [m for m in membros if m[2] <= a + EPS and m[3] >= b - EPS]
            if not cobrem:
                atual = None
                continue
            altura = max(objs[m[0]]["altura"] for m in cobrem)
            if atual and abs(atual["altura"] - altura) < EPS and abs(atual["fim"] - a) < EPS:
                atual["fim"] = b
                continue
            atual = {"sala": cobrem[0][0], "lado": cobrem[0][1], "chave": chave, "ini": a, "fim": b, "altura": altura, "vaos": []}
            trechos.append(atual)
    for oid in sorted(i for i, o in objs.items() if o["tipo"] in VAOS):
        chave, ini, fim = vao_no_mundo(planta, objs[oid])
        for tr in trechos:
            if tr["chave"] == chave and tr["ini"] <= ini + EPS and fim <= tr["fim"] + EPS:
                tr["vaos"].append(oid)
                break
    return sorted(trechos, key=lambda tr: (tr["sala"], LADOS.index(tr["lado"]), tr["ini"]))


def _sobrepoe(r1: tuple, r2: tuple) -> bool:
    """Os dois retângulos (x0, y0, x1, y1) têm área em comum (encostar não conta)?"""
    return r1[0] < r2[2] - EPS and r2[0] < r1[2] - EPS and r1[1] < r2[3] - EPS and r2[1] < r1[3] - EPS


# ------------------------------------------------------------------------------------------------------- as operações

def _criar_sala(planta: dict, d: dict) -> str:
    oid = _id_livre(planta, d, "sala")
    planta["objetos"][oid] = {"tipo": "sala", "x": _cm(d, "x_m", 0.0), "y": _cm(d, "y_m", 0.0), "z": float(planta["base_z"]),
                              "largura": _cm(d, "largura_m"), "comprimento": _cm(d, "comprimento_m"),
                              "altura": _cm(d, "altura_m", PADROES["sala"]["altura"]), "parede": PADROES["sala"]["parede"]}
    return f"sala {oid} criada"


def _mudar_sala(planta: dict, d: dict) -> str:
    oid = _unico(planta, ("sala",), d.get("id"), "sala")
    s = planta["objetos"][oid]
    for campo, chave in (("largura_m", "largura"), ("comprimento_m", "comprimento"), ("altura_m", "altura")):
        if campo in d:
            s[chave] = _cm(d, campo)
    return f"sala {oid} com {s['largura'] / 100:g} x {s['comprimento'] / 100:g} m"


def _topo_da_mesa(planta: dict, mesa_id: str) -> float:
    m = planta["objetos"][mesa_id]
    return planta["objetos"][m["sala"]]["z"] + m["altura"]


def _na_mesa(mesa: dict, x: float, y: float, raio: float) -> bool:
    """O círculo de raio `raio` em (x, y) do mundo cabe inteiro no tampo?"""
    g = math.radians(mesa["giro"])
    dx, dy = x - mesa["x"], y - mesa["y"]
    lx, ly = dx * math.cos(g) + dy * math.sin(g), -dx * math.sin(g) + dy * math.cos(g)
    return abs(lx) <= mesa["largura"] / 2 - raio + 1e-6 and abs(ly) <= mesa["profundidade"] / 2 - raio + 1e-6


def _da_mesa_para_o_mundo(mesa: dict, lx: float, ly: float) -> tuple:
    g = math.radians(mesa["giro"])
    return mesa["x"] + lx * math.cos(g) - ly * math.sin(g), mesa["y"] + lx * math.sin(g) + ly * math.cos(g)


def _colocar(planta: dict, d: dict) -> str:
    tipo = d["tipo"]
    if tipo not in VAOS + MOVEIS + OBJETOS:
        raise Invalida(f"tipo desconhecido: {tipo!r}. Existem: {', '.join(VAOS + MOVEIS + OBJETOS)}")
    oid = _id_livre(planta, d, tipo)
    pad = PADROES[tipo]
    if tipo in VAOS:
        sala_id = _unico(planta, ("sala",), d.get("sala"), "sala")
        parede = d.get("parede", pad["parede"])
        if parede not in LADOS:
            raise Invalida(f"parede desconhecida: {parede!r}. Existem: {', '.join(LADOS)}")
        o = {"tipo": tipo, "sala": sala_id, "parede": parede,
             "posicao": _cm(d, "posicao_m", lado_cm(planta["objetos"][sala_id], parede) / 2),
             "largura": _cm(d, "largura_m", pad["largura"]), "altura": _cm(d, "altura_m", pad["altura"])}
        if tipo == "porta":
            o["angulo"] = float(d.get("angulo", pad["angulo"]))
        else:
            o["peitoril"] = _cm(d, "peitoril_m", pad["peitoril"])
    elif tipo in MOVEIS:
        sala_id = _unico(planta, ("sala",), d.get("sala"), "sala")
        s = planta["objetos"][sala_id]
        o = {"tipo": tipo, "sala": sala_id,
             "x": s["x"] + _cm(d, "x_m", s["largura"] / 2), "y": s["y"] + _cm(d, "y_m", s["comprimento"] / 2),
             "giro": float(d.get("giro", pad["giro"])), "largura": _cm(d, "largura_m", pad["largura"]),
             "profundidade": _cm(d, "profundidade_m", pad["profundidade"]), "altura": _cm(d, "altura_m", pad["altura"])}
    else:
        mesa_id = _unico(planta, MOVEIS, d.get("sobre"), "mesa")
        mesa = planta["objetos"][mesa_id]
        diam, alt = _cm(d, "diametro_m", pad["diametro"]), _cm(d, "altura_m", pad["altura"])
        vizinhos = [v for v in planta["objetos"].values() if v.get("sobre") == mesa_id]
        lugar = None
        for fx, fy in VAGAS:
            x, y = _da_mesa_para_o_mundo(mesa, fx * mesa["largura"] / 2, fy * mesa["profundidade"] / 2)
            livre = all(math.hypot(x - v["x"], y - v["y"]) >= (diam + v["diametro"]) / 2 + 2.0 for v in vizinhos)
            if livre and _na_mesa(mesa, x, y, diam / 2):
                lugar = (x, y)
                break
        if lugar is None:
            raise Invalida(f"não há lugar livre sobre {mesa_id} para {tipo} de {diam:g} cm")
        o = {"tipo": tipo, "sobre": mesa_id, "x": lugar[0], "y": lugar[1],
             "z": _topo_da_mesa(planta, mesa_id) + alt / 2 + FOLGA_APOIO, "rot": [0.0, 0.0, 0.0], "diametro": diam, "altura": alt}
    planta["objetos"][oid] = o
    return f"{tipo} {oid} colocad{'a' if tipo in ('porta', 'janela', 'mesa') else 'o'}"


def _mudar(planta: dict, d: dict) -> str:
    oid = d["id"]
    if oid not in planta["objetos"]:
        raise Invalida(f"não existe peça chamada {oid!r}. Existem: {', '.join(planta['objetos']) or 'nenhuma'}")
    o = planta["objetos"][oid]
    tipo = o["tipo"]
    if tipo == "sala":
        raise Invalida("para mudar uma sala use a operação mudar_sala")
    aceitos = {"porta": ("parede", "posicao_m", "largura_m", "altura_m", "angulo"),
               "janela": ("parede", "posicao_m", "largura_m", "altura_m", "peitoril_m"),
               "mesa": ("x_m", "y_m", "giro", "largura_m", "profundidade_m", "altura_m"),
               "prato": ("diametro_m", "altura_m"), "copo": ("diametro_m", "altura_m")}[tipo]
    for campo in d:
        if campo != "id" and campo not in aceitos:
            raise Invalida(f"{oid} é {tipo}: não tem o campo {campo!r}. Campos: {', '.join(aceitos)}")
    if tipo in VAOS:
        sala = planta["objetos"][o["sala"]]
        if "parede" in d:
            nova = OPOSTA[o["parede"]] if d["parede"] == "oposta" else d["parede"]
            if nova not in LADOS:
                raise Invalida(f"parede desconhecida: {d['parede']!r}. Existem: {', '.join(LADOS)}, oposta")
            if "posicao_m" not in d and lado_cm(sala, nova) != lado_cm(sala, o["parede"]):
                o["posicao"] = lado_cm(sala, nova) / 2  # parede de outro tamanho: vai para o meio
            o["parede"] = nova
        for campo, chave in (("posicao_m", "posicao"), ("largura_m", "largura"), ("altura_m", "altura"), ("peitoril_m", "peitoril")):
            if campo in d:
                o[chave] = _cm(d, campo)
        if "angulo" in d:
            o["angulo"] = float(d["angulo"])
    elif tipo in MOVEIS:
        sala = planta["objetos"][o["sala"]]
        antes = dict(o)
        if "x_m" in d:
            o["x"] = sala["x"] + _cm(d, "x_m")
        if "y_m" in d:
            o["y"] = sala["y"] + _cm(d, "y_m")
        if "giro" in d:
            o["giro"] = float(d["giro"])
        for campo, chave in (("largura_m", "largura"), ("profundidade_m", "profundidade"), ("altura_m", "altura")):
            if campo in d:
                o[chave] = _cm(d, campo)
        levar_junto(planta, oid, antes, o)
    else:
        if "diametro_m" in d:
            o["diametro"] = _cm(d, "diametro_m")
        if "altura_m" in d:
            centro_antigo = o["altura"] / 2
            o["altura"] = _cm(d, "altura_m")
            o["z"] += o["altura"] / 2 - centro_antigo
    return f"{tipo} {oid} mudad{'a' if tipo in ('porta', 'janela', 'mesa') else 'o'}"


def levar_junto(planta: dict, mesa_id: str, antes: dict, depois: dict) -> list:
    """A mesa mudou de lugar, de giro ou de altura: o que está sobre ela vai junto. Devolve os nomes levados."""
    levados = []
    g0, g1 = math.radians(antes["giro"]), math.radians(depois["giro"])
    for oid, o in planta["objetos"].items():
        if o.get("sobre") != mesa_id:
            continue
        dx, dy = o["x"] - antes["x"], o["y"] - antes["y"]
        lx, ly = dx * math.cos(g0) + dy * math.sin(g0), -dx * math.sin(g0) + dy * math.cos(g0)
        o["x"] = depois["x"] + lx * math.cos(g1) - ly * math.sin(g1)
        o["y"] = depois["y"] + lx * math.sin(g1) + ly * math.cos(g1)
        o["z"] += depois["altura"] - antes["altura"]
        o["rot"] = [o["rot"][0], o["rot"][1] + depois["giro"] - antes["giro"], o["rot"][2]]
        levados.append(oid)
    return levados


def _remover(planta: dict, d: dict) -> str:
    oid = d["id"]
    if oid not in planta["objetos"]:
        raise Invalida(f"não existe peça chamada {oid!r}")
    presos = [i for i, o in planta["objetos"].items() if oid in (o.get("sala"), o.get("sobre"))]
    if presos:
        raise Invalida(f"{oid} ainda tem peças ligadas a ela: {', '.join(presos)}. Remova-as antes")
    del planta["objetos"][oid]
    return f"{oid} removid{'a' if oid.startswith(('sala', 'porta', 'janela', 'mesa')) else 'o'}"


_FUNCOES = {"criar_sala": _criar_sala, "mudar_sala": _mudar_sala, "colocar": _colocar, "mudar": _mudar, "remover": _remover}


# ------------------------------------------------------------------------------------------------------- conferir a planta

def conferir(planta: dict, final: bool = True) -> None:
    """Confere a planta inteira. Qualquer coisa que não fecha vira Invalida, com o nome da peça.
    `final=False` (entre uma operação e outra da mesma ficha) deixa para o fim o que só fecha com a ficha inteira:
    a porta de um lado da parede dupla espera a do outro lado."""
    objs = planta["objetos"]
    for oid, s in objs.items():
        if s["tipo"] != "sala":
            continue
        for chave in ("largura", "comprimento", "altura"):
            if not s[chave] > 0.0:
                raise Invalida(f"{oid}: {chave} tem de ser maior que zero (veio {s[chave] / 100:g} m)")
    salas = sorted((i, s) for i, s in objs.items() if s["tipo"] == "sala")
    for n, (ia, a) in enumerate(salas):
        for ib, b in salas[n + 1:]:
            dentro_a = (a["x"], a["y"], a["x"] + a["largura"], a["y"] + a["comprimento"])
            dentro_b = (b["x"], b["y"], b["x"] + b["largura"], b["y"] + b["comprimento"])
            dica = (f"para encostar, deixe {b['parede'] / 100:g} m entre o lado de dentro de uma e o da outra "
                    "(a parede fica em comum)")
            if _sobrepoe(dentro_a, dentro_b) or any(_sobrepoe(dentro_a, faixa_da_parede(b, l)) or
                                                   _sobrepoe(dentro_b, faixa_da_parede(a, l)) for l in LADOS):
                raise Invalida(f"as salas {ia} e {ib} ficariam uma em cima da outra; {dica}")
            for la in LADOS:
                for lb in LADOS:
                    ka, kb = _linha(a, la)[0], _linha(b, lb)[0]
                    if ka[0] == kb[0] and ka != kb and _sobrepoe(faixa_da_parede(a, la), faixa_da_parede(b, lb)):
                        raise Invalida(f"a parede {la} de {ia} e a parede {lb} de {ib} ficariam meio uma dentro da outra; "
                                       f"{dica}, ou {(a['parede'] + b['parede']) / 100:g} m ou mais para cada uma ter a sua")
    trechos = trechos_de_parede(planta)
    no_trecho = {v: tr for tr in trechos for v in tr["vaos"]}
    todas = [(i, l, faixa_da_parede(s, l), _linha(s, l)[0]) for i, s in salas for l in LADOS]
    for oid, o in objs.items():
        if o["tipo"] not in VAOS:
            continue
        s = objs[o["sala"]]
        comp = lado_cm(s, o["parede"])
        if o["largura"] < 40.0 or o["altura"] < 40.0:
            raise Invalida(f"{oid}: vão pequeno demais ({o['largura']:g} x {o['altura']:g} cm)")
        ini, fim = o["posicao"] - o["largura"] / 2, o["posicao"] + o["largura"] / 2
        if ini < FOLGA_VAO - 1e-6 or fim > comp - FOLGA_VAO + 1e-6:
            raise Invalida(f"{oid} não cabe na parede {o['parede']} de {o['sala']} "
                           f"(vão de {ini / 100:.2f} a {fim / 100:.2f} m numa parede de {comp / 100:g} m)")
        base = o.get("peitoril", 0.0)
        if base < 0.0 or base + o["altura"] > s["altura"] - FOLGA_VAO + 1e-6:
            raise Invalida(f"{oid} não cabe na altura da parede de {o['sala']} ({s['altura'] / 100:g} m)")
        if o["tipo"] == "porta" and not -1e-6 <= o["angulo"] <= 120.0:
            raise Invalida(f"{oid}: ângulo de {o['angulo']:g} fora do aceito (0 a 120)")
        chave, mi, mf = vao_no_mundo(planta, o)
        for outro_id, v in objs.items():
            if outro_id < oid and v["tipo"] in VAOS:
                ch2, vi, vf = vao_no_mundo(planta, v)
                if ch2 == chave and mi < vf + FOLGA_ENTRE_VAOS and vi - FOLGA_ENTRE_VAOS < mf:
                    if v["sala"] == o["sala"]:
                        raise Invalida(f"{oid} e {outro_id} ficariam um em cima do outro na parede {o['parede']} de {o['sala']}")
                    raise Invalida(f"{oid} e {outro_id} ficariam um em cima do outro: a parede entre {o['sala']} e "
                                   f"{v['sala']} é uma só, e um vão nela já passa de um cômodo para o outro")
        if oid not in no_trecho:
            raise Invalida(f"{oid} ficaria no encontro de duas paredes de alturas diferentes; mude a posição")
        # o vão atravessa a parede: nela e logo depois dela (1 cm de cada lado) não pode haver outra parede, como a
        # ponta da parede de uma sala vizinha
        recorte = (mi, chave[1] - 1.0, mf, chave[2] + 1.0) if chave[0] == "x" else (chave[1] - 1.0, mi, chave[2] + 1.0, mf)
        for sid, lado, faixa, k in (todas if final else ()):
            if k != chave and _sobrepoe(recorte, faixa):
                # parede dupla (salas a duas paredes de distância) com um vão alinhado do outro lado: passagem
                vazado = k[0] == chave[0] and any(
                    objs[v]["sala"] == sid and objs[v]["parede"] == lado and vao_no_mundo(planta, objs[v])[1] <= mi + EPS
                    and mf <= vao_no_mundo(planta, objs[v])[2] + EPS for v in objs if objs[v]["tipo"] in VAOS)
                if not vazado:
                    raise Invalida(f"{oid} daria de cara com a parede {lado} de {sid}; mude a posição")
    caixas = {}
    for oid, o in objs.items():
        if o["tipo"] not in MOVEIS:
            continue
        s = objs[o["sala"]]
        g = math.radians(o["giro"])
        mx = (abs(o["largura"] * math.cos(g)) + abs(o["profundidade"] * math.sin(g))) / 2
        my = (abs(o["largura"] * math.sin(g)) + abs(o["profundidade"] * math.cos(g))) / 2
        if (o["x"] - mx < s["x"] + FOLGA_MOVEL - 1e-6 or o["x"] + mx > s["x"] + s["largura"] - FOLGA_MOVEL + 1e-6
                or o["y"] - my < s["y"] + FOLGA_MOVEL - 1e-6 or o["y"] + my > s["y"] + s["comprimento"] - FOLGA_MOVEL + 1e-6):
            raise Invalida(f"{oid} ficaria fora de {o['sala']} (ou encostada na parede)")
        if o["altura"] > s["altura"] - 20.0 or min(o["largura"], o["profundidade"]) < 30.0 or o["altura"] < 20.0:
            raise Invalida(f"{oid}: medidas fora do aceito")
        for outro_id, (ox, oy, omx, omy) in caixas.items():
            if abs(o["x"] - ox) < mx + omx and abs(o["y"] - oy) < my + omy:
                raise Invalida(f"{oid} e {outro_id} ficariam um em cima do outro")
        caixas[oid] = (o["x"], o["y"], mx, my)
    for oid, o in objs.items():
        if o["tipo"] not in OBJETOS:
            continue
        if not 1.0 <= o["diametro"] <= 60.0 or not 0.5 <= o["altura"] <= 60.0:
            raise Invalida(f"{oid}: medidas fora do aceito")
        if o.get("sobre"):
            if not _na_mesa(objs[o["sobre"]], o["x"], o["y"], o["diametro"] / 2):
                raise Invalida(f"{oid} não cabe sobre {o['sobre']} nesse lugar")


def aplicar_ficha(planta: dict, ficha: dict) -> tuple:
    """Devolve (planta nova, resumo). Não muda a planta recebida. Recusa (Invalida) a ficha inteira se algo não fecha."""
    if not isinstance(ficha, dict) or not isinstance(ficha.get("operacoes"), list) or not ficha["operacoes"]:
        raise Invalida('a ficha precisa de "operacoes": uma lista com pelo menos uma operação')
    desconhecidos = set(ficha) - {"pedido", "operacoes"}
    if desconhecidos:
        raise Invalida(f"campo desconhecido na ficha: {', '.join(sorted(desconhecidos))}")
    nova = copy.deepcopy(planta)
    resumo = []
    for n, op in enumerate(ficha["operacoes"], 1):
        if not isinstance(op, dict):
            raise Invalida(f"operação {n}: tem de ser um objeto com o campo \"operacao\"")
        try:
            dados = _conferir_campos(op)
            resumo.append(_FUNCOES[op["operacao"]](nova, dados))
            conferir(nova, final=False)
        except Invalida as e:
            raise Invalida(f"operação {n} ({op.get('operacao')}): {e}") from None
    try:
        conferir(nova)
    except Invalida as e:
        raise Invalida(f"com a ficha inteira: {e}") from None
    return nova, resumo
