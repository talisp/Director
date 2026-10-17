"""Editor de mentira para testar o núcleo sem o Unreal. Imita só o contrato das operações (inventário, aplicar,
salvar, recarregar, Play), não a geometria. Tem botões para provocar as falhas que o executor tem de aguentar."""
import copy

from director.nucleo import pecas as P

NIVEL = "/Game/Director/Cenas/L_teste"
FORA = [{"classe": "/Script/Engine.StaticMeshActor", "caminho": "L.Floor", "rotulo": "Floor", "loc": [0.0, 0.0, -0.5],
         "rot": [0.0, 0.0, 0.0], "escala": [8.0, 8.0, 8.0]}]


class EditorFalso:
    def __init__(self):
        self.level = ""
        self.memoria: dict = {}
        self.disco: dict = {}
        self.fora = copy.deepcopy(FORA)
        self.fora_disco = copy.deepcopy(FORA)
        self.sujo = False
        self.em_play = False
        self.jogo: dict = {}
        self.chamadas: list = []
        self.n_ator = 0
        # botões de falha
        self.falhar_em = None  # id: a ação nesta peça falha (as anteriores do lote já foram feitas)
        self.errar_em = None  # id: a ação "dá certo" mas grava um valor errado (a conferência tem de pegar)
        self.estragar_fora = False  # o aplicar mexe num ator que não é do Director
        self.nao_salvar = False

    def chamar(self, nome: str, **args) -> dict:
        self.chamadas.append(nome)
        return {"ok": True, **getattr(self, "_" + nome)(**args)}

    def _info(self):
        return {"projeto_dir": "lab", "level": self.level, "em_play": self.em_play, "por_salvar": [NIVEL] if self.sujo else []}

    def _level_ensure(self, caminho, modelo=""):
        self.level = caminho
        return {"estado": "ja_aberto", "level": caminho}

    def _inventory(self, variaveis, detalhes=False):
        return {"level": self.level, "controlados": copy.deepcopy(self.memoria), "fora": copy.deepcopy(self.fora),
                "por_salvar": [self.level] if self.sujo else []}

    def _apply(self, acoes):
        feitos = []
        for a in acoes:
            if a["id"] == self.falhar_em:
                self.sujo = True
                return {"aplicado": False, "erro": f"{a['id']}: falha provocada", "feitos": feitos}
            if a["acao"] == "remover":
                del self.memoria[a["id"]]
            else:
                if a["acao"] == "criar":
                    self.n_ator += 1
                    padrao = dict(P.PECAS[a["tipo"]]["variaveis"]) if a["tipo"] in P.PECAS else {}
                    self.memoria[a["id"]] = {"classe": a["classe"], "caminho": f"L.Ator_{self.n_ator}", "rotulo": a["id"], "tipo": a["tipo"],
                                             "loc": [0.0, 0.0, 0.0], "rot": [0.0, 0.0, 0.0], "escala": [1.0, 1.0, 1.0],
                                             "params": padrao, "pontos": {}}
                m = self.memoria[a["id"]]
                for k in ("loc", "rot", "escala"):
                    if k in a:
                        m[k] = [float(v) for v in a[k]]
                m["params"].update({k: float(v) for k, v in (a.get("params") or {}).items()})
                if "objeto" in a:
                    m["objeto"]={k:v for k,v in a["objeto"].items() if k not in ("adotar","duplicar","converter")}
                    origem=a["objeto"].get("adotar")
                    if origem:self.fora=[o for o in self.fora if o['caminho']!=origem]
                if a["id"] == self.errar_em:
                    m["loc"] = [m["loc"][0] + 3.0, m["loc"][1], m["loc"][2]]
            feitos.append([a["id"], a["acao"]])
        if self.estragar_fora:
            self.fora[0]["loc"][0] += 10.0
        self.sujo = True
        return {"aplicado": True, "erro": None, "feitos": feitos}

    def _measure(self, consultas, mundo="editor"):
        return {"medidas": [{"disponivel": True, "construindo": False, "construindo_ou_bloqueada": False,
                             "malhas": ["nav_falsa"], "pronta": True, "conectividade_verificada": False} for _ in consultas]}

    def _save(self):
        if self.nao_salvar:
            return {"salvou": False, "pacotes": [], "alheios_por_salvar": [], "por_salvar": [self.level]}
        self.disco, self.fora_disco, self.sujo = copy.deepcopy(self.memoria), copy.deepcopy(self.fora), False
        return {"salvou": True, "pacotes": [self.level], "alheios_por_salvar": [], "por_salvar": []}

    def _reload_level(self):
        self.memoria, self.fora, self.sujo = copy.deepcopy(self.disco), copy.deepcopy(self.fora_disco), False
        return {"recarregou": True, "level": self.level, "por_salvar": []}

    def _sim_read(self):
        if not self.em_play:
            raise RuntimeError("fora_do_play")
        return {"tempo": 1.0, "objetos": copy.deepcopy(self.jogo)}

    def _play_stop(self):
        self.em_play = False
        return {"pedido": "parar"}

    # ajudas dos testes
    def mexer_a_mao(self, pid: str, **campos):
        """Imita uma pessoa mexendo no editor (sem salvar)."""
        for k, v in campos.items():
            if k == "params":
                self.memoria[pid]["params"].update(v)
            else:
                self.memoria[pid][k] = v
        self.sujo = True
