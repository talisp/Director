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

class Circulacao(unittest.TestCase):
    def test_varre_caminho_com_curva_e_detecta_segmento_bloqueado(self):
        from unittest.mock import patch,Mock
        from director import verificacao as V
        sala={'tipo':'sala','x':0,'y':0,'z':1,'largura':200,'comprimento':200,'altura':270,'parede':15}
        planta={'nivel':'level','objetos':{'sala':sala}}
        ed=Mock();ed.chamar.side_effect=lambda n,**kw: {'level':'level'} if n=='info' else {'atores':[]}
        direto={'medidas':[{'livre':False},{'completo':True,'pontos':[[0,0,1],[100,0,1],[100,100,1]]}]}
        pedido={'rotas':[{'de':[0,0,1],'ate':[100,100,1]}]}
        for bloqueado in (False,True):
            with patch.object(V.PL,'carregar',return_value=planta),patch.object(V.relatorio,'medir',return_value={}),patch.object(V.consultas,'medir',side_effect=[direto,{'medidas':[{'livre':True},{'livre':not bloqueado}]}]):
                r=V.verificar('teste',pedido,ed)
            rota=r['circulacao'][0]
            self.assertFalse(rota['linha_direta']['livre'])
            self.assertEqual(rota['passagem']['livre'],not bloqueado)
