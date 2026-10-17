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
