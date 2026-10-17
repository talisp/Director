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


class PecaFixa(unittest.TestCase):
    """Box do banheiro (simular false na planta) nao precisa de fisica; a cadeira precisa."""
    def _verificar(self,fisica_cadeira):
        from unittest.mock import patch,Mock
        from director import verificacao as V
        sala={'tipo':'sala','x':0,'y':0,'z':1,'largura':300,'comprimento':300,'altura':270,'parede':15}
        f=lambda sim:{'simular':sim,'massa_kg':8,'amortecimento_linear':.5,'amortecimento_angular':1,'subir':False}
        planta={'nivel':'level','objetos':{'sala':sala,'box':{'tipo':'asset','sala':'sala','fisica':f(False)},
                                             'cadeira':{'tipo':'asset','sala':'sala','fisica':f(True)}}}
        comp=lambda fis:[{'fisica':fis,'movel':True,'sobreposicoes_nativas':[]}]
        geo=[{'id':'box','rotulo':'box','caminho':'L.box','tipo':'asset','min':[10,10,1],'max':[100,100,200],'componentes_fisicos':comp(False)},
             {'id':'cadeira','rotulo':'cadeira','caminho':'L.cad','tipo':'asset','min':[150,150,1],'max':[200,200,80],'componentes_fisicos':comp(fisica_cadeira)}]
        def chamar(n,**kw):
            if n=='info':return {'level':'level'}
            if n=='scene_geometry':return {'atores':geo}
            return {'medidas':[{'acertou':True,'distancia':1}]}
        ed=Mock();ed.chamar.side_effect=chamar
        estavel=lambda a,fis:{'ator':a,'estavel':True,'fisica':fis}
        play={'rotas':[],'fisica':[estavel('box',False),estavel('cadeira',fisica_cadeira)]}
        with patch.object(V.PL,'carregar',return_value=planta),patch.object(V.relatorio,'medir',return_value={}),patch.object(V,'testar_play',return_value=play):
            return V.verificar('teste',{'simular':True},ed)

    def test_box_fixo_parado_aprova(self):
        r=self._verificar(True);self.assertTrue(r['aprovado'],r['play'])
        self.assertEqual([f['exige_fisica'] for f in r['play']['fisica']],[False,True])

    def test_cadeira_sem_fisica_reprova(self):
        from director.veredito import com_veredito
        r=self._verificar(False);self.assertFalse(r['aprovado'])
        v=com_veredito('verificar',r);self.assertIn('cadeira: sem fisica',v['motivo']);self.assertNotIn('box',v['motivo'])
