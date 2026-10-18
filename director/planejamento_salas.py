"""Composicao de comodos no mesmo backend CP-SAT; gera fichas, nunca altera o editor."""
import json
import math
from pathlib import Path
import subprocess
import sys
from . import config as C
from .nucleo import planta as PL,operacoes as OP


def _cm(v):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('medidas numericas finitas')
    cm=v*100
    if abs(cm-round(cm))>.0001:raise ValueError('planejamento de salas usa resolucao de 1 cm; informe multiplos de 0,01 m')
    return round(cm)


def resolver(planta,pedido):
    from ortools.sat.python import cp_model
    import ortools
    escolhidas=pedido.get('salas')
    if not isinstance(escolhidas,list) or not escolhidas:raise ValueError('informe salas: [{id,largura_m,comprimento_m}]')
    atuais={i:o for i,o in planta['objetos'].items() if o['tipo']=='sala'}
    salas={i:{'w':_cm(o['largura']/100),'h':_cm(o['comprimento']/100),'x':_cm(o['x']/100),'y':_cm(o['y']/100),'altura':o['altura']/100} for i,o in atuais.items()}
    ids=[]
    for o in escolhidas:
        i=o['id'];PL.nova(i)
        if i in ids:raise ValueError('sala repetida: '+i)
        if i in planta['objetos'] and i not in atuais:raise ValueError('id pertence a outro objeto: '+i)
        ids.append(i);s=salas.setdefault(i,{})
        s.update(w=_cm(o['largura_m']),h=_cm(o['comprimento_m']),altura=o.get('altura_m',s.get('altura',2.7)))
        if min(s['w'],s['h'])<100:raise ValueError('dimensoes internas minimas de 1 m: '+i)
        for eixo in ('x','y'):
            if eixo+'_m' in o:
                pos=_cm(o[eixo+'_m'])
                if i in atuais and pos!=s[eixo]:raise ValueError('mover canto de sala existente nao faz parte deste planejador: '+i)
                s[eixo]=pos
    if len(salas)>32:raise ValueError('piloto limitado a 32 salas; nao e prova de escalabilidade para vilas')
    if not atuais:
        salas[ids[0]].setdefault('x',0);salas[ids[0]].setdefault('y',0)
    parede=15
    if any(abs(o['parede']-parede)>.01 for o in atuais.values()):raise ValueError('planejador requer paredes de 15 cm')
    alcance=sum(s['w']+s['h']+30 for s in salas.values())+max([abs(s.get(k,0)) for s in salas.values() for k in ('x','y')]+[0])
    if alcance>100000:raise ValueError('escopo excede dominio do piloto')
    model=cp_model.CpModel();xy={}
    for i,s in salas.items():
        x=model.new_int_var(-alcance,alcance,i+'_x');y=model.new_int_var(-alcance,alcance,i+'_y');xy[i]=(x,y)
        if 'x' in s:model.add(x==s['x'])
        if 'y' in s:model.add(y==s['y'])
    pares=list(salas)
    # Paredes paralelas: ou faixa compartilhada exata, ou duas paredes completas separadas.
    for n,a in enumerate(pares):
        xa,ya=xy[a];wa,ha=salas[a]['w'],salas[a]['h']
        for b in pares[n+1:]:
            xb,yb=xy[b];wb,hb=salas[b]['w'],salas[b]['h']
            alternativas=[]
            for horizontal,sinal in ((True,1),(True,-1),(False,1),(False,-1)):
                aa,bb,da=(xa,xb,wa) if horizontal else (ya,yb,ha)
                if sinal<0:aa,bb,da=(xb,xa,wb) if horizontal else (yb,ya,hb)
                separado=model.new_bool_var('separado');junto=model.new_bool_var('junto');alternativas += [separado,junto]
                model.add(bb>=aa+da+2*parede).only_enforce_if(separado)
                model.add(bb==aa+da+parede).only_enforce_if(junto)
                if horizontal:
                    model.add(ya+ha>=yb).only_enforce_if(junto);model.add(yb+hb>=ya).only_enforce_if(junto)
                else:
                    model.add(xa+wa>=xb).only_enforce_if(junto);model.add(xb+wb>=xa).only_enforce_if(junto)
            model.add_bool_or(alternativas)
    nomes_assumidos={}
    for adj in pedido.get('adjacencias',[]):
        par=adj['salas'] if isinstance(adj,dict) else adj
        if not isinstance(par,list) or len(par)!=2 or par[0]==par[1] or any(i not in salas for i in par):raise ValueError('adjacencia requer duas salas existentes no pedido/planta')
        a,b=par;xa,ya=xy[a];xb,yb=xy[b];wa,ha=salas[a]['w'],salas[a]['h'];wb,hb=salas[b]['w'],salas[b]['h']
        minimo=adj.get('contato_minimo_cm',120) if isinstance(adj,dict) else 120
        if isinstance(minimo,bool) or not isinstance(minimo,int) or minimo<=0:raise ValueError('contato_minimo_cm inteiro positivo')
        lado=adj.get('lado') if isinstance(adj,dict) else None
        if lado is not None and lado not in OP.LADOS:raise ValueError('lado de adjacencia invalido')
        assumido=model.new_bool_var(a+'--'+b);model.add_assumption(assumido);nomes_assumidos[assumido.index]=par
        direcoes=[]
        for l in ([lado] if lado else OP.LADOS):
            d=model.new_bool_var(l);direcoes.append(d);cond=[assumido,d]
            if l in ('leste','oeste'):
                model.add(xb==xa+wa+parede if l=='leste' else xa==xb+wb+parede).only_enforce_if(cond)
                model.add(ya+ha>=yb+minimo).only_enforce_if(cond);model.add(yb+hb>=ya+minimo).only_enforce_if(cond)
            else:
                model.add(yb==ya+ha+parede if l=='norte' else ya==yb+hb+parede).only_enforce_if(cond)
                model.add(xa+wa>=xb+minimo).only_enforce_if(cond);model.add(xb+wb>=xa+minimo).only_enforce_if(cond)
        model.add_bool_or(direcoes).only_enforce_if(assumido)
    minx=model.new_int_var(-alcance,alcance,'minx');miny=model.new_int_var(-alcance,alcance,'miny')
    maxx=model.new_int_var(-alcance,2*alcance,'maxx');maxy=model.new_int_var(-alcance,2*alcance,'maxy')
    model.add_min_equality(minx,[p[0] for p in xy.values()]);model.add_min_equality(miny,[p[1] for p in xy.values()])
    model.add_max_equality(maxx,[xy[i][0]+s['w'] for i,s in salas.items()]);model.add_max_equality(maxy,[xy[i][1]+s['h'] for i,s in salas.items()])
    W=model.new_int_var(1,3*alcance,'W');H=model.new_int_var(1,3*alcance,'H');model.add(W==maxx-minx);model.add(H==maxy-miny)
    area=model.new_int_var(1,9*alcance*alcance,'area');model.add_multiplication_equality(area,[W,H]);model.minimize(area)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=min(10,max(.1,float(pedido.get('segundos',3))))
    solver.parameters.num_search_workers=1;solver.parameters.random_seed=0
    status=solver.solve(model)
    base={'aplicado':False,'backend':'OR-Tools '+ortools.__version__,'status':solver.status_name(status),'resolucao_cm':1}
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        core=solver.sufficient_assumptions_for_infeasibility() if status==cp_model.INFEASIBLE else []
        return {'ok':False,**base,'motivo':'restricoes_incompativeis' if status==cp_model.INFEASIBLE else 'prazo_sem_solucao',
                'adjacencias_em_conflito':[nomes_assumidos[i] for i in core if i in nomes_assumidos],
                'detalhe':'conflito conjunto entre adjacencias/dimensoes/posicoes fixas; nao significa que cada par seja impossivel isoladamente' if core else 'confira dimensoes/posicoes fixas e o prazo; nenhuma ficha aplicada'}
    operacoes=[];posicoes={}
    for i,s in salas.items():
        posicoes[i]={'x_m':solver.value(xy[i][0])/100,'y_m':solver.value(xy[i][1])/100,'largura_m':s['w']/100,'comprimento_m':s['h']/100,'altura_m':s['altura']}
        if i not in atuais:operacoes.append({'operacao':'criar_sala','id':i,**posicoes[i]})
        elif i in ids and (any(abs(atuais[i][k]-s[v])>.01 for k,v in (('largura','w'),('comprimento','h'))) or abs(atuais[i]['altura']-s['altura']*100)>.01):
            operacoes.append({'operacao':'mudar_sala','id':i,'largura_m':s['w']/100,'comprimento_m':s['h']/100,'altura_m':s['altura']})
    ficha={'pedido':pedido.get('pedido'),'revisao_base':planta['revisao'],'operacoes':operacoes}
    try:proposta=OP.aplicar_ficha(planta,ficha)[0] if operacoes else planta
    except OP.Invalida as exc:return {'ok':False,**base,'motivo':'validacao_geometrica','detalhe':str(exc),'salas':posicoes}
    from .planejamento import compartilhadas
    return {'ok':True,**base,'salas':posicoes,'ficha_salas':ficha,'paredes_compartilhadas_planejadas':compartilhadas(proposta),
            'mantidas':sorted(atuais),'area_caixa_m2':solver.value(area)/10000,'otimalidade_comprovada':status==cp_model.OPTIMAL,
            'sem_alteracoes':not operacoes,'avisos':OP.avisos(proposta),
            'limites':['comodos retangulares, 15 cm de parede, ate 32 salas; nao e plano territorial de vila',
                       'adjacencia nao cria porta/passagem automaticamente; escolha a abertura depois',
                       'cantos existentes ficam fixos; alteracao de tamanho ainda precisa caber nos objetos existentes']}


def planejar(cena,pedido):
    planta=PL.carregar(C.CENAS,cena)
    try:return resolver(planta,pedido)
    except ImportError:
        exe=Path(C.RAIZ)/'.venv-planejamento'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
        if not exe.is_file():return {'ok':False,'motivo':'ambiente_planejamento_ausente','aplicado':False}
        proc=subprocess.run([str(exe),'-m','director.planejamento_salas'],input=json.dumps({'planta':planta,'pedido':pedido}).encode(),capture_output=True,cwd=C.RAIZ,timeout=20)
        if proc.returncode:raise RuntimeError(proc.stderr.decode(errors='replace')[-1200:])
        return json.loads(proc.stdout)


if __name__=='__main__':
    dados=json.loads(sys.stdin.buffer.read());print(json.dumps(resolver(dados['planta'],dados['pedido']),ensure_ascii=True))
