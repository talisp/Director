import copy
import json
from pathlib import Path
import tempfile
import unittest
from director import estado_local as E
from director.nucleo import planta as PL, derivar as D
from director.testes.testes_nucleo import planta_apos
from director.testes.editor_falso import EditorFalso
from hermes import instalar_perfil as H
from unittest.mock import patch


class Vinculo(unittest.TestCase):
    def preparar(self, pasta):
        origem = Path(pasta) / 'checkout' / 'cenas'
        lab = Path(pasta) / 'lab'
        vinculo = lab / 'Saved/Director/vinculo.json'
        planta = planta_apos(1)
        PL.gravar(str(origem), planta)
        editor = EditorFalso()
        editor.level = planta['nivel']
        editor.memoria = copy.deepcopy(D.derivar(planta))
        return origem, lab, vinculo, editor

    def test_vinculo_preserva_fontes_e_dois_checkouts_usam_mesma_planta(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem, lab, vinculo, editor = self.preparar(tmp)
            bruto = (origem/'teste/planta.json').read_bytes()
            r = E.vincular(origem, editor, lab, vinculo)
            self.assertTrue(r['ok'])
            a = E.resolver(lab, origem, vinculo)
            b = E.resolver(lab, Path(tmp)/'checkout2/cenas', vinculo)
            self.assertEqual(a, b)
            self.assertEqual(Path(a, 'teste/planta.json').read_bytes(), bruto)
            self.assertEqual((origem/'teste/planta.json').read_bytes(), bruto)
            with self.assertRaises(ValueError):E.vincular(origem, editor, lab, vinculo)

    def test_divergencia_recusa_sem_publicar_ou_tocar_atores(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem, lab, vinculo, editor = self.preparar(tmp)
            del editor.memoria['sala1.parede_norte']
            antes = copy.deepcopy(editor.memoria)
            self.assertFalse(E.vincular(origem, editor, lab, vinculo)['ok'])
            self.assertFalse(vinculo.exists())
            self.assertEqual(editor.memoria, antes)
            self.assertNotIn('save', editor.chamadas)
            self.assertNotIn('apply', editor.chamadas)

    def test_falha_em_outra_cena_restaura_level_sem_criar_destino(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem, lab, vinculo, editor = self.preparar(tmp)
            outra = PL.nova('zz_ausente'); PL.gravar(str(origem), outra)
            inicial = editor.level
            chamar = editor._level_ensure
            def abrir(caminho, criar=True):
                if caminho == outra['nivel']:
                    self.assertFalse(criar)
                    raise ValueError('ausente')
                return chamar(caminho, criar=criar)
            editor._level_ensure = abrir
            with self.assertRaises(ValueError):E.vincular(origem, editor, lab, vinculo)
            self.assertEqual(editor.level, inicial)
            self.assertFalse(vinculo.exists())

    def test_vinculo_invalido_nao_recupera_legado_silenciosamente(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem, lab, vinculo, _ = self.preparar(tmp)
            self.assertEqual(E.resolver(lab, origem, vinculo), str(origem))
            vinculo.parent.mkdir(parents=True)
            vinculo.write_text(json.dumps({'formato':1, 'laboratorio':str(lab), 'cenas':str(lab/'sumiu')}))
            with self.assertRaises(ValueError):E.resolver(lab, origem, vinculo)

    def test_diff_skill_e_somente_leitura_e_preserva_notas(self):
        with tempfile.TemporaryDirectory() as tmp:
            origem = Path(tmp)/'fonte'; origem.mkdir()
            perfil = Path(tmp)/'perfil'; perfil.mkdir()
            (origem/'SOUL.md').write_text('regra {{DIRECTOR}}\n', encoding='utf-8')
            instalado = perfil/'SOUL.md'; instalado.write_text('regra local\nnota do Hermes\n', encoding='utf-8')
            antes = instalado.read_bytes()
            with patch.object(H, 'AQUI', str(origem)), patch.object(H, 'ARQUIVOS', ('SOUL.md',)):
                r = H.conferir(str(perfil))
            self.assertFalse(r['igual'])
            self.assertIn('+nota do Hermes', r['arquivos'][0]['diff'])
            self.assertEqual(instalado.read_bytes(), antes)
