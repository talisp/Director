import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from director import acervo as A,acervo_fontes as F


class Fontes(unittest.TestCase):
    def test_paletas_dois_formatos_e_path_blueprint(self):
        texto='- chair | Wood chair | furniture | 1x0.5x2 m | /Game/Pack/SM_Chair.SM_Chair\n- BP_Seat | 1x2x3 m | /Game/Pack/BP_Seat.BP_Seat_C'
        rows,erros=F.paleta(texto)
        self.assertFalse(erros);self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['dimensoes_cm'],[100,50,200])
        self.assertEqual(rows[1]['caminho'],'/Game/Pack/BP_Seat');self.assertEqual(rows[1]['categoria'],'')

    def test_paleta_invalida_nao_inventa_dimensoes(self):
        rows,erros=F.paleta('- c | Chair | chair | nanx1x2 m | /Game/Pack/A.A')
        self.assertEqual(rows,[]);self.assertEqual(len(erros),1)

    def test_artvip_recursos_nao_sao_objetos_independentes(self):
        d={'siblings':[{'rfilename':'Articulated_objects/small_furniture/chair/A/model_A.usd','size':10},
                       {'rfilename':'Articulated_objects/small_furniture/chair/A/resource/link.usd','size':20},
                       {'rfilename':'Articulated_objects/small_furniture/chair/A/origin/model_base.usd','size':30},
                       {'rfilename':'Scenes/SceneA.usd','size':40}]}
        rows=F.artvip(d);self.assertEqual(len(rows),1);self.assertEqual(len(rows[0]['arquivos']),3)

    def test_importacao_idempotente_pacotes_nao_sao_modelos_instalados(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);db=p/'db.sqlite3'
            pack={'schema':'code4scene.packs.v1','packs':[{'folder':'Pack','title':'Pack','fab_url':'https://www.fab.com/listings/example','price_usd_at_check':10},
                 {'folder':'Unknown','title':None,'license':None,'fab_url':None}]}
            info={'sha':'revA','cardData':{'license':'apache-2.0'},'siblings':[{'rfilename':'Articulated_objects/small_furniture/chair/A/model_A.usd','size':10}]}
            (p/'artvip-info.json').write_text(A.dump(info));(p/'code4scene-packs.yaml').write_text('fixture')
            rows,_=F.paleta('- chair | Wood chair | furniture | 1x1x1 m | /Game/Pack/Chair.Chair')
            (p/'code4scene-paletas.json').write_text(A.dump({'revision':'revC','tarefas':[{'caso':'case_1','itens':rows}]}))
            hashes={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in p.iterdir()}
            (p/'manifesto.json').write_text(A.dump({'artvip_revision':'revA','code4scene_revision':'revC','sha256':hashes}))
            with patch.object(F,'yaml_seguro',return_value=pack):
                self.assertTrue(F.importar({'pasta':str(p)},db)['ok'])
                a=A.executar({'acao':'resumo'},db)['contagens']
                self.assertTrue(F.importar({'pasta':str(p)},db)['reutilizado'])
                self.assertEqual(a,A.executar({'acao':'resumo'},db)['contagens'])
                with patch.object(F,'IMPORTADOR_SHA','outra-versao-carregada'):
                    self.assertFalse(F.importar({'pasta':str(p)},db)['reutilizado'])
                self.assertEqual(a,A.executar({'acao':'resumo'},db)['contagens'])
            self.assertEqual(a['objetos'],2);self.assertEqual(a['arquivos'],0);self.assertEqual(a['instalacoes'],0)
            with A.abrir(db) as c:
                self.assertEqual(c.execute("SELECT nome,licenca FROM pacotes WHERE chave='Unknown'").fetchone()[:],('Unknown','nao_confirmada'))
            r=A.executar({'acao':'buscar','texto':'cadeira'},db)
            self.assertEqual(r['total'],2);self.assertTrue(all(x['disponibilidade']=='remoto' for x in r['resultados']))
            (p/'artvip-info.json').write_text('{}')
            with patch.object(F,'yaml_seguro',return_value=pack):
                with self.assertRaises(ValueError):F.importar({'pasta':str(p)},db)


if __name__=='__main__':unittest.main()
