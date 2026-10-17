"""Testes do reparo da ferramenta clarify, sem Hermes nem Unreal."""
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


if __name__ == "__main__":
    unittest.main()
