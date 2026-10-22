"""Valida reaplicacao real do patch em copia descartavel, sem tocar o Hermes instalado."""
import json, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from hermes import manutencao_rota as M


class Manutencao(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / 'copia'
        self.repo.mkdir()
        self.manifesto = json.loads((M.PASTA / 'rota-native.json').read_text())
        fonte = Path.home() / 'AppData/Local/hermes/hermes-agent'
        for rel in self.manifesto['arquivos']:
            raw = subprocess.run(['git', '-C', str(fonte), 'show', self.manifesto['base'] + ':' + rel], capture_output=True, check=True).stdout
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        original = M._git
        def git(repo, *args, **kwargs):
            if args == ('rev-parse', 'HEAD'):
                return subprocess.CompletedProcess(args, 0, self.manifesto['base'] + '\n', '')
            return original(repo, *args, **kwargs)
        self.addCleanup(patch.stopall)
        patch.object(M, '_git', side_effect=git).start()
        patch.object(M, 'BACKUPS', Path(self.tmp.name) / 'backups').start()

    def test_aplica_backup_e_repeticao_sem_nova_escrita(self):
        self.assertEqual(M.conferir(self.repo)['estado'], 'aplicavel')
        r = M.conferir(self.repo, aplicar=True)
        self.assertEqual(r['estado'], 'ja_corrigido')
        for rel in self.manifesto['arquivos']:
            self.assertTrue((Path(r['backup']) / rel).is_file())
        self.assertNotIn('backup', M.conferir(self.repo, aplicar=True))

    def test_recusa_mudanca_local_e_preserva_bytes(self):
        p = self.repo / next(iter(self.manifesto['arquivos']))
        p.write_bytes(p.read_bytes() + b'\n# alteracao independente\n')
        antes = p.read_bytes()
        with self.assertRaisesRegex(ValueError, 'mudanca local'):
            M.conferir(self.repo, aplicar=True)
        self.assertEqual(p.read_bytes(), antes)
        self.assertFalse(M.BACKUPS.exists())

    def test_recusa_base_desconhecida_sem_backup(self):
        with patch.object(M, '_git', return_value=subprocess.CompletedProcess([], 0, 'outra-versao\n', '')):
            with self.assertRaisesRegex(ValueError, 'versao Hermes diferente'):
                M.conferir(self.repo, aplicar=True)
        self.assertFalse(M.BACKUPS.exists())

    def test_patch_crlf_do_checkout_windows(self):
        pasta = Path(self.tmp.name) / 'patch-windows'
        pasta.mkdir()
        (pasta / 'rota-native.json').write_text(json.dumps(self.manifesto))
        texto = (M.PASTA / 'rota-native.patch').read_text(encoding='utf-8')
        (pasta / 'rota-native.patch').write_bytes(texto.replace('\n', '\r\n').encode('utf-8'))
        with patch.object(M, 'PASTA', pasta):
            self.assertEqual(M.conferir(self.repo, aplicar=True)['estado'], 'ja_corrigido')


if __name__ == '__main__':
    unittest.main()
