import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from director import acervo as A,revisao as R


class Referencias(unittest.TestCase):
    def test_consulta_real_sql_compacta_preserva_banco_e_nao_muda_nota(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'acervo.sqlite3'
            stats=json.loads((Path(__file__).resolve().parents[2]/'docs/pilotos/spatiallm-resumo-20261021.json').read_text(encoding='utf-8'))
            with A.abrir(db,escrita=True) as c:
                A.fonte(c,'spatiallm-dataset')
                oid=A.objeto(c,'spatiallm-dataset','chunk','amostra','amostra_layout')
                A.caracteristica(c,oid,'estatisticas_layout',stats,'ensaio','sha-fonte')
            antes=hashlib.sha256(db.read_bytes()).hexdigest()
            refs=R.referencias_layout([oid,oid],db)
            self.assertEqual(len(refs),1);self.assertEqual(refs[0]['amostra']['dormitorios'],149)
            self.assertEqual(refs[0]['revisao_fonte'],'sha-fonte')
            self.assertNotIn('tipos_quartos',refs[0]);self.assertIn('nao altera notas',refs[0]['limite'])
            self.assertEqual(hashlib.sha256(db.read_bytes()).hexdigest(),antes)
            notas={k:{'nota':8,'justificativa':'opiniao'} for k in R.ITENS}
            with patch.object(R,'referencias_layout',return_value=refs),patch.object(R.PL,'carregar',return_value={'objetos':{}}),patch.object(R.V,'verificar',return_value={'aprovado':True}):
                r=R.avaliar('x',{'origem':'teste','notas':notas,'referencias_layout':[oid]},None)
            self.assertEqual(r['referencias_layout'],refs);self.assertEqual(r['soma'],48)
            with self.assertRaises(ValueError):R.referencias_layout(['inexistente'],db)
    def test_sem_referencia_nao_abre_sql_e_rejeita_entrada_ampla(self):
        with patch.object(A,'abrir',side_effect=AssertionError('nao abrir')):
            self.assertEqual(R.referencias_layout([]),[])
            for ids in ('um-id',[1],['a']*4):
                with self.assertRaises(ValueError):R.referencias_layout(ids)
