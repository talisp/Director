import json
import tempfile
import unittest
from director.nucleo import executor as X,planta as PL
from director.testes.editor_falso import EditorFalso
from director.testes.testes_nucleo import ficha


class Objetos(unittest.TestCase):
    def test_objeto_enraizado_na_planta_muda_e_remove_sem_recriar(self):
        with tempfile.TemporaryDirectory() as tmp:
            ed=EditorFalso();X.executar('teste',ficha(1),ed,tmp,pausa=lambda _:None)
            modelo={'tipo':'asset','sala':'sala1','x':80,'y':80,'z':1,'giro':0,'largura':40,'profundidade':40,'altura':80,
                'modelo':{'asset':'/Game/Cadeira','tamanho':[100,100,100],'centro':[0,0,0],'min_z':-50},
                'fisica':{'simular':True,'massa_kg':8,'amortecimento_linear':.5,'amortecimento_angular':1,'subir':False}}
            r=X.executar('teste',{'operacoes':[{'operacao':'registrar_objeto','id':'cadeira','modelo_json':json.dumps(modelo)}]},ed,tmp,pausa=lambda _:None)
            self.assertTrue(r['ok'],r)
            caminho=ed.memoria['cadeira']['caminho']
            r=X.executar('teste',{'operacoes':[{'operacao':'mudar','id':'cadeira','x_m':1}]},ed,tmp,pausa=lambda _:None)
            self.assertTrue(r['ok'],r);self.assertEqual(ed.memoria['cadeira']['caminho'],caminho)
            self.assertEqual(PL.carregar(tmp,'teste')['objetos']['cadeira']['x'],100)
            bad=X.executar('teste',{'operacoes':[{'operacao':'mudar','id':'cadeira','x_m':-.5}]},ed,tmp,pausa=lambda _:None)
            self.assertFalse(bad['ok']);self.assertEqual(PL.carregar(tmp,'teste')['objetos']['cadeira']['x'],100)
            r=X.executar('teste',{'operacoes':[{'operacao':'remover','id':'cadeira'}]},ed,tmp,pausa=lambda _:None)
            self.assertTrue(r['ok']);self.assertNotIn('cadeira',ed.memoria)


def _asset(x,y,z,larg,prof,alt,simular=True,**extra):
    return {'tipo':'asset','sala':'sala1','x':x,'y':y,'z':z,'giro':0,'largura':larg,'profundidade':prof,'altura':alt,
        'modelo':{'asset':'/Game/X','tamanho':[100,100,100],'centro':[0,0,0],'min_z':-50},
        'fisica':{'simular':simular,'massa_kg':1,'amortecimento_linear':.5,'amortecimento_angular':1,'subir':False},**extra}


def _reg(oid,modelo):
    return {'operacoes':[{'operacao':'registrar_objeto','id':oid,'modelo_json':json.dumps(modelo)}]}


class Apoiados(unittest.TestCase):
    """Travesseiro sobre a cama: no teste de 17/10 a planta recusava e o Hermes escreveu scripts soltos."""
    def test_sobre_a_cama_vai_junto_e_nao_sai_do_tampo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ed=EditorFalso();ok=lambda f:X.executar('teste',f,ed,tmp,pausa=lambda _:None)
            ok(ficha(1))
            self.assertTrue(ok(_reg('cama',_asset(330,120,1,100,200,50)))['ok'])
            self.assertFalse(ok(_reg('mala',_asset(330,120,1,40,40,40)))['ok'])  # no chao, no lugar da cama: recusa
            r=ok(_reg('travesseiro',_asset(330,190,51,60,40,14,sobre='cama')))
            self.assertTrue(r['ok'],r)
            fora=ok(_reg('livro',_asset(330,225,51,30,30,4,sobre='cama')))
            self.assertFalse(fora['ok']);self.assertIn('fora de cama',json.dumps(fora,ensure_ascii=False))
            # mover a cama leva o travesseiro (x, altura e giro)
            r=ok({'operacoes':[{'operacao':'mudar','id':'cama','x_m':3.2,'altura_m':.6}]});self.assertTrue(r['ok'],r)
            t=PL.carregar(tmp,'teste')['objetos']['travesseiro']
            self.assertEqual((t['x'],t['z']),(320,61))
            # nao remove a cama com o travesseiro em cima
            self.assertFalse(ok({'operacoes':[{'operacao':'remover','id':'cama'}]})['ok'])

    def test_dois_no_mesmo_tampo_nao_se_sobrepoem(self):
        with tempfile.TemporaryDirectory() as tmp:
            ed=EditorFalso();ok=lambda f:X.executar('teste',f,ed,tmp,pausa=lambda _:None)
            ok(ficha(1));ok(_reg('mesa_a',_asset(330,330,1,120,60,75)))
            self.assertTrue(ok(_reg('note',_asset(300,330,76,33,23,2,sobre='mesa_a')))['ok'])
            self.assertFalse(ok(_reg('livro',_asset(320,330,76,30,20,4,sobre='mesa_a')))['ok'])


class Fixos(unittest.TestCase):
    def _fazer(self,pedido):
        from director import config as C, objetos
        class Ed(EditorFalso):
            def _object_model(self,asset='',ator='',partes=None):
                return {'modelo':{'asset':'/Game/Box','tamanho':[120,100,200],'centro':[0,0,100],'min_z':0}}
        with tempfile.TemporaryDirectory() as tmp:
            ed=Ed();X.executar('teste',ficha(1),ed,tmp,pausa=lambda _:None)
            velho=C.CENAS;C.CENAS=tmp
            try:return objetos.fazer('teste',{'sala':'sala1','id':'box1','acao':'colocar','asset':'/Game/Box','x_m':.8,'y_m':.8,**pedido},ed),PL.carregar(tmp,'teste')
            finally:C.CENAS=velho

    def test_box_e_fixo_e_cadeira_simula(self):
        r,p=self._fazer({'categoria':'box_chuveiro'})
        self.assertTrue(r['ok'],r);self.assertFalse(p['objetos']['box1']['fisica']['simular']);self.assertTrue(r['fisica']['fixo'])
        r,p=self._fazer({'categoria':'cadeira'})
        self.assertTrue(p['objetos']['box1']['fisica']['simular'])
        with self.assertRaises(ValueError):self._fazer({'categoria':'pia','simular':True})


class AlturaDeApoio(unittest.TestCase):
    """Cabeceira mais alta que o colchao: o topo da caixa (83) nao e onde o travesseiro apoia (53)."""
    def _altura(self,alturas,ids=None):
        from director.objetos import _altura_de_apoio
        class Ed:
            def chamar(s,nome,consultas):
                return {'medidas':[{'acertou':True,'id':(ids or ['cama']*5)[i],'rotulo':(ids or ['cama']*5)[i],'ponto':[0,0,z]} for i,z in enumerate(alturas)]}
        cama={'z':1,'altura':82}
        return _altura_de_apoio(Ed(),cama,'cama',{'x':480,'y':560,'giro':0,'largura':62,'profundidade':42})
    def test_colchao_plano(self):
        self.assertEqual(self._altura([53,53,53.5,53,52.8]),53.5)
    def test_canto_na_cabeceira_recusa(self):
        with self.assertRaises(ValueError) as e:self._altura([53,53,83,53,83])
        self.assertIn('irregular (53.0 a 83.0 cm)',str(e.exception))
    def test_canto_fora_da_cama_recusa(self):
        with self.assertRaises(ValueError) as e:self._altura([53,53,53,53,0],ids=['cama']*4+['quarto.piso'])
        self.assertIn('canto nordeste',str(e.exception))


class Rearrumar(unittest.TestCase):
    def test_trocar_dois_moveis_de_lugar_numa_ficha(self):
        with tempfile.TemporaryDirectory() as tmp:
            ed=EditorFalso();ok=lambda f:X.executar('teste',f,ed,tmp,pausa=lambda _:None)
            ok(ficha(1));ok(_reg('a',_asset(330,80,1,60,60,50)));ok(_reg('b',_asset(330,320,1,60,60,50)))
            troca={'operacoes':[{'operacao':'mudar','id':'a','y_m':3.2},{'operacao':'mudar','id':'b','y_m':.8}]}
            r=ok(troca);self.assertTrue(r['ok'],r)
            o=PL.carregar(tmp,'teste')['objetos'];self.assertEqual((o['a']['y'],o['b']['y']),(320,80))
            # no fim, um em cima do outro continua recusado
            self.assertFalse(ok({'operacoes':[{'operacao':'mudar','id':'a','y_m':.8}]})['ok'])
