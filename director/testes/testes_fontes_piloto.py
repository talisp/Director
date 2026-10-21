import hashlib,io,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from director import acervo as A,fontes_piloto as F


class Fontes(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.raiz=Path(self.tmp.name)
        self.base=patch.object(A,'PADRAO',str(self.raiz/'Director/acervo.sqlite3'));self.base.start()
    def tearDown(self):self.base.stop();self.tmp.cleanup()
    def baixar(self,**kw):return F.baixar('https://example.test/asset',self.raiz/'cache/asset',max_bytes=4,**kw)
    def zip(self,nome='Color.jpg'):
        p=self.raiz/'arquivo.zip'
        normal=nome.replace('\\','/')
        with zipfile.ZipFile(p,'w') as z:z.writestr(normal,b'jpg ficticio');z.writestr('instalar.py',b'nao executar')
        # ZipFile normaliza separador ao escrever no Windows. Preserva o nome
        # bruto hostil no cabecalho/indice, como um ZIP externo poderia trazer.
        if normal!=nome:p.write_bytes(p.read_bytes().replace(normal.encode(),nome.encode()))
        return p
    def test_hash_e_cache_sem_rede(self):
        with patch.object(F.urllib.request,'urlopen',return_value=io.BytesIO(b'1234')):r=self.baixar(tamanho=4,sha256=hashlib.sha256(b'1234').hexdigest())
        self.assertTrue(r['hash_remoto_conferido'])
        with patch.object(F.urllib.request,'urlopen',side_effect=AssertionError('nao repetir')):self.assertTrue(self.baixar()['reutilizado'])
        Path(r['caminho']).write_bytes(b'xxxx')
        with self.assertRaises(ValueError):self.baixar()
    def test_limite_hash_e_parcial(self):
        for b,kw in [(b'12345',{}),(b'1234',{'sha256':'a'*64}),(b'123',{'tamanho':4})]:
            with patch.object(F.urllib.request,'urlopen',return_value=io.BytesIO(b)),self.assertRaises(ValueError):self.baixar(**kw)
        self.assertFalse(list(self.raiz.rglob('*.part')))
    def test_sem_manifesto_nao_batiza_cache(self):
        p=self.raiz/'cache/asset';p.parent.mkdir();p.write_bytes(b'123')
        with self.assertRaises(ValueError):self.baixar()
    def test_extracao_nao_executa_e_reuso_confere(self):
        r=F.extrair_imagens(self.zip(),self.raiz/'imagens');self.assertEqual(len(r),1)
        self.assertFalse((self.raiz/'imagens/instalar.py').exists())
        Path(r[0]['caminho']).write_bytes(b'corrompido')
        with self.assertRaises(ValueError):F.extrair_imagens(self.raiz/'arquivo.zip',self.raiz/'imagens')
    def test_recusa_traversal_e_colisao_de_nomes(self):
        for nome in ('../Color.jpg','/Color.jpg','C:/Color.jpg','x\\Color.jpg'):
            with self.subTest(nome=nome),self.assertRaises(ValueError):F.extrair_imagens(self.zip(nome),self.raiz/'imagens')
        p=self.raiz/'duplo.zip'
        with zipfile.ZipFile(p,'w') as z:z.writestr('a.jpg',b'a');z.writestr('A.JPG',b'b')
        with self.assertRaises(ValueError):F.extrair_imagens(p,self.raiz/'imagens')
    def test_https_e_disco_configurado(self):
        with self.assertRaises(ValueError):F.baixar('http://example.test/arquivo',self.raiz/'x',max_bytes=4)
        with self.assertRaises(ValueError):F.extrair_imagens(self.zip(),self.raiz.parent/'fora-piloto')


if __name__=='__main__':unittest.main()
