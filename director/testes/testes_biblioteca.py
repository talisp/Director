import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from director import biblioteca as B

class Biblioteca(unittest.TestCase):
    def test_falha_nao_apaga_indice_existente(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'biblioteca';p.mkdir()
            arq=p/'indice.json';arq.write_text(json.dumps({'itens':[{'caminho':'anterior','bytes':0}]}))
            with patch.object(B.C,'BIBLIOTECA',str(p)):
                r=B.indexar({'fontes':[{'arquivos':[str(p/'ausente.glb')]}]})
            self.assertFalse(r['ok']);self.assertEqual(json.loads(arq.read_text())['itens'][0]['caminho'],'anterior')
