import unittest,copy
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

    def test_compartilhamento_distingue_lado_da_sala_e_do_vizinho(self):
        p,_=O.aplicar_ficha(self.exemplo(),{'operacoes':[
            {'operacao':'criar_sala','id':'vizinha','largura_m':2,'comprimento_m':3,'x_m':4.15}]})
        r=T.renderizar(p,'s')
        a=r['relacoes_compartilhadas'][0]
        self.assertEqual((a['sala'],a['lado'],a['vizinho'],a['lado_vizinho']),('s','leste','vizinha','oeste'))
        self.assertEqual(r['salas']['s']['eixos_interno_cm'][0],'largura_leste_oeste')

    def test_leitura_real_mostra_mesa_movida_sem_adotar_na_planta(self):
        from director.nucleo import derivar as D
        p=self.exemplo();original=copy.deepcopy(p);inv={'controlados':D.derivar(p),'fora':[]}
        inv['controlados']['mesa']['loc'][0]=430
        class Editor:
            def chamar(self,nome,**kw):
                if nome=='info':return {'level':p['nivel'],'em_play':False}
                if nome=='inventory':return inv
                raise AssertionError('leitura nao pode executar '+nome)
        r=T.observar_no_editor(p,Editor(),'s')
        item=next(x for x in r['legenda'] if x['id']=='mesa')
        self.assertEqual(item['centro_cm'][0],430)
        self.assertGreater(item['excesso_interno_planejado_cm']['leste'],0)
        self.assertEqual(p,original);self.assertTrue(r['somente_leitura'])
        self.assertEqual(r['fonte'],'inventario_editor_com_estrutura_planejada')

    def test_leitura_real_nao_abre_outro_level(self):
        class Editor:
            def chamar(self,nome,**kw):
                self_nome=nome
                if self_nome=='info':return {'level':'outro','em_play':False}
                raise AssertionError('nao consultar outro level')
        with self.assertRaisesRegex(ValueError,'nao troca'):T.observar_no_editor(self.exemplo(),Editor())

    def test_movel_ausente_nao_e_desenhado_como_observado(self):
        from director.nucleo import derivar as D
        p=self.exemplo();inv={'controlados':D.derivar(p),'fora':[]};del inv['controlados']['mesa']
        class Editor:
            def chamar(self,nome,**kw):return {'level':p['nivel'],'em_play':False} if nome=='info' else inv
        r=T.observar_no_editor(p,Editor(),'s')
        self.assertNotIn('mesa',r['centros_grade']);self.assertIn('mesa',r['conciliacao']['faltando'])
