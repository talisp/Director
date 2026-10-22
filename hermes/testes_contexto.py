import importlib.util,json,unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location('director_contexto_teste',Path(__file__).parent/'plugins/director-contexto/__init__.py')
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class Contexto(unittest.TestCase):
    def test_conta_papeis_sem_gravar_segredos_conteudo_ou_imagem(self):
        m=M.Medidor();rows=[{'role':'system','content':'SEGREDO_NAO_GRAVAR'},{'role':'tool','content':'IMAGEM_BASE64'}]
        r=m.medir(request_messages=rows,session_id='a',request={'tools':[{'name':'terminal'}]},base_url='URL_SECRETA',api_key='CHAVE_SECRETA')
        text=json.dumps(r)
        for segredo in ('SEGREDO_NAO_GRAVAR','IMAGEM_BASE64','URL_SECRETA','CHAVE_SECRETA','terminal'):self.assertNotIn(segredo,text)
        self.assertEqual(set(r['bytes_por_papel']),{'system','tool'});self.assertEqual(r['prefixo_repetido_bytes'],0)
        r=m.medir(request_messages=rows+[{'role':'user','content':'novo'}],session_id='a')
        self.assertGreater(r['prefixo_repetido_bytes'],0)
        self.assertEqual(m.medir(request_messages=rows,session_id='outro')['prefixo_repetido_bytes'],0)

    def test_alteracao_no_inicio_nao_conta_como_prefixo_e_memoria_limitada(self):
        m=M.Medidor();m.medir(session_id='a',request_messages=[{'role':'user','content':'x'}])
        self.assertEqual(m.medir(session_id='a',request_messages=[{'role':'user','content':'y'}])['prefixo_repetido_bytes'],0)
        for n in range(200):m.medir(session_id=str(n),request_messages=[])
        self.assertLessEqual(len(m.anteriores),128)
