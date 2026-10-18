import copy
import math
import unittest
from director.nucleo import planta as PL,operacoes as O,derivar as D,portas,plano as PN


def cena(parede='oeste',**opcoes):
    return O.aplicar_ficha(PL.nova('teste'),{'operacoes':[
        {'operacao':'criar_sala','id':'s','largura_m':4,'comprimento_m':4},
        {'operacao':'colocar','tipo':'porta','id':'p','parede':parede,'posicao_m':1,'largura_m':.9,'angulo':90,**opcoes}]})[0]


class Portas(unittest.TestCase):
    def test_quatro_paredes_duas_dobradicas_dois_sentidos(self):
        for lado in O.LADOS:
            nx,ny={'sul':(0,1),'norte':(0,-1),'oeste':(1,0),'leste':(-1,0)}[lado]
            for h in ('inicio','fim'):
                for sentido in ('dentro','fora'):
                    p=cena(lado,dobradica=h,sentido=sentido)
                    folha=D.derivar(p)['p'];a=math.radians(folha['rot'][1]+folha['params']['Angulo'])
                    dentro=nx*math.cos(a)+ny*math.sin(a)
                    self.assertAlmostEqual(dentro,1 if sentido=='dentro' else -1,places=6)
                    self.assertEqual(abs(folha['params']['Angulo']),90)

    def test_omitido_preserva_dobradiça_e_rotacao_anteriores(self):
        for lado in O.LADOS:
            p=cena(lado);legado=D.derivar(p)['p']
            h='fim' if lado in ('norte','oeste') else 'inicio'
            novo=D.derivar(cena(lado,dobradica=h,sentido='dentro'))['p']
            self.assertEqual(legado,novo)

    def test_recusa_folha_batendo_no_movel_e_ficha_permanece_intacta(self):
        p=cena();antes=copy.deepcopy(p)
        with self.assertRaisesRegex(O.Invalida,'p: folha.*mesa'):
            O.aplicar_ficha(p,{'operacoes':[{'operacao':'colocar','tipo':'mesa','id':'mesa','x_m':.5,'y_m':1.45,'largura_m':.6,'profundidade_m':.5}]})
        self.assertEqual(p,antes)
        # A outra ponta do vao fica em y55; libera o mesmo movel em y145.
        p,_=O.aplicar_ficha(p,{'operacoes':[{'operacao':'mudar','id':'p','dobradica':'inicio'},
            {'operacao':'colocar','tipo':'mesa','id':'mesa','x_m':.5,'y_m':1.45,'largura_m':.6,'profundidade_m':.5}]})
        self.assertEqual(p['objetos']['p']['dobradica'],'inicio')

    def test_conciliacao_converte_angulo_nativo_com_sinal(self):
        p=cena(dobradica='inicio');real=copy.deepcopy(D.derivar(p))
        real['p']['params']['Angulo']=-45
        novo,rel=PN.conciliar(p,real)
        self.assertEqual(novo['objetos']['p']['angulo'],45)
        self.assertEqual(D.derivar(novo)['p']['params']['Angulo'],-45)

    def test_valor_invalido_recusado_antes_do_editor(self):
        for campo,valor in (('dobradica','esquerda'),('sentido','lateral')):
            with self.assertRaises(O.Invalida):cena(**{campo:valor})
