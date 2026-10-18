"""Testes da guarda (clarify, esperas e mesma cena), sem Hermes nem Unreal."""
import importlib.util
import json
import os
import unittest

_AQUI = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "director_guarda", os.path.join(_AQUI, "plugins", "director-guarda", "__init__.py")
)
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)


class Perguntas(unittest.TestCase):
    def test_repara_lista_em_texto(self):
        certas = [{"question": "Onde?", "choices": ["Aqui", "Ali"]}]
        texto = json.dumps(certas, ensure_ascii=False)
        self.assertEqual(G.consertar_perguntas({"questions": texto}), {"questions": certas})
        self.assertEqual(G.consertar_perguntas({"questions": texto + "}"}), {"questions": certas})
        self.assertEqual(G.consertar_perguntas({"questions": texto[:-1]}), {"questions": certas})

    def test_repara_opcoes(self):
        args = {"questions": [{"question": "Qual?", "choices": [{"label": "Primeira"}]}]}
        self.assertEqual(G.consertar_perguntas(args)["questions"][0]["choices"], ["Primeira"])

    def test_nao_cria_aprovacoes_nem_bloqueios(self):
        for name, args in (
            ("terminal", {"command": "python -m director fazer sala ficha.json"}),
            ("write_file", {"path": "director/operacoes.py", "content": "x"}),
            ("patch", {"path": "director/operacoes.py"}),
            ("tts", {"text": "Olá"}),
        ):
            self.assertIsNone(G._antes_da_ferramenta(name, args))

    def test_clarify_reparado_no_hook(self):
        result = G._antes_da_ferramenta("clarify", {"questions": '{"question":"Qual?"}'})
        self.assertEqual(result["action"], "modify")
        self.assertEqual(result["args"]["questions"][0]["question"], "Qual?")


# Comandos reais do teste de 17/10 (encurtados).
LACO_1651 = "\n".join([
    'cd C:/Users/x/Director && PY=C:/Users/x/venv/Scripts/python.exe; for S in "2.9 3.3"; do set -- $S',
    '$PY -m director fazer hermes_quarto_final work/fichas/quarto_resize.json >/dev/null 2>&1',
    'R=$($PY -m director planejar hermes_quarto_final work/fichas/quarto_planejar.json 2>&1)',
    'done'])
LACO_1652 = LACO_1651.replace('"2.9 3.3"', '"3.0 3.2"')


class Esperas(unittest.TestCase):
    def test_sleep_longo_e_barrado_e_curto_passa(self):
        for cmd in ("sleep 240", "sleep 300 && echo x", "sleep 2m", "Start-Sleep -Seconds 90", "timeout /t 120"):
            r = G._antes_da_ferramenta("terminal", {"command": cmd})
            self.assertEqual(r["action"], "block", cmd)
            self.assertIn("60 s", r["message"])
        for cmd in ("sleep 55", "sleep 60", "echo sleeping 300"):
            self.assertIsNone(G._antes_da_ferramenta("terminal", {"command": cmd}), cmd)

    def test_time_sleep_no_codigo(self):
        self.assertEqual(G._antes_da_ferramenta("execute_code", {"code": "import time; time.sleep(120)"})["action"], "block")
        self.assertIsNone(G._antes_da_ferramenta("execute_code", {"code": "time.sleep(30)"}))

    def test_process_wait_limitado_a_60(self):
        r = G._antes_da_ferramenta("process", {"action": "wait", "session_id": "p1", "timeout_seconds": 120})
        self.assertEqual(r, {"action": "modify", "args": {"action": "wait", "session_id": "p1", "timeout_seconds": 60}})
        self.assertIsNone(G._antes_da_ferramenta("process", {"action": "wait", "session_id": "p1", "timeout_seconds": 45}))
        self.assertIsNone(G._antes_da_ferramenta("process", {"action": "poll", "session_id": "p1"}))

    def test_tool_call_embrulhado(self):
        r = G._antes_da_ferramenta("tool_call", {"calls": [{"name": "process_manage", "arguments": {"action": "wait", "session_id": "p", "timeout_seconds": 120}}]})
        self.assertEqual(r["args"]["calls"][0]["arguments"]["timeout_seconds"], 60)
        r = G._antes_da_ferramenta("tool_call", {"calls": json.dumps([{"name": "terminal", "arguments": {"command": "sleep 240"}}])})
        self.assertEqual(r["action"], "block")


class MesmaCena(unittest.TestCase):
    def test_cenas_alteradas(self):
        self.assertEqual(G.cenas_alteradas(LACO_1651), {"hermes_quarto_final"})
        self.assertEqual(G.cenas_alteradas("python -m director planejar sala p.json"), set())
        self.assertEqual(G.cenas_alteradas("python -m director navegacao n.json"), {"*"})
        self.assertEqual(G.cenas_alteradas("python -m director ensaio executar ID t.py"), {"*"})
        self.assertEqual(G.cenas_alteradas("python -m director ensaio criar nome p.txt"), set())

    def test_segunda_varredura_na_mesma_cena_e_barrada(self):
        r = G._regra("terminal", {"command": LACO_1652, "background": True}, rodando=[LACO_1651])
        self.assertEqual(r["action"], "block")
        self.assertIn("mesma cena", r["message"])

    def test_outra_cena_leitura_e_nada_rodando_passam(self):
        self.assertIsNone(G._regra("terminal", {"command": "python -m director fazer outra f.json"}, rodando=[LACO_1651]))
        self.assertIsNone(G._regra("terminal", {"command": "python -m director planejar hermes_quarto_final p.json"}, rodando=[LACO_1651]))
        self.assertIsNone(G._regra("terminal", {"command": LACO_1652}, rodando=["python -m director planejar x p.json"]))
        self.assertIsNone(G._regra("terminal", {"command": LACO_1652}, rodando=[]))
        self.assertEqual(G._regra("terminal", {"command": LACO_1652}, rodando=["python -m director navegacao n.json"])["action"], "block")


if __name__ == "__main__":
    unittest.main()
