import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from director import acervo as A,acervo_coleta as C


class Coleta(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.pasta=self.root/'modelos';self.pasta.mkdir();self.db=self.root/'acervo.db'
        self.calls=[]

    def tearDown(self):self.tmp.cleanup()

    def modelo(self,nome='a.gltf'):
        p=self.pasta/nome;p.write_text(json.dumps({'asset':{'version':'2.0'},'buffers':[{'uri':'a.bin','byteLength':3}]}));
        (self.pasta/'a.bin').write_bytes(b'123');return p

    def inspetor(self,p):self.calls.append(p.name);return {'estado':'ok','dimensoes_cm':[1,2,3]}

    def runp(self,**kw):
        with patch.object(C,'worker',side_effect=self.inspetor):
            return C.arquivos({'pasta':str(self.pasta),**kw},self.db)

    def test_duas_rodadas_novo_modificado_dependencia_ausente_retorno(self):
        p=self.modelo();a=self.runp();self.assertEqual(a['contagens']['novos'],1)
        b=self.runp();self.assertEqual(b['contagens']['reutilizados'],1);self.assertEqual(len(self.calls),1)
        (self.pasta/'a.bin').write_bytes(b'456');self.assertEqual(self.runp()['contagens']['reinspecionados'],1)
        self.modelo('b.gltf');self.assertEqual(self.runp()['contagens']['novos'],1)
        p.unlink();self.assertEqual(self.runp()['contagens']['ausentes'],1)
        self.modelo();self.assertEqual(self.runp()['contagens']['reinspecionados'],1)
        with A.abrir(self.db) as c:self.assertGreater(c.execute('SELECT count(*) FROM inspecoes').fetchone()[0],3)

    def test_falha_nao_perde_sucesso_e_retoma_so_pendente(self):
        self.modelo();self.modelo('b.gltf')
        def f(p):
            self.calls.append(p.name)
            if p.name=='b.gltf':raise ValueError('falha de teste')
            return {'estado':'ok'}
        with patch.object(C,'worker',side_effect=f):r=C.arquivos({'pasta':str(self.pasta)},self.db)
        self.assertFalse(r['ok']);self.calls.clear()
        r=self.runp();self.assertEqual(self.calls,['b.gltf']);self.assertEqual(r['contagens']['reutilizados'],1)

    def test_inventario_parcial_nao_marca_ausentes(self):
        p=self.modelo();self.runp();p.unlink()
        with patch.object(C,'listar_arquivos',return_value=([],['pasta inacessivel'])):r=self.runp()
        self.assertFalse(r['completo']);self.assertEqual(r['contagens']['ausentes'],0)
        with A.abrir(self.db) as c:self.assertEqual(c.execute('SELECT presente FROM itens_coleta').fetchone()[0],1)

    def test_dependencia_ausente_ou_remota_nao_dispara_loader(self):
        p=self.modelo();(self.pasta/'a.bin').unlink()
        self.assertFalse(self.runp()['ok']);self.assertEqual(self.calls,[])
        p.write_text(json.dumps({'asset':{'version':'2.0'},'buffers':[{'uri':'https://example.com/a.bin'}]}))
        self.assertFalse(self.runp()['ok']);self.assertEqual(self.calls,[])

    def test_limite_retoma_sem_reinspecionar_os_prontos(self):
        self.modelo();self.modelo('b.gltf')
        r=self.runp(limite=1);self.assertFalse(r['completo']);self.assertEqual(len(self.calls),1)
        r=self.runp(limite=1);self.assertTrue(r['completo']);self.assertEqual(self.calls,['a.gltf','b.gltf'])

    def test_versao_inspetor_invalida_cache(self):
        self.modelo();self.runp()
        with patch.object(C,'VERSAO','2.0.0'):r=self.runp()
        self.assertEqual(r['contagens']['reinspecionados'],1)

    def test_interrupcao_preserva_itens_confirmados(self):
        self.modelo();self.modelo('b.gltf')
        def f(p):
            if p.name=='b.gltf':raise KeyboardInterrupt()
            return {'estado':'ok'}
        with patch.object(C,'worker',side_effect=f):
            with self.assertRaises(KeyboardInterrupt):C.arquivos({'pasta':str(self.pasta)},self.db)
        r=self.runp();self.assertEqual(r['contagens']['reutilizados'],1);self.assertEqual(self.calls,['b.gltf'])

    def test_pasta_inexistente_nao_apaga_estado(self):
        self.modelo();self.runp()
        with self.assertRaises(ValueError):C.arquivos({'pasta':str(self.pasta/'nao-existe')},self.db)
        with A.abrir(self.db) as c:self.assertEqual(c.execute('SELECT presente FROM itens_coleta').fetchone()[0],1)

    def test_coleta_concorrente_mesmo_escopo_recusada(self):
        with C.trava_escopo(self.db,'abc'):
            with self.assertRaises(ValueError):
                with C.trava_escopo(self.db,'abc'):pass
        with C.trava_escopo(self.db,'abc'):pass

    def test_limite_tambem_conta_falhas_antes_do_loader(self):
        for n in ['a.glb','b.glb','c.glb']:(self.pasta/n).write_bytes(b'GLB invalido')
        r=self.runp(limite=1)
        self.assertEqual(r['contagens']['erros'],1);self.assertFalse(r['completo']);self.assertEqual(self.calls,[])


if __name__=='__main__':unittest.main()
