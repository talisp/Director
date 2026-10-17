import unittest
import importlib.util
from director.planejamento import resolver


@unittest.skipUnless(importlib.util.find_spec('ortools'), 'solver opcional em .venv-planejamento')
class Planejamento(unittest.TestCase):
    def test_contencao_e_area_de_uso_com_caso_inviavel(self):
        q={'dimensoes_cm':[200,200],'objetos':[{'id':'a','dimensoes_cm':[100,60,180],'uso_frente_cm':70}],'segundos':1}
        r=resolver(q);self.assertTrue(r['ok']);self.assertEqual(len(r['objetos']),1)
        q['dimensoes_cm']=[80,80]
        self.assertFalse(resolver(q)['ok'])

    def test_reserva_fracionaria_e_compactacao_limitada(self):
        q={'minimo_cm':[80,80],'maximo_cm':[250,250],'objetos':[{'id':'a','dimensoes_cm':[100,60,80],'uso_frente_cm':70}], 'reservas':[[0.5,0.5,10.2,10.2]],'segundos':1}
        r=resolver(q);self.assertTrue(r['ok']);self.assertTrue(r['otimo_no_modelo'])
        self.assertLess(r['area_m2'],6.25)
