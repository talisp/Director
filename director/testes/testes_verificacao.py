import unittest
from director.verificacao import contencao


class Geometria(unittest.TestCase):
    def test_excesso_exterior_nao_confunde_espessura_da_parede(self):
        s={"x":275,"y":415,"largura":320,"comprimento":300,"parede":15}
        a={"min":[540,440,1],"max":[634,640,50]}
        r=contencao(a,s)
        self.assertFalse(r["envelope_dentro"])
        self.assertEqual(r["excesso_exterior_cm"]["leste"],24)
        self.assertEqual(r["excesso_interno_cm"]["leste"],39)
        a["max"][0]=590
        self.assertTrue(contencao(a,s)["envelope_dentro"])
