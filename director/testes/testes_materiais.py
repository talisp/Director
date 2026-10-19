import unittest,copy
from director import materiais as M
from director.nucleo import planta as PL,operacoes as O,derivar as D,plano as PN


class Materiais(unittest.TestCase):
    def planta(self):return O.aplicar_ficha(PL.nova('t'),{'operacoes':[{'operacao':'criar_sala','id':'a','largura_m':3,'comprimento_m':3,'teto':True}]})[0]
    def aplicar(self,p,sid,alvo,path):return O.aplicar_ficha(p,{'operacoes':[{'operacao':'material_sala','id':sid,'alvo':alvo,'caminho':path,'descricao':'material do ensaio'}]})[0]

    def test_apenas_material_difere_e_dimensao_reaplica_override(self):
        p=self.planta();q=self.aplicar(p,'a','piso','/Game/M_Wood');a=D.derivar(q);antes=D.derivar(p)
        self.assertEqual(antes['a.piso'],{k:v for k,v in a['a.piso'].items() if k!='material'})
        ac=PN.planejar(a,antes);self.assertEqual(len(ac),1);self.assertEqual(ac[0]['material'],'/Game/M_Wood')
        atual=copy.deepcopy(a);atual['a.piso']['params']['Largura']-=10
        ac=PN.planejar(a,atual);self.assertEqual(ac[0]['material'],'/Game/M_Wood')
        atual['a.piso']['material']='/Game/Outro';self.assertIn('material',[d['o_que'] for d in PN.diferencas(a,atual)])
        ac=PN.planejar(antes,a);self.assertIsNone(ac[0]['material'])

    def test_conflito_compartilhado_nao_escolhe_um_lado_silenciosamente(self):
        p=O.aplicar_ficha(self.planta(),{'operacoes':[{'operacao':'criar_sala','id':'b','largura_m':3,'comprimento_m':3,'x_m':3.15}]})[0]
        p=self.aplicar(p,'a','parede_leste','/Game/M_Wood')
        with self.assertRaisesRegex(O.Invalida,'conflitantes'):self.aplicar(p,'b','parede_oeste','/Game/M_Tile')

    def test_busca_por_nome_nao_inventa_semantica_e_preserva_ambiguidade(self):
        rows=[{'nome':'M_Wood_Light','caminho':'/Game/W'}, {'nome':'M_White_Tiles','caminho':'/Game/T'}]
        self.assertEqual(M.candidatos(rows,'piso de madeira clara'),[rows[0]])
        self.assertEqual(M.candidatos(rows,'parede de azulejo branco'),[rows[1]])
        self.assertEqual(M.candidatos(rows,'madeira azul'),[])
        self.assertEqual(len(M.candidatos(rows+[dict(rows[0],caminho='/Game/W2')],'madeira clara')),2)
