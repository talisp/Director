import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from hermes.instalar_perfil import pasta_do_perfil


class CaminhosPerfil(unittest.TestCase):
    def test_home_global(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'HERMES_HOME':tmp}):
            self.assertEqual(Path(pasta_do_perfil('director')),Path(tmp)/'profiles/director')

    def test_home_ja_e_o_perfil_da_conversa(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)/'profiles/director'
            with patch.dict(os.environ,{'HERMES_HOME':str(home)}):
                self.assertEqual(Path(pasta_do_perfil('director')),home)

    def test_home_de_outro_perfil_resolve_irmao(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ,{'HERMES_HOME':str(Path(tmp)/'profiles/hermes-dev')}):
                self.assertEqual(Path(pasta_do_perfil('director')),Path(tmp)/'profiles/director')

    def test_sem_override_usa_localappdata(self):
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,{'LOCALAPPDATA':tmp}):
            os.environ.pop('HERMES_HOME',None)
            self.assertEqual(Path(pasta_do_perfil('director')),Path(tmp)/'hermes/profiles/director')
