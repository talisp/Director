import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
from contextlib import closing
import unittest
from unittest.mock import patch

from director import acervo as A, acervo_operacao as O, acervo_preparacao as P


class Preparacao(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.db=self.root/'db.sqlite3'
        self.raw=b'USD teste';self.dep=b'textura'
        with A.abrir(self.db,escrita=True) as c:
            A.fonte(c,'artvip',licenca='apache-2.0')
            self.oid=A.objeto(c,'artvip','Articulated_objects/teste','mesa')
            files=[{'caminho':'Articulated_objects/teste/'+nome,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
                   for nome,raw in [('model.usd',self.raw),('textura.png',self.dep)]]
            for k,v in {'arquivos':files,'revisao_remota':'a'*40,'arquivo_principal':files[0]['caminho']}.items():A.caracteristica(c,self.oid,k,v,'teste','teste')
            A.indexar_busca(c)
        self.inspecao={'ok':True,'engine':'engine-teste','openusd':[1,2,3],'dependencias_ausentes':[],
            'caixa_stage_cm':{'dimensoes':[100,50,75]},'up_axis':'Z','meshes':2,'juntas':[{'path':'/mesa/gaveta','tipo':'PhysicsPrismaticJoint'}]}
        self.patchbase=patch.object(A,'PADRAO',str(self.root/'Director/db.sqlite3'));self.patchbase.start()
        self.rede=patch.object(O.urllib.request,'urlopen',side_effect=lambda req,**kw:io.BytesIO(self.raw if req.full_url.endswith('usd') else self.dep));self.rede.start()
        self.inspector=patch.object(O,'inspecionar_usd',return_value=self.inspecao);self.mockinspect=self.inspector.start()

    def tearDown(self):
        self.inspector.stop();self.rede.stop();self.patchbase.stop();self.tmp.cleanup()

    def pedido(self,**kw):return {'acao':'preparar','objeto':self.oid,'origem':'usuario/teste','autorizar_download':True,'pedido_id':'teste',**kw}
    def preparar(self,**kw):return A.executar(self.pedido(**kw),self.db)
    def ficha(self,**kw):return A.executar({'acao':'ficha','objeto':self.oid,**kw},self.db)

    def test_prepara_reutiliza_e_outro_pedido_nao_duplica(self):
        r=self.preparar();self.assertTrue(r['ok'],r);self.assertEqual(r['geometria']['caixa_stage_cm']['dimensoes'],[100,50,75])
        self.assertEqual(r['fisica'],'nao_testada');self.assertEqual(r['juntas_declaradas'],1)
        with patch.object(O.urllib.request,'urlopen',side_effect=AssertionError('nao baixar')):
            self.assertTrue(self.preparar()['inspecao_reutilizada'])
            self.assertEqual(self.preparar(pedido_id='outro')['variante'],r['variante'])
        self.assertEqual(self.mockinspect.call_count,1)
        with A.abrir(self.db) as c:self.assertEqual(c.execute('SELECT count(*) FROM variantes').fetchone()[0],1)

    def test_dependencia_alterada_invalida_leitura_sem_expor_medida_vigente(self):
        self.preparar()
        with A.abrir(self.db) as c:cfg=json.loads(c.execute('SELECT configuracao_json FROM variantes').fetchone()[0])
        Path(cfg['arquivos'][1]['caminho']).write_bytes(b'corrompida')
        f=self.ficha();self.assertEqual(f['validade'],'obsoleta');self.assertIsNone(f['geometria']);self.assertTrue(f['bloqueios'])
        r=self.preparar();self.assertFalse(r['ok']);self.assertIn('divergente',r['erro'])

    def test_versao_coletor_invalida(self):
        self.preparar()
        with patch.object(P,'VERSAO','nova'):self.assertEqual(self.ficha()['validade'],'obsoleta')

    def test_revisao_catalogo_invalida_sem_apagar_historico(self):
        self.preparar()
        with A.abrir(self.db,escrita=True) as c:A.caracteristica(c,self.oid,'revisao_remota','b'*40,'teste','teste')
        f=self.ficha();self.assertEqual(f['validade'],'obsoleta');self.assertIsNone(f['geometria'])
        with A.abrir(self.db) as c:self.assertEqual(c.execute('SELECT count(*) FROM variantes').fetchone()[0],1)

    def test_retomada_inspecao_sem_novo_download(self):
        self.mockinspect.side_effect=RuntimeError('ponte caiu')
        r=self.preparar();self.assertFalse(r['ok']);self.assertEqual(r['etapa'],'inspecionando')
        self.mockinspect.side_effect=None
        with patch.object(O.urllib.request,'urlopen',side_effect=AssertionError('nao baixar')):self.assertTrue(self.preparar()['ok'])

    def test_dependencias_ausentes_impedem_importacao(self):
        self.inspecao['dependencias_ausentes']=['faltou.usd']
        with patch.object(O,'importar',side_effect=AssertionError('nao importar')):
            r=self.preparar(importar=True);self.assertFalse(r['ok']);self.assertTrue(r['bloqueios'])

    def test_importacao_e_reuso_entre_pedidos_com_conferencia(self):
        with patch.object(O,'importar',return_value={'ok':True,'malhas':[{'asset':'/Game/Teste'}]}) as imp,patch.object(O,'conferir_importacao',return_value={'ok':True}) as conferir:
            self.assertTrue(self.preparar(importar=True)['ok'])
            self.assertTrue(self.preparar(importar=True,pedido_id='outro')['ok'])
            self.assertEqual(imp.call_count,1);self.assertEqual(conferir.call_count,1)

    def test_queda_importacao_nao_repete(self):
        with patch.object(O,'importar',side_effect=RuntimeError('queda depois de importar')) as imp:
            self.assertFalse(self.preparar(importar=True)['ok'])
            r=self.preparar(importar=True);self.assertEqual(r['estado'],'requer_conferencia');self.assertEqual(imp.call_count,1)

    def test_falha_sql_depois_do_motor_nao_reimporta(self):
        original=P._persistir
        def gravar(*args,**kwargs):
            if args[4]=='concluido':raise OSError('SQL indisponivel depois do motor')
            return original(*args,**kwargs)
        with patch.object(P,'_persistir',side_effect=gravar),patch.object(O,'importar',return_value={'ok':True,'malhas':[{'asset':'/Game/Teste'}]}) as imp:
            self.assertFalse(self.preparar(importar=True)['ok'])
            self.assertEqual(self.preparar(importar=True)['estado'],'requer_conferencia');self.assertEqual(imp.call_count,1)

    def test_assets_alterados_nao_sobrescreve(self):
        with patch.object(O,'importar',return_value={'ok':True,'malhas':[{'asset':'/Game/Teste'}]}) as imp,patch.object(O,'conferir_importacao',return_value={'ok':False,'motivo':'alterado'}):
            self.preparar(importar=True)
            self.assertFalse(self.preparar(importar=True,pedido_id='novo')['ok']);self.assertEqual(imp.call_count,1)

    def test_api_recusa_sql_caminhos_orcamento_e_medidas(self):
        for k in ('sql','destino','url','db','max_bytes','dimensoes','resultado'):
            with self.subTest(k=k),self.assertRaises(ValueError):self.preparar(**{k:'inventado'})
        with self.assertRaises(ValueError):self.preparar(autorizar_download=False)

    def test_orcamento_operador_antes_da_rede(self):
        with patch.dict('os.environ',{'DIRECTOR_ACERVO_MAX_BYTES':'1'}),self.assertRaises(ValueError):self.preparar()

    def test_declaracao_nao_certifica_e_fk_preserva(self):
        r=A.executar({'acao':'verificacao','objeto':self.oid,'capacidade':'voar','resultado':'aprovado','versao':'inventada','evidencia':'inventada'},self.db)
        self.assertFalse(r['validado'])
        r=A.executar({'acao':'anotar','objeto':self.oid,'origem':'teste','texto':'dimensao inventada; DROP TABLE objetos'},self.db)
        self.assertFalse(r['validado'])
        with self.assertRaises(ValueError):A.executar({'acao':'anotar','objeto':'nao existe','origem':'teste','texto':'x'},self.db)
        with A.abrir(self.db) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM verificacoes').fetchone()[0],0)
            self.assertEqual(c.execute('SELECT count(*) FROM anotacoes_acervo').fetchone()[0],2)
            self.assertEqual(c.execute('PRAGMA quick_check').fetchone()[0],'ok')

    def test_legado_capacidades_antigas_nao_sao_ocultadas(self):
        with A.abrir(self.db,escrita=True) as c:
            for i in range(6):c.execute('INSERT INTO verificacoes(objeto,capacidade,resultado,evidencia,versao,criado_em) VALUES(?,?,?,?,?,?)',
                (self.oid,'interior' if i==0 else 'cap'+str(i),'reprovado' if i==0 else 'aprovado','legado','1',A.agora()))
        self.assertEqual(len(self.ficha()['verificacoes_legadas']),6)

    def test_busca_compacta_e_assunto_sem_inventar(self):
        self.preparar()
        r=A.executar({'acao':'buscar','texto':'mesa'},self.db)['resultados'][0]
        self.assertEqual(r['preparo']['validade'],'vigente')
        self.assertEqual(self.ficha(assunto='animacoes')['animacoes']['estado'],'desconhecido')
        self.assertLess(len(A.dump(self.ficha())),2500)

    def test_migracao_backup_e_rollback(self):
        legacy=self.root/'legacy.sqlite3'
        with closing(sqlite3.connect(legacy)) as c:
            c.execute('CREATE TABLE sentinela(valor)');c.execute("INSERT INTO sentinela VALUES('preservar')");c.execute('PRAGMA user_version=3');c.commit()
        with A.abrir(legacy,escrita=True) as c:self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],4)
        with closing(sqlite3.connect(str(legacy)+'.antes-v4.sqlite3')) as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],3);self.assertEqual(c.execute('SELECT valor FROM sentinela').fetchone()[0],'preservar')
        with self.assertRaises(RuntimeError),A.abrir(legacy,escrita=True) as c:
            c.execute("UPDATE sentinela SET valor='nao persistir'");raise RuntimeError('falha')
        with A.abrir(legacy) as c:self.assertEqual(c.execute('SELECT valor FROM sentinela').fetchone()[0],'preservar')


if __name__=='__main__':unittest.main()
