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
