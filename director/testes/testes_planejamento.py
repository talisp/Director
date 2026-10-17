import unittest
import importlib.util
from director.planejamento import resolver


@unittest.skipUnless(importlib.util.find_spec('ortools'), 'solver opcional em .venv-planejamento')
class Planejamento(unittest.TestCase):
    def test_contencao_e_area_de_uso_com_caso_inviavel(self):
        q={'dimensoes_cm':[200,200],'objetos':[{'id':'a','dimensoes_cm':[100,60,180],'uso_frente_cm':70}],'segundos':1}
        r=resolver(q);self.assertTrue(r['ok']);self.assertEqual(len(r['objetos']),1)
        q['dimensoes_cm']=[80,80]
        self.assertFalse(resolver(q)['ok'])

    def test_reserva_fracionaria_e_compactacao_limitada(self):
        q={'minimo_cm':[80,80],'maximo_cm':[250,250],'objetos':[{'id':'a','dimensoes_cm':[100,60,80],'uso_frente_cm':70}], 'reservas':[[0.5,0.5,10.2,10.2]],'segundos':1}
        r=resolver(q);self.assertTrue(r['ok']);self.assertTrue(r['otimo_no_modelo'])
        self.assertLess(r['area_m2'],6.25)

class Paredes(unittest.TestCase):
    def test_compartilhamento_planejado_e_ausencia(self):
        from director.planejamento import compartilhadas
        a={'tipo':'sala','x':0,'y':0,'largura':400,'comprimento':400,'parede':15}
        b={**a,'x':415,'largura':200}
        d={'objetos':{'a':a,'b':b}}
        self.assertEqual(compartilhadas(d)[0]['comprimento_planejado_cm'],400)
        b['x']=500;self.assertEqual(compartilhadas(d),[])


QUARTO=[{'id':'cama','dimensoes_cm':[100,200,82],'uso_frente_cm':65},
        {'id':'criado','dimensoes_cm':[40,41,44],'uso_frente_cm':35,'ao_lado_de':'cama'},
        {'id':'guarda','dimensoes_cm':[100,62,200],'uso_frente_cm':65},
        {'id':'mesa','dimensoes_cm':[100,55,75],'uso_frente_cm':75},
        {'id':'cadeira','dimensoes_cm':[50,50,83],'uso_frente_cm':0,'na_frente_de':'mesa'}]
PORTA_OESTE=[{'id':'porta','tipo':'porta','parede':'oeste','posicao':100,'largura':90,'altura':210}]


def _caixa(o):
    w,d=o['dimensoes_cm'][:2]
    if o['giro'] in (90,270):w,d=d,w
    return [o['x_m']*100-w/2,o['y_m']*100-d/2,o['x_m']*100+w/2,o['y_m']*100+d/2]


@unittest.skipUnless(importlib.util.find_spec('ortools') and importlib.util.find_spec('shapely'),'solver opcional em .venv-planejamento')
class QuartoDoTeste(unittest.TestCase):
    """O quarto de 17/10: antes, o planejar reprovava 2,60 x 3,50 que o ensaio do Codex mostrou caber."""
    def test_quarto_de_260_por_350_passa_com_porta_oeste(self):
        r=resolver({'dimensoes_cm':[260,350],'objetos':QUARTO,'aberturas':PORTA_OESTE,'segundos':20})
        self.assertTrue(r['ok'],r.get('detalhe'));self.assertTrue(r['verificacao2d']['aprovado'])
        self.assertTrue(all(a['alcancado'] for a in r['verificacao2d']['acessos']))
        o={x['id']:x for x in r['objetos']}
        # cadeira encostada na frente da mesa, criado com o mesmo giro e encostado de lado na cama
        m,c=_caixa(o['mesa']),_caixa(o['cadeira'])
        self.assertEqual(o['cadeira']['giro'],(o['mesa']['giro']+180)%360)
        self.assertTrue(any(abs(a-b)<1e-6 for a,b in ((c[3],m[1]),(c[0],m[2]),(c[1],m[3]),(c[2],m[0]))))
        self.assertEqual(o['criado']['giro'],o['cama']['giro'])
        k,b=_caixa(o['criado']),_caixa(o['cama'])
        self.assertTrue(any(abs(a-x)<1e-6 for a,x in ((k[2],b[0]),(k[0],b[2]),(k[3],b[1]),(k[1],b[3]))))

    def test_compacto_fica_menor_que_o_do_hermes(self):
        r=resolver({'minimo_cm':[220,260],'maximo_cm':[300,360],'objetos':QUARTO,'aberturas':PORTA_OESTE,'segundos':30})
        self.assertTrue(r['ok'],r.get('detalhe'));self.assertLess(r['area_m2'],9.1)

    def test_impossivel_explica_quem_nao_cabe_sozinho(self):
        r=resolver({'dimensoes_cm':[150,150],'objetos':QUARTO,'aberturas':PORTA_OESTE,'segundos':5})
        self.assertFalse(r['ok']);self.assertEqual(r['motivo'],'impossivel_no_modelo')
        self.assertIn('cama',r['nao_cabem_sozinhos']);self.assertNotIn('cadeira',r['nao_cabem_sozinhos'])

    def test_porta_tem_de_caber_na_parede_testada(self):
        q={'minimo_cm':[200,100],'maximo_cm':[300,140],'objetos':[{'id':'a','dimensoes_cm':[40,40,40],'uso_frente_cm':0}],
           'aberturas':[{'id':'p','tipo':'porta','parede':'oeste','posicao':150,'largura':90,'altura':210}],'segundos':2}
        r=resolver(q);self.assertFalse(r['ok']);self.assertEqual(r['motivo'],'impossivel_no_modelo')

    def test_referencia_ausente_e_recusada(self):
        with self.assertRaises(ValueError):
            resolver({'dimensoes_cm':[300,300],'objetos':[{'id':'c','dimensoes_cm':[50,50,80],'na_frente_de':'mesa'}]})


@unittest.skipUnless(importlib.util.find_spec('ortools') and importlib.util.find_spec('shapely'),'solver opcional em .venv-planejamento')
class SalaHipotetica(unittest.TestCase):
    def test_tamanho_hipotetico_nao_abre_editor_nem_muda_planta(self):
        import hashlib,shutil,tempfile
        from pathlib import Path
        from director import config as C, planejamento
        orig=Path(__file__).resolve().parents[1]/'cenas'/'sala'/'planta.json'
        with tempfile.TemporaryDirectory() as tmp:
            destino=Path(tmp)/'sala'/'planta.json';destino.parent.mkdir();shutil.copy(orig,destino)
            antes=hashlib.sha256(destino.read_bytes()).hexdigest()
            velho=C.CENAS;C.CENAS=tmp
            try:
                r=planejamento.planejar('sala',{'sala':'sala1','minimo_cm':[300,300],'maximo_cm':[500,400],'segundos':5,
                    'objetos':[{'id':'armario','dimensoes_cm':[100,60,180],'uso_frente_cm':70}]},None)
            finally:C.CENAS=velho
            self.assertEqual(hashlib.sha256(destino.read_bytes()).hexdigest(),antes)
        self.assertTrue(r['ok'],r.get('detalhe'))
        self.assertIn('NAO foi alterada',r['origem']['dimensoes'])
        self.assertEqual(r['mantidos_da_cena'],['mesa1'])
        self.assertEqual({a['id'] for a in r['verificacao2d']['acessos']},{'armario'})

    def test_objeto_apoiado_nao_ocupa_o_chao(self):
        import json,shutil,tempfile
        from pathlib import Path
        from director import config as C, planejamento
        orig=Path(__file__).resolve().parents[1]/'cenas'/'sala'/'planta.json'
        d=json.loads(orig.read_text(encoding='utf-8'))
        m=d['objetos']['mesa1']
        d['objetos']['note']={'tipo':'asset','sala':'sala1','x':m['x'],'y':m['y'],'z':76,'giro':0,'largura':30,'profundidade':20,'altura':2,'sobre':'mesa1',
            'modelo':{'asset':'/Game/N','tamanho':[30,20,2],'centro':[0,0,1],'min_z':0},'fisica':{'simular':True,'massa_kg':2,'amortecimento_linear':.5,'amortecimento_angular':1,'subir':False}}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'sala').mkdir();(Path(tmp)/'sala'/'planta.json').write_text(json.dumps(d),encoding='utf-8')
            velho=C.CENAS;C.CENAS=tmp
            try:r=planejamento.planejar('sala',{'sala':'sala1','minimo_cm':[300,300],'maximo_cm':[500,400],'segundos':5,
                    'objetos':[{'id':'mesa1','dimensoes_cm':[120,80,75],'uso_frente_cm':60}]},None)
            finally:C.CENAS=velho
        self.assertTrue(r['ok'],r.get('detalhe'));self.assertNotIn('mantidos_da_cena',r)
