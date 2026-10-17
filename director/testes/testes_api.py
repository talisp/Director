import unittest
from director.api import consultar

class Referencia(unittest.TestCase):
    def test_consulta_traduz_e_nao_inventa_metodo(self):
        d={'meta':{'motor':'teste'},'entradas':[{'simbolo':'Mesh.get_mass','tipo':'metodo','doc':'get_mass() -> float'}]}
        self.assertEqual(consultar(d,'massa')['resultados'][0]['simbolo'],'Mesh.get_mass')
        self.assertEqual(consultar(d,'metodo_inexistente')['total'],0)
