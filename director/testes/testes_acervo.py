import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from director import acervo as A


class Acervo(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.db=self.root/'acervo.sqlite3'
        self.runp({'acao':'iniciar'})

    def tearDown(self):
        self.tmp.cleanup()

    def runp(self,p):
        return A.executar(p,self.db)

    def gravar(self,nome,dados):
        p=self.root/nome;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(dados),encoding='utf-8');return str(p)

    def test_hssd_idempotente_aliases_limite_e_sem_download(self):
        p=self.gravar('indice.json',{'chair.n.01':[{'id':'abc','name':'wood chair','up':'0,0,1'},
                                                 {'id':'abc','name':'wood chair','up':'0,0,1'}]})
        for _ in range(2):self.runp({'acao':'hssd','indice':p})
        r=self.runp({'acao':'buscar','texto':'cadeira','limite':1})
        self.assertEqual(r['total'],1)
        self.assertEqual(r['resultados'][0]['disponibilidade'],'remoto')
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['arquivos'],0)
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['registros'],1)
        self.assertEqual(self.runp({'acao':'buscar','texto':'de'})['resultados'],[])
        with self.assertRaises(ValueError):self.runp({'acao':'buscar','texto':'chair','limite':0})

    def test_hash_duplicado_nome_igual_e_arquivo_modificado(self):
        a=self.root/'a';b=self.root/'b';a.mkdir();b.mkdir()
        (a/'chair.glb').write_bytes(b'original');(b/'chair.glb').write_bytes(b'original')
        for p in [a,b]:self.runp({'acao':'varrer','pasta':str(p)})
        r=self.runp({'acao':'resumo'})['contagens'];self.assertEqual(r['objetos'],1);self.assertEqual(r['arquivos'],2)
        (b/'chair.glb').write_bytes(b'outro modelo')
        self.runp({'acao':'varrer','pasta':str(b)})
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['objetos'],2)

    def test_sinonimo_composto_nao_traz_escrivaninha_para_cadeira(self):
        p=self.gravar('indice.json',{'x':[{'id':'a','name':'wood chair'},{'id':'b','name':'desk'}]})
        self.runp({'acao':'hssd','indice':p})
        r=self.runp({'acao':'buscar','texto':'cadeira'})
        self.assertEqual([x['nome'] for x in r['resultados']],['wood chair'])

    def test_fonte_filtra_antes_do_limite_e_bytes_nao_sao_medidas(self):
        with A.abrir(self.db,escrita=True) as c:
            for fonte in ('artvip','outra'):
                A.fonte(c,fonte)
                for i in range(9):
                    oid=A.objeto(c,fonte,str(i),'table')
                    if fonte=='artvip':A.caracteristica(c,oid,'arquivos',[{'bytes':20},{'bytes':30}],'teste','teste')
            A.indexar_busca(c)
        r=self.runp({'acao':'buscar','texto':'mesa','fonte':'artvip','disponibilidade':'remoto','limite':2})
        self.assertEqual(r['total'],9);self.assertTrue(r['limitado'])
        self.assertEqual(len(r['resultados']),2)
        self.assertTrue(all(x['fonte']=='artvip' and x['bytes_download']==50 and x['fisica']=='nao_certificada' for x in r['resultados']))
        with self.assertRaises(ValueError):self.runp({'acao':'buscar','texto':'mesa','fonte':'inexistente'})
        with A.abrir(self.db,escrita=True) as c:
            oid=r['resultados'][0]['id']
            A.caracteristica(c,oid,'arquivos',[{'bytes':None}],'teste','teste')
        r=self.runp({'acao':'buscar','texto':'mesa','fonte':'artvip','limite':50})
        self.assertIsNone(next(x for x in r['resultados'] if x['id']==oid)['bytes_download'])

    def test_cli_filtros_explicitos_nao_entram_no_texto(self):
        with patch.object(A,'executar',return_value={'ok':True}) as executar:
            A.cli(['buscar','--fonte','artvip','mesa','--disponibilidade','remoto'])
            executar.assert_called_once_with({'acao':'buscar','fonte':'artvip','disponibilidade':'remoto','texto':'mesa'})
        for args in [['buscar','--fonte'],['buscar','--outro','x'],['buscar','--fonte','a','--fonte','b']]:
            with self.assertRaises(ValueError):A.cli(args)

    def test_cli_pedido_literal_arquivo_ou_stdin_equivalentes(self):
        pedido={'acao':'buscar','texto':'mesa','fonte':'artvip'}
        texto=json.dumps(pedido);arquivo=self.gravar('pedido.json',pedido)
        for entrada in (texto,arquivo,'-'):
            with patch.object(A,'executar',return_value={'ok':True}) as executar,patch('sys.stdin',io.StringIO(texto)):
                self.assertTrue(A.cli(['pedido',entrada])['ok'])
                executar.assert_called_once_with(pedido)
        with patch('sys.stdin',io.StringIO('[]')):
            with self.assertRaises(ValueError):A.cli(['pedido','-'])

    def test_snapshot_nao_vira_modelo_e_promocao_guarda_revisoes(self):
        p=self.gravar('cenas/sala/planta.json',{'nivel':'/Game/L_sala','objetos':{
            'mesa':{'tipo':'mesa','largura':100},'copo':{'tipo':'copo','sobre':'mesa'}}})
        pedido={'acao':'plantas','pasta':str(self.root/'cenas'),'projeto':str(self.root/'lab.uproject')}
        self.runp(pedido)
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['objetos'],0)
        ins=self.runp({'acao':'instancias','nivel':'/Game/L_sala'})['instancias']
        iid=next(x['id'] for x in ins if x['nome']=='copo')
        promover={'acao':'promover','instancia':iid,'nome':'copo sobre mesa','origem':'ensaio-1','tags':['cup','copo']}
        oid=self.runp(promover)['objeto']
        d=self.runp({'acao':'detalhe','objeto':oid})['objeto']
        self.assertEqual(set(json.loads(d['receitas'][0]['dependencias_json'])['objetos_contexto']),{'mesa','copo'})
        self.runp(pedido)  # referencia a instancia nao impede atualizar
        self.runp(promover)
        pl=json.loads(Path(p).read_text());pl['objetos']['copo']['altura']=20;Path(p).write_text(json.dumps(pl))
        with self.assertRaises(ValueError):self.runp(promover)
        self.runp(pedido);self.runp(promover)
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['receitas'],1)
        with A.abrir(self.db) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM registros WHERE entidade='receita'").fetchone()[0],2)

    def test_hash_divergente_nao_se_declara_baixado(self):
        f=self.root/'chair.glb';f.write_bytes(b'arquivo')
        p=self.gravar('local.json',{'itens':[{'nome':'chair','origem':'offline','caminho':str(f),'sha256':'errado'}]})
        r=self.runp({'acao':'indice','indice':p,'projeto':'lab.uproject'})
        self.assertFalse(r['ok']);self.assertEqual(self.runp({'acao':'resumo'})['contagens']['arquivos'],0)

    def test_download_posterior_vincula_objeto_remoto_sem_duplicar(self):
        p=self.gravar('indice.json',{'x':[{'id':'abc','name':'chair'}]});self.runp({'acao':'hssd','indice':p})
        oid=self.runp({'acao':'buscar','texto':'chair'})['resultados'][0]['id']
        f=self.root/'abc.glb';f.write_bytes(b'arquivo de teste, nao modelo real')
        r=self.runp({'acao':'arquivo','objeto':oid,'caminho':str(f),'origem':'download autorizado'})
        self.assertEqual(r['objeto'],oid)
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['objetos'],1)
        self.assertEqual(self.runp({'acao':'buscar','texto':'chair'})['resultados'][0]['disponibilidade'],'baixado')
        self.runp({'acao':'instalacao','objeto':oid,'projeto':'lab.uproject','caminho':'/Game/Chair','origem':'ensaio-importacao'})
        p=self.gravar('catalogo.json',{'itens':[{'nome':'Chair','origem':'projeto','caminho':'/Game/Chair'}]})
        self.runp({'acao':'indice','indice':p,'projeto':'lab.uproject'})
        self.assertEqual(self.runp({'acao':'resumo'})['contagens']['objetos'],1)
        self.assertEqual(self.runp({'acao':'buscar','texto':'chair'})['resultados'][0]['disponibilidade'],'importado_snapshot')

    def test_verificacao_com_procedencia_e_fk(self):
        p=self.gravar('indice.json',{'x':[{'id':'abc','name':'chair'}]});self.runp({'acao':'hssd','indice':p})
        oid=self.runp({'acao':'buscar','texto':'chair'})['resultados'][0]['id']
        with self.assertRaises(ValueError):self.runp({'acao':'verificacao','objeto':oid,'resultado':'aprovado'})
        self.runp({'acao':'verificacao','objeto':oid,'resultado':'nao_testado','capacidade':'colisao','versao':'sha1','evidencia':'inspecao-pendente'})
        self.runp({'acao':'tags','objeto':oid,'origem':'teste','tags':[{'texto':'cadeira','idioma':'pt'}]})
        self.assertEqual(self.runp({'acao':'detalhe','objeto':oid})['objeto']['verificacoes'][0]['resultado'],'nao_testado')


if __name__=='__main__':unittest.main()
