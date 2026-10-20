import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from director import acervo as A,acervo_operacao as O


class Operacao(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=self.root/'db.sqlite3'
        with A.abrir(self.db,escrita=True) as c:
            A.fonte(c,'artvip',licenca='apache-2.0')
            self.oid=A.objeto(c,'artvip','Articulated_objects/teste','chair')
            raw=b'modelo pequeno';self.raw=raw
            self.arquivo={'caminho':'Articulated_objects/teste/model.usd','bytes':len(raw),
                          'sha256':hashlib.sha256(raw).hexdigest()}
            for k,v in {'arquivos':[self.arquivo],'revisao_remota':'a'*40,'arquivo_principal':self.arquivo['caminho']}.items():
                A.caracteristica(c,self.oid,k,v,'teste','teste')

    def tearDown(self):self.tmp.cleanup()

    def pedido(self):
        return {'objeto':self.oid,'destino':str(self.root/'baixados'),'autorizar_download':True,'origem':'usuario/teste'}

    def test_planejamento_nao_baixa_e_rejeita_traversal(self):
        with patch.object(O.urllib.request,'urlopen',side_effect=AssertionError('nao deveria acessar rede')):
            self.assertEqual(O.planejar_download(self.oid,self.db)['bytes'],len(self.raw))
        with A.abrir(self.db,escrita=True) as c:
            A.caracteristica(c,self.oid,'arquivos',[{**self.arquivo,'caminho':'../fora.usd'}],'teste','teste')
        with self.assertRaises(ValueError):O.planejar_download(self.oid,self.db)

    def test_download_verifica_hash_reutiliza_sem_rede_e_liga_identidade(self):
        with patch.object(A,'PADRAO',str(self.root/'Director/db.sqlite3')):
            with patch.object(O.urllib.request,'urlopen',return_value=io.BytesIO(self.raw)) as rede:
                r=O.baixar(self.pedido(),self.db);self.assertEqual(rede.call_count,1)
            with patch.object(O.urllib.request,'urlopen',side_effect=AssertionError('nao repetir')):
                r2=O.baixar(self.pedido(),self.db);self.assertTrue(r2['arquivos'][0]['reutilizado'])
        self.assertEqual(A.executar({'acao':'detalhe','objeto':self.oid},self.db)['objeto']['arquivos'][0]['objeto'],self.oid)

    def test_hash_errado_nao_registra_nem_deixa_parcial(self):
        with patch.object(A,'PADRAO',str(self.root/'Director/db.sqlite3')):
            with patch.object(O.urllib.request,'urlopen',return_value=io.BytesIO(b'x'*len(self.raw))):
                with self.assertRaises(ValueError):O.baixar(self.pedido(),self.db)
        self.assertFalse(list(self.root.rglob('*.part')))
        with A.abrir(self.db) as c:self.assertEqual(c.execute('select count(*) from arquivos').fetchone()[0],0)

    def test_orcamento_e_autorizacao_antes_da_rede(self):
        with patch.object(O.urllib.request,'urlopen',side_effect=AssertionError('nao acessar')):
            with self.assertRaises(ValueError):O.baixar({**self.pedido(),'autorizar_download':False},self.db)
            with patch.object(A,'PADRAO',str(self.root/'Director/db.sqlite3')):
                with self.assertRaises(ValueError):O.baixar({**self.pedido(),'max_bytes':1},self.db)

    def test_falha_sql_nao_reexecuta_unreal_e_resultado_ue_permanece(self):
        with patch.object(O,'sincronizar',side_effect=OSError('R indisponivel')):
            r=O.apos_operacao('teste',{'ok':True,'revisao':2})
        self.assertTrue(r['ok']);self.assertFalse(r['acervo']['ok']);self.assertIn('nao repetir',r['acervo']['proxima_acao'])
        with patch.object(O,'sincronizar',side_effect=AssertionError('nao sincronizar falha')):
            self.assertFalse(O.apos_operacao('teste',{'ok':False})['ok'])

    def test_rotulos_nao_sao_fisica_e_idempotentes(self):
        r=O.rotular({},self.db);self.assertEqual(r['objetos_rotulados'],1)
        O.rotular({},self.db)
        with A.abrir(self.db) as c:
            self.assertEqual(c.execute("select count(*) from tags where idioma='pt' and texto='cadeira'").fetchone()[0],1)
            self.assertEqual(c.execute('select count(*) from verificacoes').fetchone()[0],0)

    def test_sincronizacao_preserva_modelo_versoes_e_nao_promove(self):
        from director import config as C
        from director.nucleo import planta as PL
        pasta=self.root/'cenas';p=PL.nova('teste')
        p['objetos']={'mesa':{'tipo':'asset','modelo':{'asset':'/Game/Director/Objetos/Mesa'}}}
        PL.gravar(str(pasta),p)
        with A.abrir(self.db,escrita=True) as c:A.indexar_busca(c)
        with patch.object(C,'CENAS',str(pasta)):
            O.sincronizar('teste',self.db)
            p['revisao']=1;p['objetos']['mesa']['x']=123;PL.gravar(str(pasta),p)
            O.sincronizar('teste',self.db)
        with A.abrir(self.db) as c:
            self.assertEqual(c.execute('select count(*) from instancias').fetchone()[0],1)
            self.assertEqual(c.execute("select count(*) from registros where entidade='instancia'").fetchone()[0],2)
            self.assertEqual(c.execute('select count(*) from instalacoes').fetchone()[0],1)
            self.assertEqual(c.execute('select count(*) from receitas').fetchone()[0],0)
            self.assertEqual(c.execute('select count(*) from busca where objeto=?',(self.oid,)).fetchone()[0],1)

    def test_usd_junta_declarada_nao_aprova_fisica(self):
        f=self.root/'model.usd';f.write_bytes(self.raw)
        A.executar({'acao':'arquivo','objeto':self.oid,'caminho':str(f),'origem':'teste'},self.db)
        class Editor:
            def chamar(self,nome,**kwargs):return {'resultado':{'juntas':[{'tipo':'PhysicsRevoluteJoint'}],'dependencias_ausentes':['faltou.usd']}}
        r=O.inspecionar_usd({'objeto':self.oid,'arquivo':str(f)},self.db,Editor())
        self.assertFalse(r['ok'])
        with A.abrir(self.db) as c:self.assertEqual(c.execute('select count(*) from verificacoes').fetchone()[0],0)


if __name__=='__main__':unittest.main()
