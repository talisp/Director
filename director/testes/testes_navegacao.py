import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from director import navegacao as N

class Navegacao(unittest.TestCase):
    def test_backup_persistido_mesmo_se_motor_falhar(self):
        class Ed:
            def chamar(self,n,**kw):
                if kw.get('acao'):raise RuntimeError('falha depois de iniciar ajuste')
                return {'level':'level','malhas':[{'resolucoes':[19,19,19]}]}
        with tempfile.TemporaryDirectory() as tmp,patch.object(N.C,'WORK',tmp):
            r=N.executar({'acao':'ajustar'},Ed())
            self.assertFalse(r['ok']);self.assertEqual(json.loads(Path(r['backup']).read_text())['malhas'][0]['resolucoes'],[19,19,19])
