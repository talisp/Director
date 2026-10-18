import tempfile
from pathlib import Path
import unittest
from director import diagnosticos as D


class Diagnosticos(unittest.TestCase):
    def test_agrupa_avisos_sem_confundir_evento_alheio_com_causa(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'Saved/Logs/Lab.log';p.parent.mkdir(parents=True);p.write_bytes(b'passado\n')
            marca=D.iniciar(tmp)
            p.write_bytes(p.read_bytes()+b'[hora1][  1]PIE: Warning: componente A\n[hora2][  2]PIE: Warning: componente A\nLogOutro: Error: evento simultaneo\n')
            d=D.concluir(marca,'apply','editor')
            self.assertEqual(d['grupos'][0]['contagem'],2)
            self.assertEqual(d['grupos'][0]['primeira'],'hora1')
            self.assertEqual(d['grupos'][0]['ultima'],'hora2')
            self.assertEqual(d['correlacao'],'apenas_temporal')
            self.assertEqual(D.resumo([d])['avisos_erros'],3)
            self.assertIn('evento simultaneo',d['grupos'][1]['mensagem_original'])

    def test_log_ausente_ou_rotacionado_nao_parece_limpo(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(D.concluir(D.iniciar(tmp),'measure')['coleta'],'log_indisponivel')
            p=Path(tmp)/'Saved/Logs/Lab.log';p.parent.mkdir(parents=True);p.write_bytes(b'antigo longo')
            marca=D.iniciar(tmp);p.write_bytes(b'')
            self.assertEqual(D.concluir(marca,'measure')['coleta'],'log_rotacionado')

    def test_limita_retorno_sem_apagar_referencia_ao_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'Saved/Logs/Lab.log';p.parent.mkdir(parents=True);p.write_bytes(b'')
            marca=D.iniciar(tmp)
            p.write_text(''.join(f'LogTest: Warning: aviso{i}\n' for i in range(12)))
            resumo=D.resumo([D.concluir(marca,'dev_exec')])
            self.assertEqual(len(resumo['grupos']),8)
            self.assertEqual(resumo['grupos_omitidos'],4)
            self.assertEqual(resumo['grupos'][0]['arquivo'],str(p))
