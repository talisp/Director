import copy,json,tempfile,unittest,os
from pathlib import Path
from verificar_ficha import check
from teste_skill import run,cartao,BOAS,EXPERIMENTOS_OK


def exemplo():
    d=json.loads((Path(__file__).resolve().parent.parent/'templates/FICHA_OPERADOR.json').read_text(encoding='utf-8'))
    def preencher(v):
        if isinstance(v,dict):return {k:preencher(x) for k,x in v.items()}
        if isinstance(v,list):return [preencher(x) for x in v]
        return 'evidencia concreta desta fixture' if isinstance(v,str) and '<' in v else v
    d=preencher(d)
    d.update(repo='https://github.com/ExampleOwner/Test-Repo',commit_director='a'*40,commit_fonte='b'*40)
    d['licenca']['id']='MIT'
    return d


class Ficha(unittest.TestCase):
    def test_proposta_nao_e_promocao_nem_autorizacao(self):
        d=exemplo();self.assertEqual(check(d),[])
        for campo,valor in [('integracao_autorizada',True),('commit_fonte','curto'),('estado','integrado')]:
            e=copy.deepcopy(d);e[campo]=valor;self.assertTrue(check(e),campo)
        d['estado']='verificado_no_ensaio';self.assertTrue(check(d))
        d['variacao']={'executada':True,'evidencia':'EXP2'};d['evidencias'][0]['tipo']='TESTE_ISOLADO'
        self.assertEqual(check(d),[])
        d['orcamento']['consumido']['chamadas']=21;self.assertTrue(check(d))
        d['orcamento']['limites']=[];self.assertTrue(check(d))
        self.assertTrue(check([]))

    def test_orcamento_pausa_e_retoma_sem_perder_fila(self):
        with tempfile.TemporaryDirectory(prefix='director-lote-teste-') as tmp:
            root=Path(tmp)/'pesquisa';url='https://github.com/ExampleOwner/Test-Repo'
            env={**os.environ,'DIRECTOR_RESEARCH_PROTEGIDOS':str(Path(tmp)/'protegido')}
            run(root,'add',url,'https://github.com/ExampleOwner/Segundo',env=env)
            run(root,'begin',url,env=env)
            run(root,'partial',url,'orcamento','teto de tokens autorizado atingido; feito: leitura | falta: teste | arquivos: analise.md',env=env)
            data=json.loads((root/'fila.json').read_text(encoding='utf-8'))
            self.assertEqual([i['estado'] for i in data['items']],['PARCIAL','PENDENTE'])
            self.assertIn(url,run(root,'next',env=env).stdout)
            run(root,'begin',url,env=env)
            self.assertIn('PARCIAL: orcamento',run(root,'begin',url,env=env).stdout)

    def test_finish_exige_ficha_e_vinculo_consistente(self):
        with tempfile.TemporaryDirectory(prefix='director-ficha-teste-') as tmp:
            root=Path(tmp)/'pesquisa';url='https://github.com/ExampleOwner/Test-Repo'
            env={**os.environ,'DIRECTOR_RESEARCH_PROTEGIDOS':str(Path(tmp)/'protegido')}
            run(root,'add',url,env=env);d=exemplo();v=Path(tmp)/'gargalo.json';v.write_text(json.dumps(d),encoding='utf-8')
            run(root,'gargalo',url,str(v),env=env);run(root,'begin',url,env=env)
            repo=root/'repositorios/exampleowner--test-repo';repo.mkdir(parents=True,exist_ok=True)
            (repo/'AVALIACAO.md').write_text(cartao('ExampleOwner/Test-Repo',BOAS),encoding='utf-8')
            for name in ('analise.md','evidencias.md','estado.md'):(repo/name).write_text('fixture de teste',encoding='utf-8')
            (repo/'experimentos.md').write_text(EXPERIMENTOS_OK,encoding='utf-8')
            run(root,'finish',url,ok=False,env=env)
            d['pedido']='outro pedido';(repo/'FICHA_OPERADOR.json').write_text(json.dumps(d),encoding='utf-8')
            run(root,'finish',url,ok=False,env=env)
            d['pedido']=exemplo()['pedido'];(repo/'FICHA_OPERADOR.json').write_text(json.dumps(d),encoding='utf-8')
            run(root,'finish',url,env=env)
            self.assertEqual(json.loads((root/'fila.json').read_text(encoding='utf-8'))['items'][0]['estado'],'CONCLUIDO')


if __name__=='__main__':unittest.main()
