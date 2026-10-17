import unittest,importlib.util
from director.espaco2d import avaliar

@unittest.skipUnless(importlib.util.find_spec('shapely'),'Shapely opcional')
class Espaco2d(unittest.TestCase):
    def objeto(self,oid,x,y,w,d,h=180):return {'id':oid,'x':x,'y':y,'largura':w,'profundidade':d,'altura':h}
    def test_porta_e_janela_respeitam_altura(self):
        q={'dimensoes_cm':[400,400],'objetos':[self.objeto('armario',200,360,100,60)],
          'aberturas':[{'id':'janela','tipo':'janela','parede':'norte','posicao':200,'largura':120,'altura':110,'peitoril':90}]}
        r=avaliar(q);self.assertFalse(r['aprovado']);self.assertEqual(r['violacoes'][0]['invasao_cm'],40)
        q['objetos'][0]['altura']=80;self.assertEqual(avaliar(q)['violacoes'],[])
        q['aberturas'][0].update({'id':'porta','tipo':'porta','altura':210})
        r=avaliar(q);self.assertFalse(r['aprovado']);self.assertEqual(r['violacoes'][0]['invasao_cm'],60)
    def test_cama_identificada_como_bloqueio_e_giro(self):
        q={'dimensoes_cm':[400,400],'objetos':[self.objeto('cama',200,200,340,90)]}
        r=avaliar(q);self.assertFalse(r['aprovado']);self.assertEqual(r['regioes'],2)
        self.assertEqual(r['bloqueadores_individuais'],['cama'])
        q['objetos'][0]['largura']=200;self.assertTrue(avaliar(q)['aprovado'])
        q['objetos'][0].update({'largura':340,'giro':90});self.assertEqual(avaliar(q)['regioes'],2)
    def test_planejador_nao_aprova_candidato_desconectado(self):
        from director.planejamento import resolver
        q={'dimensoes_cm':[400,400],'objetos':[{'id':'novo','dimensoes_cm':[40,40,50]}],
            'obstaculos':[self.objeto('cama',200,200,340,90)],'segundos':1}
        r=resolver(q);self.assertFalse(r['ok']);self.assertNotIn('objetos',r)
        self.assertEqual(r['motivo'],'filtro2d_reprovou')

    def test_quarto_sol_medido_passa_sem_unreal(self):
        import json
        from pathlib import Path
        q=json.loads((Path(__file__).parent/'fixtures/quarto_sol_2d.json').read_text())
        r=avaliar(q)
        self.assertTrue(r['aprovado'],r);self.assertEqual(r['regioes'],1)
        self.assertEqual(r['proporcao_maior_regiao'],1)


@unittest.skipUnless(importlib.util.find_spec('shapely'),'Shapely opcional')
class Acesso(unittest.TestCase):
    def objeto(self,oid,x,y,w,d,h=180):return {'id':oid,'x':x,'y':y,'largura':w,'profundidade':d,'altura':h}
    PORTA=[{'id':'p','tipo':'porta','parede':'oeste','posicao':200,'largura':90,'altura':210}]
    def test_bolsao_sem_alvo_nao_reprova_e_alvo_no_bolsao_reprova(self):
        # Parede interna de armarios de x=250 ate o leste: o canto nordeste vira bolsao.
        objs=[self.objeto('g1',300,300,40,200),self.objeto('g2',350,210,100,40)]
        q={'dimensoes_cm':[400,400],'objetos':objs,'aberturas':self.PORTA,'alvos':[{'id':'g2','caixa':[300,130,400,190]}]}
        r=avaliar(q);self.assertGreater(r['regioes'],1);self.assertTrue(r['aprovado'],r)
        q['alvos'].append({'id':'canto','caixa':[330,330,400,400]})
        r=avaliar(q);self.assertFalse(r['aprovado'])
        self.assertEqual([a['id'] for a in r['acessos'] if not a['alcancado']],['canto'])
    def test_sem_porta_mantem_regra_antiga(self):
        q={'dimensoes_cm':[400,400],'objetos':[self.objeto('cama',200,200,340,90)],'alvos':[{'id':'x','caixa':[0,0,50,50]}]}
        self.assertFalse(avaliar(q)['aprovado'])


@unittest.skipUnless(importlib.util.find_spec('shapely'),'Shapely opcional')
class FolhaDaPorta(unittest.TestCase):
    """17/10 ao vivo: a folha aberta (90 cm para dentro) fechava a passagem entre a porta e a cama."""
    def test_folha_aberta_fecha_passagem_estreita(self):
        from director.espaco2d import folha
        porta={'id':'p','tipo':'porta','parede':'oeste','posicao':100,'largura':90,'altura':210,'angulo':90}
        f=folha(porta,260,350).bounds
        self.assertAlmostEqual(f[0],0);self.assertAlmostEqual(f[2],90);self.assertAlmostEqual((f[1]+f[3])/2,145)
        cama={'id':'cama','x':195,'y':245,'largura':100,'profundidade':200,'altura':80}
        q={'dimensoes_cm':[300,350],'objetos':[cama],'aberturas':[porta],'alvos':[{'id':'canto','caixa':[5,250,90,345]}]}
        self.assertFalse(avaliar(q)['aprovado'])           # folha ate x 90, cama de 145 a 245 e de 245 a 300: 55 cm
        cama['x']=245;self.assertTrue(avaliar(q)['aprovado'])  # folha ate 90, cama a partir de 195: 105 cm passa
    def test_dobradica_de_cada_parede(self):
        from director.espaco2d import folha
        for parede,(x,y) in (('sul',(55,0)),('leste',(260,55)),('norte',(145,350)),('oeste',(0,145))):
            b=folha({'parede':parede,'posicao':100,'largura':90,'angulo':90},260,350).bounds
            self.assertTrue(b[0]-1e-6<=x<=b[2]+1e-6 and b[1]-1e-6<=y<=b[3]+1e-6,(parede,b))
