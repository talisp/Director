import copy,tempfile,unittest
from unittest.mock import patch
from director import revisao as R
from director.nucleo import planta as PL,executor as X,operacoes as O
from director.testes.editor_falso import EditorFalso


def notas(v):return {k:{'nota':v,'justificativa':'avaliacao do caso, nao uma medida'} for k in R.ITENS}


class Revisao(unittest.TestCase):
    def test_nota_nao_apaga_medida_reprovada_e_falta_vira_pergunta(self):
        r=R.pontuar(notas(9),{'aprovado':False},[{'falta':'janela'}])
        self.assertEqual([r[k]['nota'] for k in ('funcao','passagem','seguiu_pedido')],[3,3,3])
        self.assertEqual(r['completude']['nota'],5);self.assertEqual(r['realismo']['nota'],9)
        p=O.aplicar_ficha(PL.nova('x'),{'operacoes':[{'operacao':'criar_sala','id':'quarto','largura_m':3,'comprimento_m':3},
            {'operacao':'colocar','tipo':'porta'}]})[0]
        antes=copy.deepcopy(p);q=R.perguntas(p,{'quarto':'quarto'})
        self.assertEqual([x['falta'] for x in q],['janela']);self.assertEqual(p,antes)
        self.assertEqual(R.perguntas(p,{'quarto':'quarto'},['quarto.janela']),[])
        with self.assertRaises(ValueError):R.pontuar(notas(float('nan')),{},[])

    def test_recuo_identidade_limite_tres_e_interferencia(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(R.C,'CENAS',tmp),patch.object(R.C,'ESTADO_DIR',tmp),patch.object(R.C,'WORK',tmp),patch.object(R.C,'LAB_DIR',''),patch.object(X,'_esperar_nav',return_value=True):
            ed=EditorFalso()
            X.executar('t',{'operacoes':[{'operacao':'criar_sala','id':'s','largura_m':4,'comprimento_m':4},
                {'operacao':'colocar','tipo':'mesa','id':'m','x_m':2,'y_m':2}]},ed,tmp)
            pos=copy.deepcopy(ed.memoria['m']);fora=copy.deepcopy(ed.fora)
            def avaliacao(c,p,e,tipos=None):return {'ok':True,'veredito':'APROVADO','medidas':{'aprovado':True},'notas':p['notas'],'soma':sum(n['nota'] for n in p['notas'].values()),'perguntas':[]}
            with patch.object(R,'avaliar',side_effect=avaliacao),patch.object(R.V,'verificar',return_value={'aprovado':True}):
                R.executar('t',{'acao':'iniciar','pedido':'mesa central','notas':notas(6),'dispensados':['s.janela']},ed)
                for n in range(3):
                    R.executar('t',{'acao':'corrigir','ficha':{'operacoes':[{'operacao':'mudar','id':'m','x_m':2.3}]}},ed)
                    baixas=notas(7);baixas['funcao']['nota']=4 # soma sobe, um item cai 2: deve recuar
                    r=R.executar('t',{'acao':'concluir','notas':baixas},ed)
                    self.assertTrue(r['recuou']);self.assertEqual(ed.memoria['m'],pos);self.assertEqual(ed.fora,fora)
                self.assertEqual(r['estado'],'encerrada');self.assertEqual(r['rodadas'],3)
                self.assertEqual(R.executar('t',{'acao':'estado'},ed)['revisao']['dispensados'],['s.janela'])
                with self.assertRaisesRegex(ValueError,'encerrada'):R.executar('t',{'acao':'corrigir'},ed)
                R.executar('t',{'acao':'iniciar','pedido':'outra revisao','notas':notas(6)},ed)
                ed.memoria['m']['loc'][0]+=1
                with self.assertRaisesRegex(ValueError,'divergem'):R.executar('t',{'acao':'corrigir','ficha':{}},ed)
