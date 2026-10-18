import json,tempfile,unittest,importlib.util,copy,ast,types
from pathlib import Path
from unittest.mock import patch
from director import navegacao as N

class Navegacao(unittest.TestCase):
    def test_backup_persistido_mesmo_se_motor_falhar(self):
        class Ed:
            def chamar(self,n,**kw):
                if n=='measure':return {'medidas':[{'pronta':True}]}
                if kw.get('acao'):raise RuntimeError('falha depois de iniciar ajuste')
                return {'level':'level','malhas':[{'resolucoes':[19,19,19]}]}
        with tempfile.TemporaryDirectory() as tmp,patch.object(N.C,'WORK',tmp):
            r=N.executar({'acao':'ajustar'},Ed())
            self.assertFalse(r['ok']);self.assertEqual(json.loads(Path(r['backup']).read_text())['malhas'][0]['resolucoes'],[19,19,19])

    def test_reconstruir_espera_carga_e_nao_aprova_rota(self):
        class Ed:
            def __init__(self):self.estados=iter([False,True,True,True,True]);self.acoes=[]
            def chamar(self,n,**kw):
                if n=='measure':return {'medidas':[{'pronta':next(self.estados)}]}
                if kw.get('acao'):
                    self.acoes.append(kw)
                    return {'backup':{'level':'level','malhas':[]},'rebuild_solicitado':True}
                return {'level':'level','malhas':[]}
        with tempfile.TemporaryDirectory() as tmp,patch.object(N.C,'WORK',tmp),patch.object(N.time,'sleep'):
            ed=Ed();r=N.executar({'acao':'reconstruir'},ed)
            self.assertTrue(r['pronta']);self.assertFalse(r['conectividade_verificada'])
            self.assertEqual(ed.acoes[0]['acao'],'reconstruir')

    def test_carga_nao_liberada_nao_altera_motor(self):
        class Ed:
            def chamar(self,n,**kw):
                if n=='measure':return {'medidas':[{'pronta':False}]}
                if kw.get('acao'):raise AssertionError('nao deveria alterar')
                return {'level':'level','malhas':[]}
        with patch.object(N.time,'monotonic',side_effect=range(100)),patch.object(N.time,'sleep'):
            r=N.executar({'acao':'reconstruir','prazo_s':3},Ed())
            self.assertFalse(r['ok']);self.assertTrue(r['nenhuma_alteracao'])

    def test_prazo_invalido_recusado_antes_da_ponte(self):
        for t in (0,-1,61,float('nan'),float('inf')):
            with self.assertRaises(ValueError):N.executar({'acao':'reconstruir','prazo_s':t},None)


_arquivo=Path(__file__).parents[1]/'editor/director_tools/nav_parametros.py'
_spec=importlib.util.spec_from_file_location('nav_parametros_teste',_arquivo)
NP=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(NP)


class Parametros(unittest.TestCase):
    def setUp(self):
        self.perfis=[{'cell_size':c,'cell_height':10,'agent_max_step_height':35} for c in (38,19,19)]

    def test_refino_incompativel_recusado_sem_alterar_entrada(self):
        antes=copy.deepcopy(self.perfis)
        with self.assertRaisesRegex(ValueError,'tile_cm=950'):
            NP.preparar(self.perfis,1000,'regiao',5,2)
        self.assertEqual(self.perfis,antes)

    def test_alinhamento_explicito_preserva_default_e_raio(self):
        r=NP.preparar(self.perfis,1000,'regiao',5,2,950)
        self.assertEqual(r['resolucoes'][:2],self.perfis[:2])
        self.assertEqual(r['resolucoes'][2]['cell_size'],5)
        self.assertEqual(r['tiles_efetivos_cm'],[950]*3)
        self.assertTrue(r['tile_alterado'])

    def test_tamanhos_fracionarios_e_level_uniforme(self):
        r=NP.preparar(self.perfis,988,'regiao',4.75,2)
        self.assertEqual(r['tiles_efetivos_cm'],[988]*3)
        self.assertFalse(r['tile_alterado'])
        r=NP.preparar(self.perfis,1000,'level',5,2)
        self.assertEqual(r['tiles_efetivos_cm'],[1000]*3)

    def test_precisao_float_dos_perfis_normalizados_pelo_motor(self):
        self.perfis[0]['cell_size']=38.46154022216797
        self.perfis[1]['cell_size']=18.867923736572266
        r=NP.preparar(self.perfis,1000,'regiao',5,2)
        self.assertLess(max(r['tiles_efetivos_cm'])-min(r['tiles_efetivos_cm']),.001)

    def test_valores_invalidos_e_perfis_incompletos(self):
        for c in (0,-1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):NP.preparar(self.perfis,1000,'regiao',c,2)
        with self.assertRaises(ValueError):NP.preparar(self.perfis[:1],1000,'regiao',5,2)


class OperacaoNativa(unittest.TestCase):
    """Compila a funcao real sem Unreal e simula o callback nativo de TileSizeUU."""
    def setUp(self):
        class Param(dict):
            def get_editor_property(self,k):return self[k]
            def set_editor_property(self,k,v):self[k]=v
            def copy(self):return Param(self)
        class Nav:
            def __init__(self):
                self.props={'agent_radius':35.,'tile_size_uu':950.,'nav_mesh_resolution_params':[
                    Param(cell_size=c,cell_height=10.,agent_max_step_height=35.) for c in (38.,19.,5.)]}
                self.mudancas=[]
            def get_path_name(self):return 'nav'
            def get_editor_property(self,k):return self.props[k]
            def set_editor_property(self,k,v):
                self.mudancas.append(k);self.props[k]=v
                if k=='tile_size_uu':
                    for p in self.props['nav_mesh_resolution_params']:
                        p['cell_size']=v/round(v/p['cell_size'])
        self.nav=Nav();self.comandos=[]
        U=types.SimpleNamespace(RecastNavMesh=Nav,NavMeshBoundsVolume=type('Bounds',(),{}),
            NavigationSystemV1=types.SimpleNamespace(is_navigation_being_built_or_locked=lambda w:False,
                get_navigation_system=lambda w:None),
            SystemLibrary=types.SimpleNamespace(execute_console_command=lambda w,c:self.comandos.append(c)))
        env={'U':U,'NP':NP,'math':__import__('math'),'_eas':lambda:types.SimpleNamespace(get_all_level_actors=lambda:[self.nav]),
             '_mundo_jogo':lambda:None,'_mundo_editor':lambda:None,'info':lambda:{'level':'level'}}
        tree=ast.parse(_arquivo.with_name('ops.py').read_text(encoding='utf-8'))
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_nav_dados','nav_config')]
        for n in nodes:n.decorator_list=[]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'ops.py','exec'),env)
        self.executar=env['nav_config']

    def test_restaurar_tile_antes_dos_perfis_evitar_normalizacao_oculta(self):
        backup={'level':'level','criados':[],'malhas':[{'ator':'nav','raio_cm':35.,'tile_cm':1000.,
            'resolucoes':[dict(cell_size=c,cell_height=10.,agent_max_step_height=35.) for c in (38.,19.,19.)]}]}
        r=self.executar(acao='restaurar',backup=backup)
        self.assertEqual(r['atual'][0],backup['malhas'][0])
        self.assertEqual(self.nav.mudancas[0],'tile_size_uu')

    def test_recusa_de_perfis_antes_da_primeira_mutacao(self):
        self.nav.props['tile_size_uu']=1000.
        self.nav.props['nav_mesh_resolution_params'][2]['cell_size']=19.
        with self.assertRaisesRegex(ValueError,'desalinhados'):
            self.executar(acao='ajustar',regiao=[[0,0,0],[100,100,100]])
        self.assertEqual(self.nav.mudancas,[]);self.assertEqual(self.comandos,[])

    def test_reconstruir_nao_muda_parametros(self):
        r=self.executar(acao='reconstruir')
        self.assertTrue(r['rebuild_solicitado']);self.assertEqual(self.nav.mudancas,[])
        self.assertEqual(self.comandos,['RebuildNavigation'])
