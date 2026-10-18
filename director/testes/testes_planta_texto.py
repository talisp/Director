import unittest
from director import planta_texto as T
from director.nucleo import operacoes as O,planta as PL


class Texto(unittest.TestCase):
    def exemplo(self):
        return O.aplicar_ficha(PL.nova('teste'),{'operacoes':[
            {'operacao':'criar_sala','id':'s','largura_m':4,'comprimento_m':3},
            {'operacao':'colocar','tipo':'porta','id':'p','parede':'oeste','posicao_m':1,'angulo':90},
            {'operacao':'colocar','tipo':'janela','id':'j','parede':'norte'},
            {'operacao':'colocar','tipo':'mesa','id':'mesa','x_m':2,'y_m':1.5}]})[0]

    def test_centro_e_escala_norte_para_cima_sem_unreal(self):
        p=self.exemplo();r=T.renderizar(p,escala_cm=10)
        row,col=r['centros_grade']['mesa'];grid=r['texto'].splitlines()
        self.assertEqual(grid[row][col],'A')
        x=r['origem_grade_cm'][0]+col*10;y=r['origem_grade_cm'][1]-row*10
        self.assertLessEqual(abs(x-200),10);self.assertLessEqual(abs(y-150),10)
        self.assertEqual(r['fonte'],'planta_desejada')
        self.assertIn('=',r['texto']);self.assertIn('o',r['texto'])
        self.assertEqual(p,self.exemplo())

    def test_movel_fora_da_parede_nao_e_recortado(self):
        p=self.exemplo();p['objetos']['mesa']['x']=430
        r=T.renderizar(p,escala_cm=10)
        row,col=r['centros_grade']['mesa']
        self.assertEqual(r['texto'].splitlines()[row][col],'A')
        self.assertGreater(r['origem_grade_cm'][0]+col*10,400)
        item=next(x for x in r['legenda'] if x['id']=='mesa')
        self.assertEqual(item['excesso_interno_planejado_cm']['leste'],90)

    def test_limite_e_id_inexistente_sao_explicitos(self):
        with self.assertRaises(ValueError):T.renderizar(self.exemplo(),'ausente')
        with self.assertRaises(ValueError):T.renderizar(self.exemplo(),escala_cm=.1)
