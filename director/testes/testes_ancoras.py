import copy,json,unittest
from director.nucleo import planta as PL,operacoes as O,derivar as D,plano as PN
from director.testes.testes_objetos import _asset,_reg


class Ancoras(unittest.TestCase):
    def planta(self):
        return O.aplicar_ficha(PL.nova('a'),{'operacoes':[
            {'operacao':'criar_sala','id':'sala1','largura_m':4,'comprimento_m':4,'teto':True},
            {'operacao':'colocar','tipo':'janela','id':'jan','parede':'norte','posicao_m':2}]})[0]

    def test_teto_opcional_sem_mudar_pecas_existentes(self):
        p=self.planta();alvo=D.derivar(p);self.assertEqual(alvo['sala1.teto']['rot'],[0,180,180])
        q=O.aplicar_ficha(p,{'operacoes':[{'operacao':'mudar_sala','id':'sala1','teto':False}]})[0]
        a=D.derivar(q);self.assertEqual({k:v for k,v in alvo.items() if k!='sala1.teto'},a)
        with self.assertRaises(O.Invalida):O.aplicar_ficha(p,{'operacoes':[{'operacao':'mudar_sala','teto':1}]})

    def test_quadro_sobre_janela_recusa_mas_parede_solida_aceita(self):
        p=self.planta();quadro=_asset(200,398,121,60,3,60,False,ancora={'tipo':'parede','lado':'norte'})
        quadro['giro']=180
        with self.assertRaisesRegex(O.Invalida,'invade vao jan'):O.aplicar_ficha(p,_reg('quadro',quadro))
        quadro['x']=65
        q=O.aplicar_ficha(p,_reg('quadro',quadro))[0]
        # Mover a janela para baixo do quadro tambem precisa recusar, mesmo por outra ferramenta.
        with self.assertRaisesRegex(O.Invalida,'invade vao jan'):
            O.aplicar_ficha(q,{'operacoes':[{'operacao':'mudar','id':'jan','posicao_m':.65,'largura_m':.6}]})

    def test_luminaria_depende_de_teto_real_e_altura_preservada(self):
        p=self.planta();lamp=_asset(200,200,250.5,30,30,20,False,ancora={'tipo':'teto'})
        q=O.aplicar_ficha(p,_reg('lamp',lamp))[0]
        with self.assertRaisesRegex(O.Invalida,'nao existe teto'):
            O.aplicar_ficha(q,{'operacoes':[{'operacao':'mudar_sala','teto':False}]})
        with self.assertRaisesRegex(O.Invalida,'altura do teto'):
            O.aplicar_ficha(q,{'operacoes':[{'operacao':'mudar_sala','altura_m':3}]})

    def test_tapete_sem_colisao_pode_sobrepor_pegada_sem_simular(self):
        p=self.planta();p=O.aplicar_ficha(p,{'operacoes':[{'operacao':'colocar','tipo':'mesa','id':'mesa','x_m':2,'y_m':2}]})[0]
        r=_asset(200,200,1.2,200,200,.2,False);r['fisica']['colisao']=False
        q=O.aplicar_ficha(p,_reg('tapete',r))[0]
        self.assertFalse(D.derivar(q)['tapete']['objeto']['colisao'])
        r['fisica']['simular']=True
        with self.assertRaisesRegex(O.Invalida,'nao pode simular'):O.aplicar_ficha(p,_reg('tapete',r))

    def test_empilhamento_preserva_descendentes_ao_mover_e_recusa_ciclo(self):
        p=self.planta();p=O.aplicar_ficha(p,_reg('mesa',_asset(200,200,1,120,100,75,False)))[0]
        p=O.aplicar_ficha(p,_reg('livro',_asset(200,200,76,30,25,4,sobre='mesa')))[0]
        p=O.aplicar_ficha(p,_reg('pequeno',_asset(200,200,80,10,10,5,sobre='livro')))[0]
        q=O.aplicar_ficha(p,{'operacoes':[{'operacao':'mudar','id':'mesa','x_m':2.4}]})[0]
        self.assertEqual(q['objetos']['pequeno']['x'],240)
        original=copy.deepcopy(p);p['objetos']['mesa']['sobre']='pequeno'
        with self.assertRaisesRegex(O.Invalida,'ciclo'):O.conferir(p)
        self.assertEqual(original['objetos']['pequeno']['x'],200)

    def test_mudanca_de_colisao_nao_passa_como_conciliada(self):
        p=self.planta();o=_asset(100,100,1,50,50,1,False);o['fisica']['colisao']=False
        q=O.aplicar_ficha(p,_reg('t',o))[0];alvo=D.derivar(q);real=copy.deepcopy(alvo)
        real['t']['objeto']['colisao']=True
        self.assertEqual(PN.diferencas(alvo,real)[0]['o_que'],'objeto')

    def test_altura_do_apoio_interno_escala_com_geometria_e_nao_com_topo(self):
        p=self.planta();p=O.aplicar_ficha(p,_reg('estante',_asset(200,200,1,100,60,180,False)))[0]
        p=O.aplicar_ficha(p,_reg('livro',_asset(200,200,81,20,15,4,sobre='estante')))[0]
        q=O.aplicar_ficha(p,{'operacoes':[{'operacao':'mudar','id':'estante','altura_m':1.98}]})[0]
        self.assertAlmostEqual(q['objetos']['livro']['z'],89)
