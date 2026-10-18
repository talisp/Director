import unittest
from director.catalogo import consultar


class Catalogo(unittest.TestCase):
    def test_projeto_antes_de_offline_e_criado_camel_case(self):
        from director.catalogo import _aliases
        self.assertIn('criado_mudo',_aliases('cabinetBed')[0])
        d={'itens':[{'nome':'chair chair cadeira','origem':'offline'}, {'nome':'chair','origem':'projeto'}]}
        self.assertEqual(consultar(d,{'texto':'cadeira'})['resultados'][0]['origem'],'projeto')
    def test_portugues_encontra_chair_e_prioriza_cena(self):
        base={'level':'teste','itens':[{'nome':'chairDesk','origem':'projeto','categoria':['cadeira'],'sinonimos':['chair','cadeira']},
             {'nome':'Cadeira_mesa1','origem':'cena','categoria':['cadeira'],'sinonimos':['chair'],'dimensoes_cm':[50,50,90]}]}
        r=consultar(base,{'texto':'chair'})
        self.assertEqual(r['resultados'][0]['nome'],'Cadeira_mesa1')
        self.assertEqual(len(consultar(base,{'texto':'cadeira','maximo_cm':[40,40,100]})['resultados']),0)
        self.assertEqual(consultar(base,{'texto':'geladeira'})['total'],0)
