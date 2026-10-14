"""Cadastro das PEÇAS: o que vira ator no Unreal. Só dados (o editor recebe isto como JSON e monta os Blueprints).

Cada peça é um Blueprint com variáveis (os parâmetros, editáveis na instância) e um Construction Script escrito na
linguagem de grafos da ferramenta de Blueprint da Epic. A geometria é feita pelo Unreal: cubos e cilindros do motor
(com a colisão simples deles), escalados pelo Construction Script. Acrescentar uma peça é acrescentar uma entrada aqui.

Convenções do espaço local (cm):
- parede: corre em +X a partir da origem, espessura centrada em Y, base em z = 0;
- piso: canto mínimo na origem, topo em z = 0;
- porta: origem no pé do lado da dobradiça, folha em +X quando fechada, abre girando para +Y;
- janela: origem no canto de baixo do vão, vidro em +X;
- mesa: origem no chão, no centro; objeto: origem no centro do corpo.
Componentes com nome começando por `Uso` são pontos de uso (onde o personagem fica) e por `Ancora`, pontos de apoio
(sem sublinhado no nome: a ferramenta de grafos da Epic não acha a variável de um componente com sublinhado).
"""

CUBO = "/Engine/BasicShapes/Cube.Cube"  # 100 cm de lado, centrado, com colisão simples de caixa
CILINDRO = "/Engine/BasicShapes/Cylinder.Cylinder"  # 100 cm de diâmetro e de altura, centrado, com colisão simples
PASTA_PECAS = "/Game/Director/Pecas"

GET = "Variables|Default|Get"  # componentes da peça
VAR = "Variables|Director|Get"  # parâmetros da peça (as variáveis ficam na categoria "Director" do painel de detalhes)
VEC = "Math|Vector|MakeVector"
ROT = "Math|Rotator|MakeRotator"
LOC = "Transformation|SetRelativeLocation"
ESC = "Transformation|SetRelativeScale3D"
GIRO = "Transformation|SetRelativeRotation"


def _caixa(comp: str, x0: str, x1: str, y_cm: str, z0: str, z1: str) -> str:
    """Posiciona e escala o cubo `comp` para ocupar x0..x1 e z0..z1 (expressões), com `y_cm` de espessura.
    Se a largura ou a altura for nula (ex.: parede sem vão), o cubo fica invisível, com 1 cm, 5 cm abaixo da base da
    peça (dentro do piso), onde não barra nada.

    Por que não desligar a colisão dele: medido ao vivo em 13/10, a colisão que o Construction Script desliga numa
    rodada fica guardada na instância e volta nas rodadas seguintes (o segmento reaparece visível e sem colisão).
    Por isso a peça nunca mexe em colisão: só em posição, escala e visibilidade."""
    w, h = f"(- {x1} {x0})", f"(- {z1} {z0})"
    return f"""
  (bind vis_{comp} (and (> {w} 0.1) (> {h} 0.1)))
  ({LOC} :self ({GET}{comp}) :NewLocation ({VEC} :X (/ (+ {x0} {x1}) 2.0) :Y 0.0 :Z (select vis_{comp} (/ (+ {z0} {z1}) 2.0) -5.0)))
  ({ESC} :self ({GET}{comp}) :NewScale3D ({VEC} :X (/ (select vis_{comp} {w} 1.0) 100.0) :Y (/ (select vis_{comp} {y_cm} 1.0) 100.0) :Z (/ (select vis_{comp} {h} 1.0) 100.0)))
  (Rendering|SetVisibility :self ({GET}{comp}) :bNewVisibility vis_{comp})"""


def _cubo(nome: str, pai: str = "", **props) -> dict:
    return {"nome": nome, "classe": "StaticMeshComponent", "pai": pai, "props": {"static_mesh": {"asset": CUBO}, **props}}


def _ponto(nome: str, pai: str = "") -> dict:
    return {"nome": nome, "classe": "SceneComponent", "pai": pai, "props": {}}


_PAREDE = f"""
(fn ConstructionScript ()
  (bind L ({VAR}Comprimento))
  (bind H ({VAR}Altura))
  (bind E ({VAR}Espessura))
  (bind a (- ({VAR}VaoCentro) (/ ({VAR}VaoLargura) 2.0)))
  (bind b (+ ({VAR}VaoCentro) (/ ({VAR}VaoLargura) 2.0)))
  (bind vb ({VAR}VaoBase))
  (bind vt (+ ({VAR}VaoBase) ({VAR}VaoAltura)))
{_caixa("Esq", "0.0", "a", "E", "0.0", "H")}
{_caixa("Dir", "b", "L", "E", "0.0", "H")}
{_caixa("Acima", "a", "b", "E", "vt", "H")}
{_caixa("Abaixo", "a", "b", "E", "0.0", "vb")})
"""

_PISO = f"""
(fn ConstructionScript ()
  (bind L ({VAR}Largura))
  (bind C ({VAR}Comprimento))
  (bind E ({VAR}Espessura))
  ({LOC} :self ({GET}Laje) :NewLocation ({VEC} :X (/ L 2.0) :Y (/ C 2.0) :Z (/ E -2.0)))
  ({ESC} :self ({GET}Laje) :NewScale3D ({VEC} :X (/ L 100.0) :Y (/ C 100.0) :Z (/ E 100.0))))
"""

_PORTA = f"""
(fn ConstructionScript ()
  (bind L ({VAR}Largura))
  (bind A ({VAR}Altura))
  ({LOC} :self ({GET}Folha) :NewLocation ({VEC} :X (/ L 2.0) :Y (/ ({VAR}Espessura) 2.0) :Z (/ A 2.0)))
  ({ESC} :self ({GET}Folha) :NewScale3D ({VEC} :X (/ L 100.0) :Y (/ ({VAR}Espessura) 100.0) :Z (/ A 100.0)))
  ({GIRO} :self ({GET}Dobradica) :NewRotation ({ROT} :Roll 0.0 :Pitch 0.0 :Yaw ({VAR}Angulo)))
  ({LOC} :self ({GET}UsoDentro) :NewLocation ({VEC} :X (/ L 2.0) :Y ({VAR}DistanciaUso) :Z 0.0))
  ({LOC} :self ({GET}UsoFora) :NewLocation ({VEC} :X (/ L 2.0) :Y (- 0.0 ({VAR}DistanciaUso)) :Z 0.0)))
"""

_JANELA = f"""
(fn ConstructionScript ()
  (bind L ({VAR}Largura))
  (bind A ({VAR}Altura))
  ({LOC} :self ({GET}Vidro) :NewLocation ({VEC} :X (/ L 2.0) :Y 0.0 :Z (/ A 2.0)))
  ({ESC} :self ({GET}Vidro) :NewScale3D ({VEC} :X (/ L 100.0) :Y (/ ({VAR}Espessura) 100.0) :Z (/ A 100.0))))
"""


def _perna(nome: str, sx: str, sy: str) -> str:
    return f"""
  ({LOC} :self ({GET}{nome}) :NewLocation ({VEC} :X (* {sx} (- (/ L 2.0) 8.0)) :Y (* {sy} (- (/ P 2.0) 8.0)) :Z (/ (- A 4.0) 2.0)))
  ({ESC} :self ({GET}{nome}) :NewScale3D ({VEC} :X 0.06 :Y 0.06 :Z (/ (- A 4.0) 100.0)))"""


_MESA = f"""
(fn ConstructionScript ()
  (bind L ({VAR}Largura))
  (bind P ({VAR}Profundidade))
  (bind A ({VAR}Altura))
  ({LOC} :self ({GET}Tampo) :NewLocation ({VEC} :X 0.0 :Y 0.0 :Z (- A 2.0)))
  ({ESC} :self ({GET}Tampo) :NewScale3D ({VEC} :X (/ L 100.0) :Y (/ P 100.0) :Z 0.04))
{_perna("Perna1", "1.0", "1.0")}
{_perna("Perna2", "1.0", "-1.0")}
{_perna("Perna3", "-1.0", "1.0")}
{_perna("Perna4", "-1.0", "-1.0")}
  ({LOC} :self ({GET}AncoraTopo) :NewLocation ({VEC} :X 0.0 :Y 0.0 :Z A)))
"""

_OBJETO = f"""
(fn ConstructionScript ()
  (bind D ({VAR}Diametro))
  (Transformation|SetActorScale3D :NewScale3D ({VEC} :X (/ D 100.0) :Y (/ D 100.0) :Z (/ ({VAR}Altura) 100.0))))
"""

PECAS: dict = {
    "parede": {
        "blueprint": "BP_Parede", "pai": "/Script/Engine.Actor",
        "variaveis": {"Comprimento": 400.0, "Altura": 270.0, "Espessura": 15.0,
                      "VaoLargura": 0.0, "VaoCentro": 0.0, "VaoBase": 0.0, "VaoAltura": 0.0},
        "componentes": [_cubo("Esq"), _cubo("Dir"), _cubo("Acima"), _cubo("Abaixo")],
        "dsl": _PAREDE,
    },
    "piso": {
        "blueprint": "BP_Piso", "pai": "/Script/Engine.Actor",
        "variaveis": {"Largura": 400.0, "Comprimento": 400.0, "Espessura": 10.0},
        "componentes": [_cubo("Laje")],
        "dsl": _PISO,
    },
    "porta": {
        "blueprint": "BP_Porta", "pai": "/Script/Engine.Actor",
        "variaveis": {"Largura": 100.0, "Altura": 210.0, "Espessura": 4.0, "Angulo": 0.0, "DistanciaUso": 90.0},
        # A folha é móvel e ENTRA na malha de navegação (o laboratório refaz a malha com o jogo rodando): porta fechada
        # tira o caminho, porta aberta devolve, e quem anda contorna a folha aberta. Medido em 13/10: com a folha
        # fora da malha, o personagem entrava e ficava preso na folha aberta.
        # A folha fica encostada na face de dentro da parede (Y = meia espessura): aberta a 90 graus, ela sai
        # inteira do vão.
        "componentes": [_ponto("Dobradica"),
                        _cubo("Folha", "Dobradica", mobility={"enum": ["ComponentMobility", "MOVABLE"]},
                              can_ever_affect_navigation=True),
                        _ponto("UsoDentro"), _ponto("UsoFora")],
        "dsl": _PORTA,
    },
    "janela": {
        "blueprint": "BP_Janela", "pai": "/Script/Engine.Actor",
        "variaveis": {"Largura": 120.0, "Altura": 110.0, "Espessura": 2.0},
        "componentes": [_cubo("Vidro")],
        "dsl": _JANELA,
    },
    "mesa": {
        "blueprint": "BP_Mesa", "pai": "/Script/Engine.Actor",
        "variaveis": {"Largura": 120.0, "Profundidade": 80.0, "Altura": 75.0},
        "componentes": [_cubo("Tampo"), _cubo("Perna1"), _cubo("Perna2"), _cubo("Perna3"), _cubo("Perna4"),
                        _ponto("AncoraTopo")],
        "dsl": _MESA,
    },
    "objeto": {
        # corpo físico solto (prato, copo...): o pai é o StaticMeshActor do motor, para a raiz ser a própria malha
        # (um corpo com física que não é a raiz se solta do ator ao simular)
        "blueprint": "BP_Objeto", "pai": "/Script/Engine.StaticMeshActor",
        "variaveis": {"Diametro": 10.0, "Altura": 10.0},
        "componentes": [],
        "raiz": {"props": {"static_mesh": {"asset": CILINDRO}, "mobility": {"enum": ["ComponentMobility", "MOVABLE"]}},
                 "fisica": True},
        "dsl": _OBJETO,
    },
}

# Peças que são classes do próprio motor (sem Blueprint): só posição, giro e escala.
NATIVAS: dict = {
    "nav": {"classe": "/Script/NavigationSystem.NavMeshBoundsVolume", "caixa_base": 200.0},
}


def classe_de(tipo: str) -> str:
    """Caminho que o editor usa para criar a peça."""
    if tipo in NATIVAS:
        return NATIVAS[tipo]["classe"]
    return f"{PASTA_PECAS}/{PECAS[tipo]['blueprint']}"


def variaveis() -> dict:
    """tipo -> nomes das variáveis que o inventário lê de volta."""
    return {t: sorted(p["variaveis"]) for t, p in PECAS.items()}
