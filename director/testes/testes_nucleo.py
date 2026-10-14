"""Testes do núcleo do Director, SEM o Unreal (critério G e a parte de F que não precisa do editor).

Rodar, na raiz:  venv\\Scripts\\python.exe -m unittest director.testes.testes_nucleo -v
Cada regra tem o seu caso que TEM de reprovar.
"""
import copy
import json
import os
import shutil
import tempfile
import unittest

from director import ponte
from director.nucleo import derivar as D
from director.nucleo import executor as X
from director.nucleo import operacoes as OP
from director.nucleo import plano as PN
from director.nucleo import planta as PL
from director.nucleo import regua as R
from director.testes.editor_falso import EditorFalso

FICHAS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fichas")


def ficha(n: int) -> dict:
    with open(os.path.join(FICHAS, f"comando{n}.json"), encoding="utf-8") as f:
        return json.load(f)


def planta_apos(*ns: int) -> dict:
    p = PL.nova("teste")
    for n in ns:
        p, _ = OP.aplicar_ficha(p, ficha(n))
    return p


class Operacoes(unittest.TestCase):
    def test_comando1_cria_sala_porta_janela_mesa(self):
        p = planta_apos(1)
        self.assertEqual(sorted(p["objetos"]), ["janela1", "mesa1", "porta1", "sala1"])
        s = p["objetos"]["sala1"]
        self.assertEqual((s["largura"], s["comprimento"], s["altura"]), (400.0, 400.0, 270.0))
        self.assertEqual((p["objetos"]["porta1"]["parede"], p["objetos"]["porta1"]["posicao"]), ("sul", 200.0))
        self.assertEqual((p["objetos"]["mesa1"]["x"], p["objetos"]["mesa1"]["y"]), (200.0, 200.0))

    def test_comando1_pecas_derivadas(self):
        alvo = D.derivar(planta_apos(1))
        self.assertEqual(sorted(alvo), ["janela1", "mesa1", "porta1", "sala1.nav", "sala1.parede_leste", "sala1.parede_norte",
                                        "sala1.parede_oeste", "sala1.parede_sul", "sala1.piso"])
        sul = alvo["sala1.parede_sul"]
        self.assertEqual(sul["loc"], [-15.0, -7.5, 1.0])
        self.assertEqual((sul["params"]["Comprimento"], sul["params"]["VaoLargura"], sul["params"]["VaoCentro"], sul["params"]["VaoAltura"]),
                         (430.0, 100.0, 215.0, 210.0))
        self.assertEqual(alvo["sala1.parede_norte"]["params"]["VaoLargura"], 0.0)
        leste = alvo["sala1.parede_leste"]
        self.assertEqual((leste["loc"], leste["rot"][1]), ([407.5, 0.0, 1.0], 90.0))
        self.assertEqual((leste["params"]["VaoCentro"], leste["params"]["VaoBase"], leste["params"]["VaoAltura"]), (200.0, 90.0, 110.0))
        self.assertEqual((alvo["porta1"]["loc"], alvo["porta1"]["rot"][1]), ([150.0, -7.5, 1.0], 0.0))
        self.assertEqual(alvo["janela1"]["loc"], [407.5, 140.0, 91.0])

    def test_comando2_aumenta_e_muda_a_porta(self):
        antes, depois = planta_apos(1), planta_apos(1, 2)
        self.assertEqual(depois["objetos"]["sala1"]["largura"], 500.0)
        self.assertEqual((depois["objetos"]["porta1"]["parede"], depois["objetos"]["porta1"]["posicao"]), ("norte", 200.0))
        self.assertEqual(depois["objetos"]["mesa1"], antes["objetos"]["mesa1"])  # a mesa não foi tocada
        alvo = D.derivar(depois)
        self.assertEqual((alvo["porta1"]["loc"], alvo["porta1"]["rot"][1]), ([250.0, 407.5, 1.0], 180.0))  # abre para dentro
        self.assertEqual(alvo["sala1.parede_sul"]["params"]["VaoLargura"], 0.0)
        self.assertEqual(alvo["sala1.parede_norte"]["params"]["VaoLargura"], 100.0)

    def test_comando3_prato_e_copo_sobre_a_mesa(self):
        p = planta_apos(1, 2, 3)
        prato, copo = p["objetos"]["prato1"], p["objetos"]["copo1"]
        self.assertEqual((prato["sobre"], copo["sobre"]), ("mesa1", "mesa1"))
        self.assertAlmostEqual(prato["z"], 1.0 + 75.0 + 1.0 + 0.1)  # chão + mesa + meia altura do prato + folga
        self.assertAlmostEqual(copo["z"], 1.0 + 75.0 + 5.0 + 0.1)
        self.assertNotEqual((prato["x"], prato["y"]), (copo["x"], copo["y"]))

    def test_ficha_recusada_nao_muda_a_planta(self):
        base = planta_apos(1)
        casos = {
            "operação desconhecida": [{"operacao": "explodir"}],
            "campo desconhecido": [{"operacao": "mudar_sala", "largura": 5}],
            "número em texto": [{"operacao": "mudar_sala", "largura_m": "cinco"}],
            "falta campo": [{"operacao": "criar_sala", "largura_m": 4}],
            "janela maior que a parede": [{"operacao": "mudar", "id": "janela1", "largura_m": 4.5}],
            "sala encolhe e a mesa fica fora": [{"operacao": "mudar_sala", "largura_m": 2.2}],
            "porta em cima da janela": [{"operacao": "mudar", "id": "porta1", "parede": "leste"}],
            "peça que não existe": [{"operacao": "mudar", "id": "porta9", "angulo": 90}],
            "nome repetido": [{"operacao": "colocar", "tipo": "mesa", "id": "mesa1"}],
            "mesa em cima da mesa": [{"operacao": "colocar", "tipo": "mesa"}],
            "campo de outro tipo": [{"operacao": "mudar", "id": "mesa1", "angulo": 90}],
            "sala pequena demais": [{"operacao": "criar_sala", "largura_m": 1, "comprimento_m": 3, "x_m": 30}],
            "remover sala com peças": [{"operacao": "remover", "id": "sala1"}],
            "segunda operação ruim desfaz a primeira": [{"operacao": "mudar", "id": "porta1", "angulo": 90},
                                                      {"operacao": "mudar_sala", "largura_m": 99}],
        }
        for nome, ops in casos.items():
            copia = copy.deepcopy(base)
            with self.assertRaises(OP.Invalida, msg=nome):
                OP.aplicar_ficha(base, {"operacoes": ops})
            self.assertEqual(base, copia, nome)
        for ruim in ({}, {"operacoes": []}, {"operacoes": "x"}, {"operacoes": [1]}, {"operacoes": [{"operacao": "remover", "id": "mesa1"}], "extra": 1}):
            with self.assertRaises(OP.Invalida):
                OP.aplicar_ficha(base, ruim)

    def test_recusa_diz_qual_peca(self):
        p, _ = OP.aplicar_ficha(planta_apos(1), {"operacoes": [{"operacao": "mudar", "id": "mesa1", "x_m": 3.2}]})
        with self.assertRaises(OP.Invalida) as c:
            OP.aplicar_ficha(p, {"operacoes": [{"operacao": "mudar_sala", "largura_m": 3.5}]})
        self.assertIn("mesa1", str(c.exception))  # encolher deixaria a mesa de fora
        with self.assertRaises(OP.Invalida) as c:
            OP.aplicar_ficha(planta_apos(1), {"operacoes": [{"operacao": "mudar_sala", "largura_m": 2.2}]})
        self.assertIn("porta1", str(c.exception))  # aqui quem não cabe é a porta

    def test_objeto_sem_mesa_e_recusado(self):
        p, _ = OP.aplicar_ficha(PL.nova("t"), {"operacoes": [{"operacao": "criar_sala", "largura_m": 4, "comprimento_m": 4}]})
        with self.assertRaises(OP.Invalida):
            OP.aplicar_ficha(p, {"operacoes": [{"operacao": "colocar", "tipo": "copo"}]})

    def test_dois_vaos_na_mesma_parede_dividem_a_parede(self):
        p, _ = OP.aplicar_ficha(planta_apos(1), {"operacoes": [{"operacao": "colocar", "tipo": "janela", "parede": "sul", "posicao_m": 3.2, "largura_m": 0.8}]})
        alvo = D.derivar(p)
        a, b = alvo["sala1.parede_sul"], alvo["sala1.parede_sul_2"]
        self.assertAlmostEqual(a["params"]["Comprimento"] + b["params"]["Comprimento"], 430.0)
        self.assertAlmostEqual(a["loc"][0] + a["params"]["Comprimento"], b["loc"][0])  # um começa onde o outro acaba
        self.assertEqual(a["params"]["VaoCentro"], 215.0)  # a porta continua no mesmo ponto do mundo
        self.assertAlmostEqual(b["loc"][0] + b["params"]["VaoCentro"], 320.0)
        self.assertEqual((b["params"]["VaoBase"], b["params"]["VaoLargura"]), (90.0, 80.0))

    def test_mover_a_mesa_leva_o_que_esta_sobre_ela(self):
        p = planta_apos(1, 2, 3)
        antes = copy.deepcopy(p["objetos"])
        q, _ = OP.aplicar_ficha(p, {"operacoes": [{"operacao": "mudar", "id": "mesa1", "x_m": 3.0, "y_m": 2.5}]})
        for nome in ("prato1", "copo1"):
            self.assertAlmostEqual(q["objetos"][nome]["x"] - antes[nome]["x"], 100.0)
            self.assertAlmostEqual(q["objetos"][nome]["y"] - antes[nome]["y"], 50.0)

    def test_capacidades_e_texto_puro(self):
        cap = json.loads(json.dumps(OP.capacidades()))
        self.assertEqual(sorted(cap["operacoes"]), ["colocar", "criar_sala", "mudar", "mudar_sala", "remover"])


class Plano(unittest.TestCase):
    def _inventario_de(self, planta: dict) -> dict:
        return {pid: {**copy.deepcopy(p), "caminho": "L." + pid, "pontos": {}} for pid, p in D.derivar(planta).items()}

    def test_cena_igual_nao_gera_acao(self):
        p = planta_apos(1, 2, 3)
        self.assertEqual(PN.planejar(D.derivar(p), self._inventario_de(p)), [])
        self.assertEqual(PN.diferencas(D.derivar(p), self._inventario_de(p)), [])

    def test_comando2_so_atualiza_o_que_mudou(self):
        inv = self._inventario_de(planta_apos(1))
        acoes = PN.planejar(D.derivar(planta_apos(1, 2)), inv)
        self.assertEqual({a["acao"] for a in acoes}, {"atualizar"})  # nada é apagado nem recriado
        tocados = {a["id"] for a in acoes}
        self.assertNotIn("mesa1", tocados)
        self.assertNotIn("sala1.parede_oeste", tocados)
        self.assertEqual(tocados, {"sala1.piso", "sala1.parede_sul", "sala1.parede_norte", "sala1.parede_leste", "sala1.nav",
                                   "porta1", "janela1"})
        sul = next(a for a in acoes if a["id"] == "sala1.parede_sul")
        self.assertNotIn("loc", sul)  # a parede sul não sai do lugar: só mudam o comprimento e o vão
        self.assertEqual(sorted(sul["params"]), ["Comprimento", "VaoAltura", "VaoCentro", "VaoLargura"])

    def test_diferenca_pequena_demais_nao_conta_e_grande_conta(self):
        p = planta_apos(1)
        inv = self._inventario_de(p)
        inv["mesa1"]["loc"][0] += 0.01
        self.assertEqual(PN.diferencas(D.derivar(p), inv), [])
        inv["mesa1"]["loc"][0] += 0.2
        self.assertEqual([d["o_que"] for d in PN.diferencas(D.derivar(p), inv)], ["loc"])
        inv["sala1.parede_sul"]["params"]["VaoLargura"] = 90.0
        del inv["janela1"]
        inv["intruso"] = inv["mesa1"]
        self.assertEqual(sorted(d["o_que"] for d in PN.diferencas(D.derivar(p), inv)), ["falta", "loc", "params", "sobra"])

    def test_conciliar_adota_edicao_manual(self):
        p = planta_apos(1, 2, 3)
        inv = self._inventario_de(p)
        inv["mesa1"]["loc"] = [230.0, 200.0, 1.0]
        inv["porta1"]["params"]["Angulo"] = 70.0
        inv["sala1.parede_oeste"]["params"]["Altura"] = 300.0
        del inv["janela1"]
        nova, rel = PN.conciliar(p, inv)
        self.assertEqual(nova["objetos"]["mesa1"]["x"], 230.0)
        self.assertEqual(nova["objetos"]["porta1"]["angulo"], 70.0)
        self.assertAlmostEqual(nova["objetos"]["prato1"]["x"] - p["objetos"]["prato1"]["x"], 30.0)  # foi junto com a mesa
        self.assertEqual(sorted(rel["levados_junto"]), ["copo1", "prato1"])
        self.assertEqual(rel["estrutura_divergente"], ["sala1.parede_oeste"])
        self.assertEqual(rel["faltando"], ["janela1"])
        self.assertEqual(p["objetos"]["mesa1"]["x"], 200.0)  # a planta recebida não muda


class Executor(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="d2_teste_")
        self.ed = EditorFalso()

    def tearDown(self):
        shutil.rmtree(self.raiz, ignore_errors=True)

    def fazer(self, f) -> dict:
        return X.executar("teste", f, self.ed, self.raiz, pausa=lambda _s: None)

    def registro(self) -> list:
        with open(os.path.join(self.raiz, "teste", "registro.jsonl"), encoding="utf-8") as f:
            return [json.loads(x) for x in f]

    def test_tres_comandos(self):
        r1, r2, r3 = self.fazer(ficha(1)), self.fazer(ficha(2)), self.fazer(ficha(3))
        self.assertTrue(r1["ok"] and r2["ok"] and r3["ok"], (r1, r2, r3))
        self.assertEqual((r1["revisao"], r2["revisao"], r3["revisao"]), (1, 2, 3))
        self.assertEqual({a[0] for a in r1["acoes"]}, {"criar"})
        self.assertEqual({a[0] for a in r2["acoes"]}, {"atualizar"})
        self.assertEqual(sorted(a[1] for a in r3["acoes"]), ["copo1", "prato1"])
        self.assertEqual(len(r2["atores_mantidos"]), 9)  # todos os atores do comando 1 continuam os mesmos
        self.assertEqual(self.ed.memoria, self.ed.disco)
        self.assertEqual(PL.carregar(self.raiz, "teste")["revisao"], 3)
        self.assertEqual([x["evento"] for x in self.registro()], ["inicio", "fim"] * 3)

    def test_ficha_invalida_nao_toca_na_cena(self):
        self.fazer(ficha(1))
        antes, n = copy.deepcopy(self.ed.memoria), self.ed.chamadas.count("apply")
        r = self.fazer({"operacoes": [{"operacao": "mudar_sala", "largura_m": 2.2}]})
        self.assertEqual((r["ok"], r["motivo"], r["tocou_na_cena"]), (False, "recusado", False))
        self.assertIn("porta1", r["porque"])
        self.assertEqual(self.ed.memoria, antes)
        self.assertEqual(self.ed.chamadas.count("apply"), n)
        self.assertEqual(PL.carregar(self.raiz, "teste")["revisao"], 1)
        self.assertEqual(self.registro()[-1]["motivo"], "recusado")

    def test_falha_no_meio_desfaz_tudo(self):
        self.fazer(ficha(1))
        antes = copy.deepcopy(self.ed.memoria)
        self.ed.falhar_em = "sala1.parede_leste"
        r = self.fazer(ficha(2))
        self.assertEqual((r["ok"], r["motivo"], r["recuperado"], r["cena_igual_a_antes"]), (False, "falha_ao_aplicar", True, True))
        self.assertEqual(self.ed.memoria, antes)
        self.assertEqual(PL.carregar(self.raiz, "teste")["revisao"], 1)

    def test_conferencia_pega_valor_errado(self):
        self.fazer(ficha(1))
        antes = copy.deepcopy(self.ed.memoria)
        self.ed.errar_em = "porta1"
        r = self.fazer(ficha(2))
        self.assertEqual((r["ok"], r["motivo"], r["cena_igual_a_antes"]), (False, "conferencia_falhou", True))
        self.assertEqual(r["diferencas"][0]["id"], "porta1")
        self.assertEqual(self.ed.memoria, antes)

    def test_conferencia_pega_ator_alheio_mexido(self):
        self.fazer(ficha(1))
        self.ed.estragar_fora = True
        r = self.fazer(ficha(2))
        self.assertEqual((r["ok"], r["motivo"], r["resto_da_cena_igual"], r["cena_igual_a_antes"]), (False, "conferencia_falhou", False, True))

    def test_nao_salvou_nao_vale(self):
        self.fazer(ficha(1))
        self.ed.nao_salvar = True
        r = self.fazer(ficha(2))
        self.assertEqual((r["ok"], r["motivo"]), (False, "nao_salvou"))
        self.assertEqual(PL.carregar(self.raiz, "teste")["revisao"], 1)

    def test_edicao_manual_e_adotada_e_preservada(self):
        self.fazer(ficha(1))
        self.ed.mexer_a_mao("mesa1", loc=[230.0, 200.0, 1.0])
        r = self.fazer(ficha(2))
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["adotados"][0]["id"], "mesa1")
        self.assertNotIn("mesa1", [a[1] for a in r["acoes"]])  # o Director não mexe na mesa
        self.assertEqual(self.ed.memoria["mesa1"]["loc"], [230.0, 200.0, 1.0])
        self.assertEqual(PL.carregar(self.raiz, "teste")["objetos"]["mesa1"]["x"], 230.0)

    def test_peca_apagada_a_mao_faz_recusar(self):
        self.fazer(ficha(1))
        del self.ed.memoria["janela1"]
        r = self.fazer(ficha(2))
        self.assertEqual((r["ok"], r["motivo"], r["tocou_na_cena"]), (False, "recusado", False))
        self.assertIn("janela1", r["porque"])
        r = self.fazer({"operacoes": [{"operacao": "remover", "id": "janela1"}]})
        self.assertTrue(r["ok"], r)
        self.assertNotIn("janela1", PL.carregar(self.raiz, "teste")["objetos"])

    def test_peca_com_etiqueta_que_a_planta_nao_conhece_faz_recusar(self):
        self.fazer(ficha(1))
        self.ed.memoria["fantasma"] = copy.deepcopy(self.ed.memoria["mesa1"])
        r = self.fazer(ficha(2))
        self.assertEqual((r["ok"], r["tocou_na_cena"]), (False, False))
        self.assertIn("fantasma", self.ed.memoria)  # não foi apagada

    def test_em_play_recusa(self):
        self.fazer(ficha(1))
        self.ed.em_play = True
        self.assertEqual(self.fazer(ficha(2))["motivo"], "recusado")

    def test_incorporar_grava_o_que_o_play_mudou(self):
        for n in (1, 2, 3):
            self.fazer(ficha(n))
        p = PL.carregar(self.raiz, "teste")
        copo, prato = p["objetos"]["copo1"], p["objetos"]["prato1"]
        self.ed.em_play = True
        self.ed.jogo = {"copo1": {"loc": [copo["x"] + 12.0, copo["y"] - 4.0, copo["z"] - 0.1], "rot": [0.0, 35.0, 0.0], "vel": 0.0},
                        "prato1": {"loc": [prato["x"] + 150.0, prato["y"], 2.0], "rot": [0.0, 0.0, 0.0], "vel": 0.0}}
        r = X.incorporar("teste", self.ed, self.raiz, pausa=lambda _s: None)
        self.assertTrue(r["ok"], r)
        q = PL.carregar(self.raiz, "teste")
        self.assertAlmostEqual(q["objetos"]["copo1"]["x"], copo["x"] + 12.0)
        self.assertEqual(q["objetos"]["copo1"]["sobre"], "mesa1")  # continua sobre a mesa
        self.assertIsNone(q["objetos"]["prato1"]["sobre"])  # caiu no chão: deixou de estar sobre a mesa
        self.assertEqual(self.ed.memoria["copo1"]["loc"], self.ed.jogo["copo1"]["loc"])
        self.assertEqual(self.ed.memoria, self.ed.disco)

    def test_incorporar_fora_do_play_falha(self):
        self.fazer(ficha(1))
        with self.assertRaises(RuntimeError):
            X.incorporar("teste", self.ed, self.raiz, pausa=lambda _s: None)


class ClienteFalso:
    def __init__(self, projeto_dir: str):
        self.projeto_dir, self.ops = projeto_dir, []

    def list_toolsets(self) -> str:
        return "- PythonTypes.DirectorTools_0xABC: x"

    def call(self, toolset, tool, **kw):
        self.ops.append(kw.get("name"))
        return json.dumps({"ok": True, "projeto_dir": self.projeto_dir})


class Protecao(unittest.TestCase):
    def test_recusa_a_porta_do_projeto_do_filme(self):
        for url in ("http://127.0.0.1:8001/mcp", "http://localhost:8001/mcp"):
            with self.assertRaises(ponte.Recusado):
                ponte.Ponte("teste", url=url)

    def test_recusa_editor_que_nao_e_o_laboratorio(self):
        cliente = ClienteFalso("D:/Projetos/OutroProjeto/")
        p = ponte.Ponte("teste", cliente=cliente)
        with self.assertRaises(ponte.Recusado):
            p.chamar("apply", acoes=[])
        self.assertEqual(cliente.ops, ["info"])  # só perguntou quem era: a ação nunca saiu

    def test_aceita_o_laboratorio(self):
        from director import config as C
        cliente = ClienteFalso(C.LAB_DIR.replace("\\", "/") + "/")
        ponte.Ponte("teste", cliente=cliente).chamar("inventory", variaveis={})
        self.assertEqual(cliente.ops, ["info", "inventory"])


class Reguas(unittest.TestCase):
    def test_medida_interna(self):
        self.assertTrue(R.medida_interna(200.0, 200.5, 400.0)["ok"])
        self.assertFalse(R.medida_interna(200.0, 203.0, 400.0)["ok"])  # 3 cm a mais reprova

    def test_repouso_e_queda(self):
        self.assertTrue(R.repouso([0, 0, 77.0], [0.3, 0.2, 76.9])["ok"])
        self.assertFalse(R.repouso([0, 0, 77.0], [0, 0, 75.5])["ok"])  # desceu 1,5 cm
        self.assertFalse(R.repouso([0, 0, 77.0], [1.5, 0, 77.0])["ok"])  # andou 1,5 cm
        self.assertTrue(R.caiu([0, 0, 82.0], [5.0, 0, 6.0])["ok"])
        self.assertFalse(R.caiu([0, 0, 82.0], [0, 0, 81.9])["ok"])  # ficou na mesa: não é queda

    def test_chegou(self):
        self.assertTrue(R.chegou(8.0, "IDLE", 0.0)["ok"])
        self.assertFalse(R.chegou(180.0, "IDLE", 0.0)["ok"])  # parou longe (porta fechada)
        self.assertFalse(R.chegou(8.0, "MOVING", 120.0)["ok"])  # ainda andando

    def test_mesmo_lugar(self):
        self.assertTrue(R.mesmo_lugar([1, 2, 3], [1, 2, 3.05])["ok"])
        self.assertFalse(R.mesmo_lugar([1, 2, 3], [1, 2.3, 3])["ok"])


if __name__ == "__main__":
    unittest.main()
