"""Valida ficha dirigida; forma/procedencia nao provam que algoritmo funciona."""
import json,math,re,sys
from pathlib import Path


def check(data):
    errs=[]
    if not isinstance(data,dict):return ['ficha deve ser objeto JSON']
    def texto(obj,k):
        if not isinstance(obj.get(k),str) or not obj[k].strip() or re.search(r'<[^>\n]+>',obj[k]):errs.append('texto obrigatorio, sem placeholder: '+k)
    if data.get('schema')!=1:errs.append('schema deve ser 1')
    for k in ('problema','issue','pedido','capacidade_existente','acrescimo','hipotese','limites','recuperacao','dependencias','teste_aceitacao'):
        texto(data,k)
    for k in ('commit_director','commit_fonte'):
        if not re.fullmatch('[0-9a-f]{40}',str(data.get(k,''))):errs.append('commit completo obrigatorio: '+k)
    if not re.fullmatch(r'https://github\.com/[\w.-]+/[\w.-]+',str(data.get('repo',''))):errs.append('repo deve ser URL GitHub canonica')
    lic=data.get('licenca',{})
    if not isinstance(lic,dict):lic={}
    for k in ('id','fonte','conferida_em'):texto(lic,k)
    if data.get('classe') not in ('codigo','algoritmo','inspiracao','pronto'):errs.append('classe invalida')
    if data.get('integracao_autorizada') is not False:errs.append('ficha de pesquisa nao autoriza integracao')
    if data.get('estado') not in ('proposta','verificado_no_ensaio'):errs.append('estado invalido')
    fontes=data.get('arquivos_funcoes')
    if not isinstance(fontes,list) or not fontes or not all(isinstance(v,str) and v.strip() for v in fontes):errs.append('arquivos_funcoes obrigatorios')
    ev=data.get('evidencias')
    if not isinstance(ev,list) or not ev:errs.append('evidencias obrigatorias');ev=[]
    for e in ev:
        if not isinstance(e,dict):errs.append('evidencia deve ser objeto');continue
        if e.get('tipo') not in ('ALEGADO','CODIGO','TESTE_ISOLADO','UNREAL','NAO_VERIFICADO'):errs.append('tipo de evidencia invalido')
        texto(e,'referencia');texto(e,'observado')
    if data.get('estado')=='verificado_no_ensaio':
        v=data.get('variacao',{})
        if not isinstance(v,dict) or v.get('executada') is not True or not v.get('evidencia'):errs.append('promocao exige variacao executada com evidencia')
        if not any(isinstance(e,dict) and e.get('tipo') in ('TESTE_ISOLADO','UNREAL') for e in ev):errs.append('codigo/alegacao nao equivalem a teste')
        if lic.get('id') in ('NAO_VERIFICADA','?',''):errs.append('licenca nao verificada impede promocao')
    budget=data.get('orcamento',{})
    if not isinstance(budget,dict):budget={}
    limites=budget.get('limites',{});consumido=budget.get('consumido',{})
    if not isinstance(limites,dict):limites={}
    if not isinstance(consumido,dict):consumido={}
    for k in ('repos','chamadas','dados_bytes'):
        limite=limites.get(k);usado=consumido.get(k)
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 for v in (limite,usado)):
            errs.append('orcamento numerico e finito: '+k)
        elif usado>limite:errs.append('orcamento excedido: '+k+'; registrar decisao antes de continuar')
    op=data.get('operador',{})
    if not isinstance(op,dict):op={}
    for k in ('pre_condicoes','procedimento','esperado','quando_pedir_ajuda'):texto(op,k)
    return errs


def main():
    try:errs=check(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig')))
    except (OSError,ValueError,IndexError) as e:errs=[type(e).__name__+': falha ao ler ficha']
    print(json.dumps({'valida':not errs,'erros':errs,'limite':'validador de forma, nao auditoria independente de funcionamento'},ensure_ascii=True))
    return 1 if errs else 0


if __name__=='__main__':raise SystemExit(main())
