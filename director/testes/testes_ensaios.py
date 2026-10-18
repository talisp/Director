import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from director import ensaios as E
from director.testes.editor_falso import EditorFalso


class Ensaios(unittest.TestCase):
    def test_script_exato_hash_e_mudanca_real_registrados(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = E.criar("teste", "mover objeto", tmp)
            src = Path(tmp) / "original.py"
            raw = b"resultado = {'ok': True}\n"
            src.write_bytes(raw)
            ed = EditorFalso()
            def rodar(**kw):
                ed.fora[0]["loc"][0] += 10
                return {"resultado": {"ok": True}}
            ed._dev_exec = rodar
            r = E.executar(e["id"], src, ed, tmp)
            src.write_text("# alterado depois")
            self.assertTrue(r["ok"])
            self.assertEqual(Path(r["registro"]).with_name("script.py").read_bytes(), raw)
            self.assertEqual(r["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(r["mudancas"]["alterados"], ["ator:L.Floor"])
            self.assertEqual(len(E.listar(e["id"], tmp)["ensaios"][0]["execucoes"]), 1)

    def test_erro_apos_mutacao_nao_perde_evidencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            e = E.criar("falha", "erro provocado", tmp)
            src = Path(tmp) / "falha.py"
            src.write_text("raise RuntimeError('falha')")
            ed = EditorFalso()
            def rodar(**kw):
                ed.fora[0]["loc"][0] += 10
                raise RuntimeError("falha provocada")
            ed._dev_exec = rodar
            r = E.executar(e["id"], src, ed, tmp)
            self.assertFalse(r["ok"])
            d = json.loads(Path(r["registro"]).read_text())
            self.assertIn("falha provocada", d["erro"]["mensagem"])
            self.assertTrue(d["mudancas"]["alterados"])

    def test_identificador_nao_e_caminho(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                E.listar("../outro", tmp)
