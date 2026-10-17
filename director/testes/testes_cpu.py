import ast,unittest,types
from pathlib import Path

class CpuPlay(unittest.TestCase):
    def funcao(self,cfg):
        src=Path('director/editor/director_tools/ops.py').read_text(encoding='utf-8')
        f=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='_freio_de_fundo')
        st=types.SimpleNamespace();env={'U':types.SimpleNamespace(load_object=lambda *a:cfg),'_estado':lambda:st}
        exec(compile(ast.Module(body=[f],type_ignores=[]),'<controle_cpu>','exec'),env)
        return env['_freio_de_fundo']
    def test_restaura_true_e_false_e_indica_falha(self):
        class Cfg:
            def __init__(self,v):self.v=v
            def get_editor_property(self,p):
                if self.v is None:raise ValueError('indisponivel')
                return self.v
            def set_editor_property(self,p,v):self.v=v
        for old in (True,False):
            cfg=Cfg(old);f=self.funcao(cfg)
            self.assertTrue(f(True)['aplicado']);self.assertFalse(cfg.v)
            self.assertTrue(f(False)['restaurado']);self.assertEqual(cfg.v,old)
        self.assertFalse(self.funcao(Cfg(None))(True)['aplicado'])
