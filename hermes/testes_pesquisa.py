import importlib.util,tempfile,sqlite3,json,unittest,hashlib
from pathlib import Path
from unittest.mock import patch
from contextlib import closing

s=importlib.util.spec_from_file_location('instalar_pesquisa_teste',Path(__file__).parent/'instalar_pesquisa.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class InstalacaoPesquisa(unittest.TestCase):
    def preparar(self,tmp):
        raiz=Path(tmp);src=raiz/'fonte';src.mkdir();(src/'SKILL.md').write_text('nova',encoding='utf-8')
        (src/'BASELINE-0.2.1.json').write_text(json.dumps({'SKILL.md':hashlib.sha256(b'antiga').hexdigest()}),encoding='utf-8')
        p=raiz/'perfil';(p/'skills/director-research').mkdir(parents=True);(p/'skills/director-research/SKILL.md').write_text('antiga',encoding='utf-8')
        with closing(sqlite3.connect(p/'state.db')) as c:
            c.execute('create table session_admissions(status text)');c.execute('create table session_turn_leases(expires_at real)')
        return src,p

    def test_backup_extras_preservados_e_conferencia_sem_instalar(self):
        with tempfile.TemporaryDirectory() as tmp:
            src,p=self.preparar(tmp);note=p/'skills/director-research/nota-local.md';note.write_text('aprendizado local',encoding='utf-8')
            with patch.object(M,'FONTE',src):
                self.assertFalse(M.conferir(p)['igual']);self.assertEqual((p/'skills/director-research/SKILL.md').read_text(),'antiga')
                r=M.aplicar(p);self.assertTrue(r['igual']);self.assertEqual(note.read_text(),'aprendizado local')
                self.assertEqual((Path(r['backup'])/'SKILL.md').read_text(),'antiga')
                self.assertFalse(M.aplicar(p)['instalado'])

    def test_recusa_conflito_e_perfil_ativo(self):
        with tempfile.TemporaryDirectory() as tmp:
            src,p=self.preparar(tmp)
            with patch.object(M,'FONTE',src):
                f=p/'skills/director-research/SKILL.md';f.write_text('editada por outro agente',encoding='utf-8')
                with self.assertRaisesRegex(ValueError,'baseline'):M.aplicar(p)
                f.write_text('antiga',encoding='utf-8')
                with closing(sqlite3.connect(p/'state.db')) as c:
                    c.execute("insert into session_admissions values ('started')");c.commit()
                with self.assertRaisesRegex(ValueError,'ocupado'):M.aplicar(p)
                self.assertEqual(f.read_text(),'antiga')
