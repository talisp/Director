import unittest
from director.catalogo import consultar


class Catalogo(unittest.TestCase):
    def test_nome_composto_nao_vira_cama_nem_roupeiro(self):
        from director.catalogo import _aliases
        self.assertEqual(_aliases('cabinetBed')[0],['criado_mudo'])
        self.assertEqual(_aliases('bookcaseClosedDoors')[0],['estante'])
        self.assertEqual(_aliases('bedsideTable')[0],['criado_mudo'])
        self.assertEqual(_aliases('chairDesk')[0],['cadeira'])
        self.assertEqual(_aliases('Ornate Royal Armchair')[0],['cadeira'])
        self.assertIn('cama',_aliases('bedSingle')[0])

    def test_busca_dimensoes_minimas_recusa_miniatura(self):
        base={'itens':[{'nome':'bedSingle','origem':'offline','dimensoes_cm':[57,112,37]}]}
        self.assertEqual(consultar(base,{'texto':'bed','minimo_cm':[80,180,30]})['total'],0)

    def test_expansao_nao_faz_criado_mudo_parecer_roupeiro_ou_cama(self):
        from director.catalogo import _aliases
        itens=[]
        for n in ('cabinetBed','bedSingle','desk','chairDesk'):
            cats,alias=_aliases(n)
            itens.append({'nome':n,'origem':'offline','categoria':cats,'sinonimos':alias})
        base={'itens':itens}
        self.assertEqual([x['nome'] for x in consultar(base,{'texto':'single bed'})['resultados']],['bedSingle'])
        self.assertEqual([x['nome'] for x in consultar(base,{'texto':'cadeira'})['resultados']],['chairDesk'])
        self.assertEqual(consultar(base,{'texto':'armario estreito'})['total'],0)
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
