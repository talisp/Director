"""Regressões de observação, CLI offline e falso pronto durante AsyncLoadLock."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from director import consultas
from director.nucleo import executor as X, planta as PL
from director.testes.editor_falso import EditorFalso
from director.testes.testes_nucleo import ficha


class Interface(unittest.TestCase):
    def test_tasklist_localizado_nao_depende_de_decodificacao(self):
        from director import lab
        from types import SimpleNamespace
        for saida,esperado in [(b'INFO: nenhuma tarefa \x80 encontrada',False),
                              (b'"UnrealEditor.exe","41664","Console"',True),
                              (b'"python.exe","41664","Console"',False)]:
            with patch.object(lab.subprocess,'run',return_value=SimpleNamespace(stdout=saida)):
                self.assertEqual(lab._pid_vivo(41664),esperado)

    def test_ajuda_e_erros_de_uso_nao_precisam_de_editor(self):
        env = dict(os.environ, DIRECTOR_LAB_PORTA="1")
        for args, code in [(["--help"], 0), (["fazer", "--help"], 0), (["lab", "--help"], 0),
                           (["inexistente"], 2), (["fazer"], 2), (["fazer", "nova", "arquivo_inexistente.json"], 2)]:
            cmd = [sys.executable, "-m", "director.lab", "--help"] if args[0] == "lab" else [sys.executable, "-m", "director", *args]
            r = subprocess.run(cmd, capture_output=True, env=env, timeout=5)
            self.assertEqual(r.returncode, code, r.stderr)
            json.loads(r.stdout.decode("ascii"))
            self.assertNotIn(b"Traceback", r.stdout + r.stderr)

    def test_trava_nativa_nao_vira_pronta_por_nao_estar_construindo(self):
        ed = Mock()
        estados = [False] * 5 + [True] * 4
        ed.chamar.side_effect = [{"medidas": [{"construindo": False, "pronta": s}]} for s in estados]
        self.assertTrue(X._esperar_nav(ed, lambda _: None))
        self.assertEqual(ed.chamar.call_count, 9)

    def test_nav_ausente_ou_travada_termina_sem_falso_sucesso(self):
        ed = Mock()
        ed.chamar.return_value = {"medidas": [{"construindo": None, "pronta": False}]}
        with patch.object(X.time, "monotonic", side_effect=[0, 0, 1, 41]):
            self.assertFalse(X._esperar_nav(ed, lambda _: None))


class Consultas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ed = EditorFalso()
        self.raiz = self.tmp.name
        X.executar("teste", ficha(1), self.ed, self.raiz, pausa=lambda _: None)

    def tearDown(self):
        self.tmp.cleanup()

    def test_observar_separa_planejado_e_edicao_real_sem_escrever(self):
        self.ed.memoria["mesa1"]["loc"] = [250, 200, 1]
        before = copy.deepcopy(self.ed.memoria)
        planta = PL.carregar(self.raiz, "teste")
        self.ed.chamadas.clear()
        r = consultas.observar("teste", self.ed, self.raiz, ["mesa1"])
        self.assertEqual(set(r["objetos"]), {"mesa1"})
        self.assertEqual(r["objetos"]["mesa1"]["planejado"]["x"], 200)
        self.assertEqual(r["objetos"]["mesa1"]["real"]["loc"][0], 250)
        self.assertIsNone(r["objetos"]["mesa1"]["real"]["caixa"])  # dado ausente nao e inventado
        self.assertTrue(r["diferencas"])
        self.assertEqual(self.ed.memoria, before)
        self.assertEqual(PL.carregar(self.raiz, "teste"), planta)
        self.assertTrue(set(self.ed.chamadas) <= {"info", "inventory", "measure"})

    def test_estado_informa_planta_usada_mesmo_em_outro_level(self):
        self.ed.level='/Game/Outra'
        r=X.estado('teste',self.ed,self.raiz)
        self.assertFalse(r['level_aberto'])
        self.assertEqual(r['planta'],PL.caminho(self.raiz,'teste'))
        self.assertEqual(r['nivel'],PL.carregar(self.raiz,'teste')['nivel'])

    def test_recusa_divergencia_com_contexto_sem_inventar_causa_nem_alterar(self):
        del self.ed.memoria['sala1.parede_norte']
        self.ed.memoria['fantasma']=copy.deepcopy(self.ed.memoria['mesa1'])
        antes=copy.deepcopy(self.ed.memoria)
        aplicacoes=self.ed.chamadas.count('apply')
        r=X.executar('teste',{'operacoes':[{'operacao':'mudar','id':'porta1','angulo':90}]},self.ed,self.raiz)
        self.assertFalse(r['ok'])
        self.assertFalse(r['tocou_na_cena'])
        self.assertEqual(r['diagnostico']['codigo'],'planta_editor_divergentes')
        self.assertEqual(r['diagnostico']['planta'],PL.caminho(self.raiz,'teste'))
        self.assertIn('sala1.parede_norte',r['diagnostico']['faltando'])
        self.assertIn('fantasma',r['diagnostico']['sobrando'])
        self.assertNotIn('apagadas',r['porque'])
        self.assertEqual(self.ed.memoria,antes)
        self.assertEqual(self.ed.chamadas.count('apply'),aplicacoes)
        self.assertEqual(PL.carregar(self.raiz,'teste')['revisao'],1)

    def test_observar_cena_nova_informa_como_criar_sem_tocar_editor(self):
        self.ed.chamadas.clear()
        r = consultas.observar("nova", self.ed, self.raiz)
        self.assertFalse(r["existe"])
        self.assertEqual(self.ed.chamadas, [])
        self.assertFalse(os.path.exists(PL.caminho(self.raiz, "nova")))

    def test_sala_selecionada_inclui_seus_objetos(self):
        r = consultas.observar("teste", self.ed, self.raiz, ["sala1"])
        self.assertEqual(set(r["objetos"]), {"sala1", "porta1", "janela1", "mesa1"})

    def test_consulta_nao_abre_outra_cena(self):
        self.ed.level = "/Game/Outro"
        self.ed.chamadas.clear()
        with self.assertRaises(ValueError):
            consultas.observar("teste", self.ed, self.raiz)
        self.assertEqual(self.ed.chamadas, ["info"])

    def test_caminho_parcial_nao_e_completo(self):
        self.ed._measure = lambda **_: {"medidas": [{"existe": True, "parcial": True, "comprimento": 25}]}
        r = consultas.medir("teste", [{"tipo": "caminho", "de": [0, 0, 1], "ate": [100, 100, 1]}], self.ed, self.raiz)
        self.assertFalse(r["medidas"][0]["completo"])

    def test_capsula_e_coordenadas_invalidas_recusadas_antes_do_editor(self):
        for q in [{"tipo": "caminho", "de": [0, float("nan"), 1], "ate": [0, 0, 1]},
                  {"tipo": "varredura", "de": [0, 0, 1], "ate": [0, 0, 1], "raio": 90, "meia_altura": 88}]:
            self.ed.chamadas.clear()
            with self.assertRaises(ValueError):
                consultas.medir("teste", [q], self.ed, self.raiz)
            self.assertEqual(self.ed.chamadas, [])

    def test_repeticao_sem_acoes_nao_inventa_prontidao(self):
        self.ed._measure = lambda **_: {"medidas": [{"pronta": False}]}
        r = X.executar("teste", {"operacoes": [{"operacao": "mudar_sala", "largura_m": 4, "comprimento_m": 4}]}, self.ed, self.raiz, pausa=lambda _: None)
        self.assertTrue(r["ok"])
        self.assertEqual(r["acoes"], [])
        self.assertFalse(r["navegacao_pronta"])
        self.assertFalse(r["conectividade_verificada"])
