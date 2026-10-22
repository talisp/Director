"""Contagem local por hook nativo. Nunca registra texto, URLs, chaves ou imagens."""
import hashlib,json,logging,time,threading
from logging.handlers import RotatingFileHandler


class Medidor:
    def __init__(self):self.anteriores={};self.trava=threading.Lock()

    def medir(self,**kw):
        rows=kw.get('request_messages') or [];papeis={};atual=[]
        for m in rows:
            papel=m.get('role','outro') if isinstance(m,dict) else 'outro'
            if papel not in ('system','developer','user','assistant','tool'):papel='outro'
            raw=json.dumps(m,ensure_ascii=False,separators=(',',':')).encode('utf-8')
            tamanho=len(raw);papeis[papel]=papeis.get(papel,0)+tamanho
            atual.append((hashlib.sha256(raw).digest(),tamanho))
        sid=kw.get('session_id','');repetido=0
        with self.trava:
            anterior=self.anteriores.get(sid,[])
            for a,b in zip(anterior,atual):
                if a[0]!=b[0]:break
                repetido+=b[1]
            if len(self.anteriores)>=128 and sid not in self.anteriores:self.anteriores.pop(next(iter(self.anteriores)))
            self.anteriores[sid]=atual
        request=kw.get('request') or {};schema=request.get('tools',[]) if isinstance(request,dict) else []
        system=kw.get('system_prompt') or ''
        return {'quando':time.time(),'session_id':sid,'api_request_id':kw.get('api_request_id'),
            'chamada':kw.get('api_call_count'),'mensagens':len(rows),'bytes_por_papel':papeis,
            'schema_ferramentas_bytes':len(json.dumps(schema,ensure_ascii=False).encode()),
            'system_separado_bytes':len(json.dumps(system,ensure_ascii=False).encode()),
            'prefixo_repetido_bytes':repetido,'tokens_aproximados_hermes':kw.get('approx_input_tokens'),
            'ferramentas':kw.get('tool_count'),'limite':'bytes nao sao tokens; repeticao nao equivale a custo faturado; system pode estar tambem nas mensagens'}


def register(ctx):
    # Captura a pasta do perfil durante registro; nao depende de variavel global de outro perfil.
    pasta=ctx.state.data_dir;pasta.mkdir(parents=True,exist_ok=True)
    logger=logging.Logger('director-contexto-local');logger.propagate=False
    h=RotatingFileHandler(pasta/'medidas.jsonl',maxBytes=1024*1024,backupCount=1,encoding='utf-8')
    h.setFormatter(logging.Formatter('%(message)s'));logger.addHandler(h);medidor=Medidor()
    def antes(**kwargs):logger.info(json.dumps(medidor.medir(**kwargs),ensure_ascii=True))
    ctx.register_hook('pre_api_request',antes);ctx.on_unload(h.close)
