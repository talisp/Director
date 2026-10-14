"""Operações do Director dentro do editor do laboratório. Cada uma recebe e devolve dados simples (JSON).

Regra: usar o que o Unreal já tem. Aqui não há geometria nem física próprias:
- as peças são Blueprints com Construction Script, criados pela ferramenta de Blueprint da Epic (EditorToolset);
- colisão e física são as dos componentes do motor; as medidas são traçados e consultas de navegação do motor;
- criar, mover e apagar atores é pelo subsistema de atores do editor, dentro de uma transação do editor.
O Director só toca em atores com a etiqueta `DIR_ID:` e só grava em `/Game/Director`.
"""
import hashlib
import importlib
import json
import math
import sys
import types
from typing import Any

import unreal

U: Any = unreal

OPS: dict = {}
PASTA = "/Game/Director"
ET_ID, ET_TIPO = "DIR_ID:", "DIR_TIPO:"
ESTADO = "director_estado"  # estado de sessão (Play): sobrevive à recarga das operações
# atores que o próprio motor cria e muda sozinho: não entram na conferência "o resto da cena ficou igual"
IGNORAR = ("RecastNavMesh", "AbstractNavData", "NavigationDataChunkActor", "WorldDataLayers", "WorldSettings",
           "WorldPartitionMiniMap", "GameplayDebuggerPlayerManager", "ChaosDebugDrawActor", "Brush", "DefaultPhysicsVolume")
PASSO_AMOSTRA_S = 0.05


def op(fn):
    OPS[fn.__name__] = fn
    return fn


def _estado() -> Any:
    st = sys.modules.get(ESTADO)
    if st is None:
        st = types.ModuleType(ESTADO)
        sys.modules[ESTADO] = st
    return st


def _mundo_editor():
    return U.get_editor_subsystem(U.UnrealEditorSubsystem).get_editor_world()


def _mundo_jogo():
    return U.get_editor_subsystem(U.UnrealEditorSubsystem).get_game_world()


def _eas():
    return U.get_editor_subsystem(U.EditorActorSubsystem)


def _les():
    return U.get_editor_subsystem(U.LevelEditorSubsystem)


def _v(v) -> list:
    return [round(v.x, 3), round(v.y, 3), round(v.z, 3)]


def _r(r) -> list:
    return [round(r.pitch, 3), round(r.yaw, 3), round(r.roll, 3)]


def _vec(l) -> Any:
    return U.Vector(float(l[0]), float(l[1]), float(l[2]))


def _rot(l) -> Any:
    return U.Rotator(pitch=float(l[0]), yaw=float(l[1]), roll=float(l[2]))


def _sujos() -> list:
    util = U.EditorLoadingAndSavingUtils
    nomes = (str(p.get_name()) for p in list(util.get_dirty_content_packages()) + list(util.get_dirty_map_packages()))
    return sorted(n for n in nomes if not n.startswith("/Temp/"))  # o mapa sem nome com que o editor abre não conta


def _level() -> str:
    mundo = _mundo_editor()
    return mundo.get_path_name().split(".")[0] if mundo else ""


def _etiquetas(ator) -> tuple:
    oid = tipo = ""
    for t in ator.tags:
        s = str(t)
        if s.startswith(ET_ID):
            oid = s[len(ET_ID):]
        elif s.startswith(ET_TIPO):
            tipo = s[len(ET_TIPO):]
    return oid, tipo


def _classe(ator) -> str:
    c = ator.get_class().get_path_name()
    return c.split(".")[0] if c.startswith("/Game/") else c  # Blueprint: devolve o caminho do asset


def _controlados(mundo_jogo=None) -> dict:
    """id -> ator, só os que têm a etiqueta do Director."""
    if mundo_jogo is not None:
        atores = U.GameplayStatics.get_all_actors_of_class(mundo_jogo, U.Actor)
    else:
        atores = _eas().get_all_level_actors()
    achados = {}
    for a in atores:
        oid, _ = _etiquetas(a)
        if oid:
            if oid in achados:
                raise RuntimeError(f"dois atores com o mesmo identificador: {oid}")
            achados[oid] = a
    return achados


# ----------------------------------------------------------------------------------------------------------- geral

@op
def info():
    """Quem é este editor: pasta do projeto, versão, level aberto, se está em Play."""
    return {"projeto_dir": str(U.Paths.convert_relative_path_to_full(U.Paths.project_dir())),
            "motor": str(U.SystemLibrary.get_engine_version()),
            "level": _level(),
            "em_play": _mundo_jogo() is not None,
            "lingua": str(U.InternationalizationLibrary.get_current_language()),
            "por_salvar": _sujos(),
            "ops": sorted(OPS)}


@op
def quit_editor(descartar: bool = False):
    """Fecha o editor do laboratório. Recusa se houver algo por salvar, a não ser com descartar=True
    (o editor do laboratório abre sem diálogos, então o que não foi salvo é jogado fora)."""
    sujos = _sujos()
    if sujos and not descartar:
        raise RuntimeError(f"há pacotes por salvar: {sujos}")
    U.SystemLibrary.quit_editor()
    return {"pedido": "sair"}


@op
def dev_exec(codigo: str):
    """SÓ DESENVOLVIMENTO: roda um trecho de Python no editor do laboratório e devolve a variável `resultado`.
    O núcleo nunca usa esta operação."""
    amb: dict = {"unreal": unreal, "U": U}
    exec(codigo, amb)  # noqa: S102
    return {"resultado": amb.get("resultado")}


# ----------------------------------------------------------------------------------------------------------- peças

def _valor(v):
    if isinstance(v, dict) and "asset" in v:
        return U.load_asset(v["asset"].split(".")[0])
    if isinstance(v, dict) and "enum" in v:
        return getattr(getattr(U, v["enum"][0]), v["enum"][1])
    return v


def _moldes(bp) -> dict:
    """nome da variável do componente -> molde do componente dentro do Blueprint."""
    sds = U.get_engine_subsystem(U.SubobjectDataSubsystem)
    lib = U.SubobjectDataBlueprintFunctionLibrary
    achados = {}
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        d = lib.get_data(h)
        if lib.is_actor(d):
            continue
        obj = lib.get_object_for_blueprint(d, bp)
        if obj is not None:
            achados[str(lib.get_variable_name(d))] = obj
    return achados


@op
def pieces_build(pecas: dict, refazer: bool = False):
    """Cria ou atualiza os Blueprints das peças pela ferramenta de Blueprint da Epic e salva os assets.
    Peça já igual ao cadastro (mesma assinatura) não é tocada."""
    if str(U.InternationalizationLibrary.get_current_language()) != "en":
        raise RuntimeError("o editor precisa estar em inglês (-culture=en): a linguagem de grafos da Epic usa os nomes em inglês")
    BT = importlib.import_module("editor_toolset.toolsets.blueprint").BlueprintTools
    AT = importlib.import_module("editor_toolset.toolsets.actor").ActorTools
    eal = U.EditorAssetLibrary
    saida = {}
    for tipo, s in pecas.items():
        caminho = f"{PASTA}/Pecas/{s['blueprint']}"
        assinatura = hashlib.sha1(json.dumps(s, sort_keys=True).encode()).hexdigest()[:16]
        if eal.does_asset_exist(caminho):
            bp = U.load_asset(caminho)
            if str(eal.get_metadata_tag(bp, "director_assinatura")) == assinatura and not refazer:
                saida[tipo] = {"estado": "igual", "asset": caminho, "assinatura": assinatura}
                continue
            estado = "atualizado"
        else:
            bp = BT.create(f"{PASTA}/Pecas", s["blueprint"], U.load_class(None, s["pai"]))
            estado = "criado"
        tem = set(BT.list_variables(bp))
        for nome in s["variaveis"]:
            if nome not in tem:
                BT.add_variable(bp, nome, "float")
                BT.set_variable_instance_editable(bp, nome, True)
                BT.set_variable_category(bp, nome, "Director")
        moldes = _moldes(bp)
        for c in s["componentes"]:
            if c["nome"] not in moldes:
                dono = moldes[c["pai"]] if c.get("pai") else bp
                AT.add_component(dono, getattr(U, c["classe"]).static_class(), c["nome"])
                moldes = _moldes(bp)
        for c in s["componentes"]:
            for prop, v in c["props"].items():
                moldes[c["nome"]].set_editor_property(prop, _valor(v))
        raiz = s.get("raiz")
        if raiz:  # peça cujo pai já traz o componente raiz (ex.: StaticMeshActor)
            comp = BT.get_default_object(bp).get_editor_property("static_mesh_component")
            for prop, v in raiz["props"].items():
                comp.set_editor_property(prop, _valor(v))
            if raiz.get("fisica"):
                comp.set_simulate_physics(True)
        BT.compile_blueprint(bp)
        BT.write_graph_dsl(BT.get_graph(bp, "UserConstructionScript"), s["dsl"])
        padrao = BT.get_default_object(bp)
        for nome, v in s["variaveis"].items():
            padrao.set_editor_property(nome, float(v))
        BT.compile_blueprint(bp)
        eal.set_metadata_tag(bp, "director_assinatura", assinatura)
        if not eal.save_loaded_asset(bp, False):
            raise RuntimeError(f"não consegui salvar {caminho}")
        saida[tipo] = {"estado": estado, "asset": caminho, "assinatura": assinatura,
                       "componentes": sorted(_moldes(bp)), "variaveis": sorted(BT.list_variables(bp))}
    return {"pecas": saida}


# ----------------------------------------------------------------------------------------------------------- level

@op
def level_ensure(caminho: str, modelo: str = "/Engine/Maps/Templates/Template_Default"):
    """Abre o level da cena; se ele não existe, cria a partir do modelo do motor (chão e luz) e salva."""
    if not caminho.startswith(PASTA + "/"):
        raise RuntimeError(f"o level da cena tem de ficar em {PASTA}")
    if _mundo_jogo() is not None:
        raise RuntimeError("em_play")
    if _level() == caminho:
        return {"estado": "ja_aberto", "level": caminho}
    sujos = _sujos()
    if sujos:
        raise RuntimeError(f"há pacotes por salvar: {sujos}")
    if U.EditorAssetLibrary.does_asset_exist(caminho):
        ok, estado = _les().load_level(caminho), "carregado"
    else:
        ok, estado = _les().new_level_from_template(caminho, modelo), "criado"
    if not ok or _level() != caminho:
        raise RuntimeError(f"não consegui abrir {caminho} (level atual: {_level()})")
    return {"estado": estado, "level": caminho}


@op
def reload_level():
    """Joga fora o que está na memória e recarrega o level do disco (recuperação depois de uma falha)."""
    if _mundo_jogo() is not None:
        raise RuntimeError("em_play")
    caminho = _level()
    ok = _les().load_level(caminho)
    return {"recarregou": bool(ok), "level": _level(), "por_salvar": _sujos()}


@op
def save():
    """Salva só o que é do Director: o level da cena e os assets em /Game/Director."""
    util = U.EditorLoadingAndSavingUtils
    todos = list(util.get_dirty_content_packages()) + list(util.get_dirty_map_packages())
    meus = [p for p in todos if str(p.get_name()).startswith(PASTA + "/")]
    alheios = sorted(str(p.get_name()) for p in todos if p not in meus)
    ok = util.save_packages(meus, True) if meus else True
    return {"salvou": bool(ok), "pacotes": sorted(str(p.get_name()) for p in meus), "alheios_por_salvar": alheios,
            "por_salvar": _sujos()}


# ----------------------------------------------------------------------------------------------------------- cena

def _descrever(ator) -> dict:
    return {"classe": _classe(ator), "caminho": ator.get_path_name(), "rotulo": str(ator.get_actor_label()),
            "loc": _v(ator.get_actor_location()), "rot": _r(ator.get_actor_rotation()),
            "escala": _v(ator.get_actor_scale3d())}


def _pontos(ator) -> dict:
    """Pontos de uso e de apoio declarados pela peça (componentes `Uso...` e `Ancora...`), em coordenadas do mundo."""
    achados = {}
    for c in ator.get_components_by_class(U.SceneComponent):
        nome = str(c.get_name())
        if nome.startswith(("Uso", "Ancora")):
            achados[nome] = _v(c.get_world_location()) + [round(c.get_world_rotation().yaw, 3)]
    return achados


@op
def inventory(variaveis: dict):
    """Inventário do level aberto: os atores do Director (com identificador, tipo, classe, posição, parâmetros e
    pontos de uso) e, à parte, todos os outros atores (para conferir que não foram tocados)."""
    controlados, fora = {}, []
    for a in _eas().get_all_level_actors():
        oid, tipo = _etiquetas(a)
        d = _descrever(a)
        if not oid:
            if not d["classe"].split(".")[-1].startswith(IGNORAR):
                fora.append(d)
            continue
        if oid in controlados:
            raise RuntimeError(f"dois atores com o mesmo identificador: {oid}")
        d["tipo"] = tipo
        d["params"] = {}
        for nome in variaveis.get(tipo, []):
            d["params"][nome] = round(float(a.get_editor_property(nome)), 3)
        d["pontos"] = _pontos(a)
        controlados[oid] = d
    return {"level": _level(), "controlados": controlados, "fora": sorted(fora, key=lambda x: x["caminho"]),
            "por_salvar": _sujos()}


def _uma(a: dict, idx: dict) -> str:
    acao, oid = a["acao"], a["id"]
    if acao == "remover":
        ator = idx.pop(oid)
        if not _eas().destroy_actor(ator):
            raise RuntimeError(f"não consegui apagar {oid}")
        return "removido"
    if acao == "criar":
        if oid in idx:
            raise RuntimeError(f"já existe: {oid}")
        classe = a["classe"]
        loc, rot = _vec(a["loc"]), _rot(a["rot"])
        if classe.startswith("/Script/"):
            cls = U.load_class(None, classe)
            if cls is None:
                raise RuntimeError(f"classe desconhecida: {classe}")
            ator = _eas().spawn_actor_from_class(cls, loc, rot)
        else:
            molde = U.load_asset(classe)
            if molde is None:
                raise RuntimeError(f"peça não encontrada: {classe}")
            ator = _eas().spawn_actor_from_object(molde, loc, rot)
        if ator is None:
            raise RuntimeError(f"o editor não criou {oid}")
        ator.set_actor_label(oid)
        ator.set_editor_property("tags", [ET_ID + oid, ET_TIPO + a["tipo"]])
        ator.set_folder_path("Director")
        idx[oid] = ator
    elif acao == "atualizar":
        ator = idx[oid]
        ator.modify()
        if "loc" in a or "rot" in a:
            loc = _vec(a["loc"]) if "loc" in a else ator.get_actor_location()
            rot = _rot(a["rot"]) if "rot" in a else ator.get_actor_rotation()
            ator.set_actor_location_and_rotation(loc, rot, False, True)
    else:
        raise RuntimeError(f"ação desconhecida: {acao}")
    if "escala" in a:
        ator.set_actor_scale3d(_vec(a["escala"]))
    for nome, v in (a.get("params") or {}).items():
        ator.set_editor_property(nome, float(v))  # mudar a variável faz o Unreal rodar o Construction Script de novo
    if a.get("tipo") == "nav":
        nav = U.NavigationSystemV1.get_navigation_system(_mundo_editor())
        if nav is not None:
            nav.on_navigation_bounds_updated(ator)
    return "criado" if acao == "criar" else "atualizado"


@op
def apply(acoes: list):
    """Aplica a lista de ações (criar, atualizar, remover) numa única transação do editor.

    Se uma ação falha, para e devolve `aplicado=False`: quem chamou recarrega o level do disco (`reload_level`).
    O "desfazer" do editor não serve de recuperação: medido ao vivo em 13/10, cancelar a transação não desfaz nada,
    e desfazer a remoção de uma peça devolve o ator com os componentes quebrados (sem colisão)."""
    if _mundo_jogo() is not None:
        raise RuntimeError("em_play")
    idx = _controlados()
    feitos, erro = [], None
    with U.ScopedEditorTransaction("Director: aplicar"):
        try:
            for a in acoes:
                feitos.append([a["id"], _uma(a, idx)])
        except Exception as e:  # noqa: BLE001
            erro = f"{a.get('id')}: {type(e).__name__}: {e}"
    return {"aplicado": erro is None, "erro": erro, "feitos": feitos}


# ----------------------------------------------------------------------------------------------------------- medir

def _acerto(hit) -> dict:
    if not hit:
        return {"acertou": False}
    d = hit.to_dict()
    ator = d.get("hit_actor")
    comp = d.get("hit_component")
    oid, tipo = _etiquetas(ator) if ator else ("", "")
    return {"acertou": bool(d.get("blocking_hit")), "id": oid, "tipo": tipo,
            "rotulo": str(ator.get_actor_label()) if ator else "", "componente": str(comp.get_name()) if comp else "",
            "distancia": round(float(d.get("distance", 0.0)), 2), "ponto": _v(d["impact_point"])}


@op
def measure(consultas: list, mundo: str = "editor"):
    """Medidas pelo próprio motor. Tipos de consulta:
    - raio: {de, ate} -> primeiro objeto que barra a linha (canal de visibilidade, colisão simples);
    - varredura: {de, ate, raio, meia_altura} -> primeiro objeto que barra uma cápsula (perfil de colisão Pawn);
    - caminho: {de, ate} -> caminho da malha de navegação (existe, parcial, comprimento, pontos);
    - nav: {} -> se a malha de navegação ainda está sendo construída."""
    w = _mundo_jogo() if mundo == "jogo" else _mundo_editor()
    if w is None:
        raise RuntimeError("mundo indisponível")
    nada = U.Array(U.Actor)
    saida = []
    for c in consultas:
        t = c["tipo"]
        if t == "raio":
            hit = U.SystemLibrary.line_trace_single(w, _vec(c["de"]), _vec(c["ate"]), U.TraceTypeQuery.ECC_VISIBILITY,
                                                    False, nada, U.DrawDebugTrace.NONE, True)
            saida.append(_acerto(hit))
        elif t == "varredura":
            hit = U.SystemLibrary.capsule_trace_single_by_profile(
                w, _vec(c["de"]), _vec(c["ate"]), float(c.get("raio", 34.0)), float(c.get("meia_altura", 88.0)),
                "Pawn", False, nada, U.DrawDebugTrace.NONE, True)
            saida.append(_acerto(hit))
        elif t == "caminho":
            nav = U.NavigationSystemV1.get_navigation_system(w)
            p = nav.find_path_to_location_synchronously(w, _vec(c["de"]), _vec(c["ate"])) if nav else None
            if p is None:
                saida.append({"existe": False, "motivo": "sem_caminho"})
            else:
                pts = [_v(x) for x in p.path_points]
                saida.append({"existe": bool(p.is_valid()) and len(pts) >= 2, "parcial": bool(p.is_partial()),
                              "comprimento": round(float(p.get_path_length()), 1), "pontos": pts})
        elif t == "nav":
            nav = U.NavigationSystemV1.get_navigation_system(w)
            malhas = [str(a.get_actor_label()) for a in _eas().get_all_level_actors()
                      if a.get_class().get_name().startswith("RecastNavMesh")] if mundo != "jogo" else []
            saida.append({"construindo": bool(nav.is_navigation_being_built(w)) if nav else None, "malhas": malhas})
        else:
            raise RuntimeError(f"consulta desconhecida: {t}")
    return {"medidas": saida}


# ----------------------------------------------------------------------------------------------------------- Play

def _freio_de_fundo(soltar: bool):
    """O editor em segundo plano roda a ~3 quadros/s ("Use Less CPU when in Background"). soltar=True desliga essa
    economia só na memória e guarda o valor anterior; False devolve o anterior. (Receita do experimento 1.)"""
    st = _estado()
    try:
        cfg = U.load_object(None, "/Script/UnrealEd.Default__EditorPerformanceSettings")
        prop = "throttle_cpu_when_not_foreground"
        anterior = getattr(st, "freio_anterior", None)
        if soltar:
            if anterior is None:
                st.freio_anterior = bool(cfg.get_editor_property(prop))
            cfg.set_editor_property(prop, False)
        elif anterior is not None:
            cfg.set_editor_property(prop, anterior)
            st.freio_anterior = None
        return bool(cfg.get_editor_property(prop))
    except Exception as e:  # noqa: BLE001
        return f"erro: {e}"


def _parar_amostragem():
    st = _estado()
    cabo = getattr(st, "cabo", None)
    if cabo is not None:
        try:
            U.unregister_slate_post_tick_callback(cabo)
        except Exception:  # noqa: BLE001
            pass
    st.cabo = None


@op
def play_start(simulate: bool = True, full_speed: bool = True):
    """Pede ao editor para rodar o jogo (atendido no próximo quadro: confira com play_state)."""
    if _mundo_jogo() is not None:
        raise RuntimeError("ja_em_play")
    freio = _freio_de_fundo(True) if full_speed else None
    if simulate:
        _les().editor_play_simulate()
    else:
        _les().editor_request_begin_play()
    return {"modo": "simulate" if simulate else "pie", "economia_de_cpu_ligada": freio}


@op
def play_state():
    w = _mundo_jogo()
    return {"em_play": w is not None, "tempo": round(float(U.GameplayStatics.get_time_seconds(w)), 3) if w else None}


@op
def play_stop():
    """Para o jogo. O que mudou durante o Play NÃO vai para o cenário salvo (isso é o `incorporar` do núcleo)."""
    _parar_amostragem()
    _estado().andar = None
    if _mundo_jogo() is not None:
        _les().editor_request_end_play()
    return {"pedido": "parar", "economia_de_cpu_ligada": _freio_de_fundo(False)}


def _raiz_fisica(ator):
    raiz = ator.get_editor_property("root_component")
    return raiz if isinstance(raiz, U.PrimitiveComponent) else None


@op
def sim_read():
    """Onde está, durante o Play, cada objeto do Director (posição, giro, velocidade; ângulo real da dobradiça)."""
    w = _mundo_jogo()
    if w is None:
        raise RuntimeError("fora_do_play")
    saida = {}
    for oid, a in _controlados(w).items():
        d = {"loc": _v(a.get_actor_location()), "rot": _r(a.get_actor_rotation()),
             "vel": round(float(a.get_velocity().length()), 2)}
        raiz = _raiz_fisica(a)
        d["fisica"] = bool(raiz.is_simulating_physics()) if raiz else False
        for c in a.get_components_by_class(U.SceneComponent):
            if str(c.get_name()) == "Dobradica":
                d["angulo"] = round(float(c.get_editor_property("relative_rotation").yaw), 3)
        saida[oid] = d
    return {"tempo": round(float(U.GameplayStatics.get_time_seconds(w)), 3), "objetos": saida}


@op
def sim_impulse(id: str, velocidade: list):
    """Empurra um objeto físico durante o Play (mudança de velocidade, em cm/s)."""
    w = _mundo_jogo()
    if w is None:
        raise RuntimeError("fora_do_play")
    raiz = _raiz_fisica(_controlados(w)[id])
    if raiz is None or not raiz.is_simulating_physics():
        raise RuntimeError(f"{id} não está simulando física")
    raiz.add_impulse(_vec(velocidade), "None", True)
    return {"empurrado": id}


@op
def sim_move(id: str, loc: list):
    """Durante o Play, leva um objeto para outro ponto (teleporte) e o solta ali."""
    w = _mundo_jogo()
    if w is None:
        raise RuntimeError("fora_do_play")
    a = _controlados(w)[id]
    a.set_actor_location(_vec(loc), False, True)
    raiz = _raiz_fisica(a)
    if raiz is not None:
        raiz.set_physics_linear_velocity(U.Vector(0.0, 0.0, 0.0), False, "None")
        raiz.wake_all_rigid_bodies()
    return {"movido": id, "loc": _v(a.get_actor_location())}


@op
def sim_door(id: str, angulo: float):
    """Durante o Play, gira a folha da porta na dobradiça (0 = fechada)."""
    w = _mundo_jogo()
    if w is None:
        raise RuntimeError("fora_do_play")
    a = _controlados(w)[id]
    for c in a.get_components_by_class(U.SceneComponent):
        if str(c.get_name()) == "Dobradica":
            c.set_relative_rotation(U.Rotator(pitch=0.0, yaw=float(angulo), roll=0.0), False, False)
            a.set_editor_property("Angulo", float(angulo))
            return {"porta": id, "angulo": round(float(c.get_editor_property("relative_rotation").yaw), 3)}
    raise RuntimeError(f"{id} não tem dobradiça")


def _tick(_dt: float):
    st = _estado()
    andar = getattr(st, "andar", None)
    if andar is None:
        return
    try:
        w = _mundo_jogo()
        peao = andar.get("peao")
        if w is None or peao is None:
            return
        agora = float(U.GameplayStatics.get_time_seconds(w))
        if agora - andar["ultimo"] < PASSO_AMOSTRA_S:
            return
        andar["ultimo"] = agora
        p = peao.get_actor_location()
        andar["amostras"].append([round(agora, 3), round(p.x, 1), round(p.y, 1), round(p.z, 1),
                                  round(float(peao.get_velocity().length()), 1), round(peao.get_actor_rotation().yaw, 1)])
    except Exception as e:  # noqa: BLE001
        andar["erro"] = str(e)


ANDARILHO = "TESTE_ANDARILHO"  # personagem de teste: sem etiqueta do Director, nunca é salvo


def _andarilho(mundo_jogo=None):
    atores = U.GameplayStatics.get_all_actors_of_class(mundo_jogo, U.Character) if mundo_jogo is not None         else [a for a in _eas().get_all_level_actors() if isinstance(a, U.Character)]
    for a in atores:
        if any(str(t) == ANDARILHO for t in a.tags):
            return a
    return None


@op
def walker_place(em: list, velocidade: float = 200.0):
    """Põe no level (fora do Play) o personagem de teste: o `Character` do motor, só a cápsula, com controlador de IA.
    O Python do editor não cria atores dentro do Play, por isso ele é posto antes e retirado depois (walker_remove)."""
    if _mundo_jogo() is not None:
        raise RuntimeError("em_play")
    if _andarilho() is not None:
        raise RuntimeError("o personagem de teste já está no level")
    peao = _eas().spawn_actor_from_class(U.Character, U.Vector(float(em[0]), float(em[1]), float(em[2]) + 90.0), U.Rotator())
    peao.set_actor_label(ANDARILHO)
    peao.set_editor_property("tags", [ANDARILHO])
    peao.set_editor_property("auto_possess_ai", U.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
    peao.set_editor_property("use_controller_rotation_yaw", False)
    mov = peao.character_movement
    mov.set_editor_property("max_walk_speed", float(velocidade))
    mov.set_editor_property("orient_rotation_to_movement", True)
    return {"posto": ANDARILHO, "loc": _v(peao.get_actor_location())}


@op
def walker_remove():
    """Tira do level o personagem de teste."""
    if _mundo_jogo() is not None:
        raise RuntimeError("em_play")
    peao = _andarilho()
    if peao is None:
        return {"tirado": False}
    return {"tirado": bool(_eas().destroy_actor(peao))}


@op
def sim_walk_start(de: list, ate: list, raio_chegada: float = 10.0):
    """Durante o Play, leva o personagem de teste para `de` (pés no chão) e manda andar até `ate` pela navegação do
    Unreal (AIController.MoveToLocation)."""
    w = _mundo_jogo()
    if w is None:
        raise RuntimeError("fora_do_play")
    st = _estado()
    _parar_amostragem()
    peao = _andarilho(w)
    if peao is None:
        raise RuntimeError("o personagem de teste não está no jogo (use walker_place antes do Play)")
    if peao.get_controller() is None:
        peao.spawn_default_controller()
    ctrl = peao.get_controller()
    if ctrl is None or not isinstance(ctrl, U.AIController):
        raise RuntimeError("sem_controlador_de_ia")
    ctrl.stop_movement()
    meia = float(peao.capsule_component.get_scaled_capsule_half_height())
    peao.set_actor_location(U.Vector(float(de[0]), float(de[1]), float(de[2]) + meia + 2.0), False, True)
    peao.character_movement.set_editor_property("velocity", U.Vector(0.0, 0.0, 0.0))
    ctrl.clear_focus()
    resp = ctrl.move_to_location(_vec(ate), acceptance_radius=float(raio_chegada), stop_on_overlap=False,
                                 use_pathfinding=True, project_destination_to_navigation=True, can_strafe=False,
                                 filter_class=None, allow_partial_path=False)
    st.andar = {"peao": peao, "ctrl": ctrl, "amostras": [], "erro": None, "ultimo": 0.0, "ate": list(ate)}
    st.cabo = U.register_slate_post_tick_callback(_tick)
    return {"resposta": getattr(resp, "name", str(resp)), "partida": _v(peao.get_actor_location()),
            "meia_altura": round(meia, 1), "raio": round(float(peao.capsule_component.get_scaled_capsule_radius()), 1)}


@op
def sim_walk_state(amostras_desde: int = -1):
    """Como está o andar: situação do movimento, posição, distância no chão até o destino e, se pedido, amostras."""
    st = _estado()
    andar = getattr(st, "andar", None)
    if andar is None or _mundo_jogo() is None:
        raise RuntimeError("sem_andar")
    peao, ate = andar["peao"], andar["ate"]
    p = peao.get_actor_location()
    situacao = andar["ctrl"].get_move_status()
    d = {"situacao": getattr(situacao, "name", str(situacao)), "loc": _v(p),
         "vel": round(float(peao.get_velocity().length()), 1),
         "distancia_chao": round(math.hypot(p.x - ate[0], p.y - ate[1]), 1),
         "n_amostras": len(andar["amostras"]), "erro": andar["erro"]}
    if amostras_desde >= 0:
        d["amostras"] = andar["amostras"][amostras_desde:]
    return d
