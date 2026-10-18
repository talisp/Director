import copy
import importlib.util
import unittest
from director.nucleo import planta as PL,operacoes as OP,derivar as D


@unittest.skipUnless(importlib.util.find_spec('ortools'),'OR-Tools opcional')
class Salas(unittest.TestCase):
    def resolver(self,p,q):
        from director.planejamento_salas import resolver
        return resolver(p,q)

    def pedido(self,largura=4):
        return {'salas':[{'id':'sala','largura_m':largura,'comprimento_m':3},
          {'id':'corredor','largura_m':1.5,'comprimento_m':3},
          {'id':'quarto','largura_m':3,'comprimento_m':3},
          {'id':'banheiro','largura_m':2,'comprimento_m':3}],
          'adjacencias':[['sala','corredor'],['corredor','quarto'],['corredor','banheiro']],'segundos':3}

    def test_quatro_comodos_geram_ficha_valida_com_variacao(self):
        for largura in (4,4.5):
            p=PL.nova('teste');antes=copy.deepcopy(p);r=self.resolver(p,self.pedido(largura))
            self.assertTrue(r['ok'],r)
            novo,_=OP.aplicar_ficha(p,r['ficha_salas'])
            conexoes={frozenset(a['salas']) for a in r['paredes_compartilhadas_planejadas']}
            for par in self.pedido()['adjacencias']:self.assertIn(frozenset(par),conexoes)
            self.assertEqual(p,antes);self.assertFalse(r['aplicado'])
            self.assertEqual(len([o for o in novo['objetos'].values() if o['tipo']=='sala']),4)

    def test_adjacencia_impossivel_identifica_par_em_conflito(self):
        r=self.resolver(PL.nova('teste'),{'salas':[{'id':'a','largura_m':3,'comprimento_m':3,'x_m':0,'y_m':0},
            {'id':'b','largura_m':3,'comprimento_m':3,'x_m':10,'y_m':0}], 'adjacencias':[['a','b']]})
        self.assertFalse(r['ok']);self.assertEqual(r['motivo'],'restricoes_incompativeis')
        self.assertIn(['a','b'],r['adjacencias_em_conflito'])

    def test_aumentar_local_preserva_outros_cantos_e_movel(self):
        p,_=OP.aplicar_ficha(PL.nova('teste'),{'operacoes':[
            {'operacao':'criar_sala','id':'cozinha','largura_m':3,'comprimento_m':3},
            {'operacao':'criar_sala','id':'quarto','largura_m':3,'comprimento_m':3,'x_m':10},
            {'operacao':'colocar','tipo':'mesa','sala':'cozinha','id':'mesa','x_m':1.5,'y_m':1.5}]})
        r=self.resolver(p,{'salas':[{'id':'cozinha','largura_m':4,'comprimento_m':3}]})
        self.assertTrue(r['ok'],r);novo,_=OP.aplicar_ficha(p,r['ficha_salas'])
        self.assertEqual(novo['objetos']['quarto'],p['objetos']['quarto'])
        self.assertEqual(novo['objetos']['mesa'],p['objetos']['mesa'])


class Passagens(unittest.TestCase):
    def test_plano_antigo_recusa_sem_aplicar_nem_mudar_planta(self):
        import tempfile
        from director.nucleo import executor as X
        from director.testes.editor_falso import EditorFalso
        with tempfile.TemporaryDirectory() as tmp:
            ed=EditorFalso()
            r=X.executar('teste',{'operacoes':[{'operacao':'criar_sala','id':'a','largura_m':3,'comprimento_m':3}]},ed,tmp,pausa=lambda s:None)
            self.assertTrue(r['ok']);antes=copy.deepcopy(ed.memoria);ed.chamadas.clear()
            r=X.executar('teste',{'revisao_base':0,'operacoes':[{'operacao':'mudar_sala','id':'a','largura_m':4}]},ed,tmp,pausa=lambda s:None)
            self.assertEqual(r['motivo'],'planta_revisao_alterada')
            self.assertNotIn('apply',ed.chamadas);self.assertEqual(ed.memoria,antes)
            self.assertEqual(PL.carregar(tmp,'teste')['revisao'],1)

    def planta(self,largura=1):
        return OP.aplicar_ficha(PL.nova('teste'),{'operacoes':[
            {'operacao':'criar_sala','id':'a','largura_m':3,'comprimento_m':3},
            {'operacao':'criar_sala','id':'b','largura_m':3,'comprimento_m':3,'x_m':3.15},
            {'operacao':'colocar','tipo':'passagem','id':'integracao','sala':'a','parede':'leste','largura_m':largura}]})[0]

    def test_so_corta_parede_compartilhada_sem_folha_ou_ator_inventado(self):
        p=self.planta();pecas=D.derivar(p)
        self.assertNotIn('integracao',pecas)
        cortes=[o for o in pecas.values() if o['tipo']=='parede' and o['params']['VaoLargura']]
        self.assertEqual(len(cortes),1);self.assertEqual(cortes[0]['params']['VaoLargura'],100)
        self.assertEqual(cortes[0]['params']['VaoBase'],0)

    def test_passagem_menor_que_capsula_recusa(self):
        with self.assertRaisesRegex(OP.Invalida,'capsula'):self.planta(.65)
