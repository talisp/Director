import unittest
from unittest.mock import Mock
from director import relatorio


class Relatorio(unittest.TestCase):
    def test_medida_diferente_do_pedido_nao_copia_planta(self):
        planta = {"objetos": {"s": {"tipo": "sala", "x": 0, "y": 0, "z": 1, "largura": 320, "comprimento": 300, "altura": 270, "parede": 15}}}
        ed = Mock()
        ed.chamar.return_value = {"medidas": [{"acertou": True, "tipo": "parede", "distancia": d} for d in [160, 145, 150, 150]]}
        r = relatorio.medir(planta, ed)
        self.assertEqual(r["medido"]["s"]["largura"], 305)
        self.assertFalse(r["medido"]["s"]["confere_com_planta"])
        ed.chamar.return_value["medidas"][0]["tipo"] = "mesa"
        r = relatorio.medir(planta, ed)
        self.assertEqual(r["medido"], {})
        self.assertTrue(any(isinstance(x, dict) for x in r["nao_verificado"]))
