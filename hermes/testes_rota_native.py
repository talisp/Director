"""Smoke local do contrato Hermes instalado; sem modelo, editor ou SQL de usuario."""
import copy,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as N
root=Path.home()/'AppData/Local/hermes/hermes-agent'
sys.path.insert(0,str(root))
from gateway.config import Platform
from gateway.session import SessionSource
from gateway.session_local import LocalSessionAdapter
from gateway.session_policy import policy_for_source,build_policy
from hermes_state_runtime import RuntimeStoreError
from hermes_cli.gateway_chat import _requested_policy,validate_options
class Rota(unittest.TestCase):
 def test_rota_local_nao_cai_no_default_ao_perder_identidade(self):
  s=SessionSource(platform=Platform.LOCAL,chat_id='chat',user_id='teste',chat_type='dm')
  a=object.__new__(LocalSessionAdapter);a.sources={};a.policies={'chat':'politica-escolhida'}
  a.authority=N(sessions={'chat':N(source=s)});a.register_source(s)
  r=N(_adapter_for_source=lambda source:a)
  self.assertEqual(policy_for_source(r,s),'politica-escolhida')
  with self.assertRaisesRegex(RuntimeStoreError,'invalid_local_source'):policy_for_source(r,copy.copy(s))
  with self.assertRaisesRegex(RuntimeStoreError,'invalid_local_source'):policy_for_source(N(_adapter_for_source=lambda source:None),s)
  self.assertIsNone(policy_for_source(r,N(platform=Platform.TELEGRAM)))
 def test_canonicalizacao_preserva_politica_do_perfil_secundario(self):
  from unittest.mock import patch
  from gateway.authz_mixin import GatewayAuthorizationMixin
  from gateway.session_identity import canonical_identity
  class Runner(GatewayAuthorizationMixin):
   _adapter_for_source=GatewayAuthorizationMixin._delivery_adapter_for
  r=Runner();r.config=N(multiplex_profiles=True);r._primary_profile_name='default'
  s=SessionSource(platform=Platform.LOCAL,chat_id='chat-beta',user_id='teste',chat_type='dm',profile='beta')
  a=object.__new__(LocalSessionAdapter);a.sources={};a.policies={s.chat_id:'LUNA-ESCOLHIDA'}
  a.authority=N(sessions={s.chat_id:N(source=s)});a.register_source(s)
  prim=object.__new__(LocalSessionAdapter);prim.sources={};prim.policies={};prim.authority=N(sessions={})
  r.adapters={Platform.LOCAL:prim};r._profile_adapters={'beta':{Platform.LOCAL:a}}
  with tempfile.TemporaryDirectory() as tmp,patch('hermes_cli.profiles.get_profile_dir',return_value=Path(tmp)),patch.object(r,'_resolve_profile_home_for_source',return_value=Path(tmp),create=True):
   canonical_identity(s,runner=r,primary_home=Path(tmp))
   self.assertEqual(policy_for_source(r,s),'LUNA-ESCOLHIDA')
 def test_provider_novo_nao_herda_rota_e_modelo_do_anterior(self):
  from gateway.session_policy import _apply_launch_overrides
  old={'model':{'default':'modelo-local','provider':'host-local','base_url':'http://127.0.0.1:9/v1','api_key':'falso-nao-reutilizar','api_mode':'chat_completions','context_length':1000000}}
  c=copy.deepcopy(old)
  _apply_launch_overrides({'model':'modelo-novo','provider':'openai-codex'},c)
  self.assertEqual(c['model']['default'],'modelo-novo')
  for key in ['base_url','api_key','api_mode','context_length']:self.assertNotIn(key,c['model'])
  self.assertIn('base_url',old['model'])
  c=copy.deepcopy(old)
  _apply_launch_overrides({'provider':'custom','base_url':'http://127.0.0.1:8/v1'},c)
  self.assertEqual(c['model']['base_url'],'http://127.0.0.1:8/v1')
 def test_orcamento_cli_chega_na_politica_da_execucao(self):
  args=N(run_budget=45,model='modelo-ensaio',provider='custom',source='cli')
  validate_options(args);p=_requested_policy(args)
  self.assertEqual(p['run_budget'],45)
  with tempfile.TemporaryDirectory() as tmp:
   policy=build_policy(dict(p,cwd=tmp,toolsets=[]),{'platform_toolsets':{'cli':[]}},profile_terminal=False)
   self.assertEqual(policy.run_budget_seconds,45)
if __name__=='__main__':unittest.main()
