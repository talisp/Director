import unittest
from director.api import consultar

class Referencia(unittest.TestCase):
    def test_consulta_traduz_e_nao_inventa_metodo(self):
        d={'meta':{'motor':'teste'},'entradas':[{'simbolo':'Mesh.get_mass','tipo':'metodo','doc':'get_mass() -> float'}]}
        self.assertEqual(consultar(d,'massa')['resultados'][0]['simbolo'],'Mesh.get_mass')
        self.assertEqual(consultar(d,'metodo_inexistente')['total'],0)

    def test_atores_do_level_e_colisao_com_acento(self):
        d={'meta':{},'entradas':[
            {'simbolo':'EditorActorSubsystem.get_all_level_actors','tipo':'metodo','doc':'actors in the level'},
            {'simbolo':'CollisionEnabled.QUERY_AND_PHYSICS','tipo':'valor','doc':'collision physics'}]}
        self.assertEqual(consultar(d,'atores do level')['resultados'][0]['simbolo'],'EditorActorSubsystem.get_all_level_actors')
        self.assertEqual(consultar(d,'colisão')['resultados'][0]['simbolo'],'CollisionEnabled.QUERY_AND_PHYSICS')

    def test_trecho_longo_preserva_ocorrencia_e_marca_corte(self):
        d={'meta':{},'entradas':[{'simbolo':'Actor','tipo':'classe','doc':'x '*2000+'physics damping valor relevante'}]}
        r=consultar(d,'amortecimento')['resultados'][0]
        self.assertIn('damping',r['doc']);self.assertTrue(r['texto_truncado'])
        self.assertLessEqual(len(r['doc']),1200)
