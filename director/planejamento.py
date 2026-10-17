"""Propostas espaciais por CP-SAT existente; nao altera a cena."""
import json
import math
from pathlib import Path
import subprocess
import sys
from . import config as C,relatorio
from .nucleo import planta as PL,operacoes as OP


def resolver(pedido):
    from ortools.sat.python import cp_model
    import ortools
    minimo=pedido.get('minimo_cm',pedido.get('dimensoes_cm'))
    maximo=pedido.get('maximo_cm',pedido.get('dimensoes_cm'))
    if not minimo or not maximo or len(minimo)!=2 or len(maximo)!=2:raise ValueError('informe dimensoes_cm ou minimo_cm/maximo_cm')
    if any(not math.isfinite(v) or v<=0 for v in minimo+maximo) or any(a>b for a,b in zip(minimo,maximo)):raise ValueError('dimensoes positivas e limites coerentes')
    if not pedido.get('objetos'):raise ValueError('informe objetos com dimensoes_cm')
    model=cp_model.CpModel()
    reservas=[]
    for b in pedido.get('reservas',[]):
        if len(b)!=4 or not all(math.isfinite(v) for v in b):raise ValueError('reserva precisa de quatro numeros finitos')
        x0,y0=math.floor(b[0]),math.floor(b[1])
        reservas.append([x0,y0,math.ceil(b[0]+b[2])-x0,math.ceil(b[1]+b[3])-y0])
    W=model.new_int_var(math.ceil(minimo[0]),math.floor(maximo[0]),'largura')
    H=model.new_int_var(math.ceil(minimo[1]),math.floor(maximo[1]),'comprimento')
    area=model.new_int_var(1,math.ceil(maximo[0]*maximo[1]),'area');model.add_multiplication_equality(area,[W,H]);model.minimize(area)
    dados=[];xis=[];yis=[];folga=int(pedido.get('folga_cm',5))
    for o in pedido['objetos']:
        w,d=map(lambda v:math.ceil(v),o['dimensoes_cm'][:2]);uso=math.ceil(o.get('uso_frente_cm',70))
        if min(w,d)<=0 or uso<0:raise ValueError('objeto precisa de dimensoes positivas e uso nao negativo')
        rot=model.new_bool_var(o['id']+'_rot')
        if o.get('girar',True) is False:model.add(rot==0)
        rw=model.new_int_var(min(w,d),max(w,d),o['id']+'_w');rh=model.new_int_var(min(w,d),max(w,d),o['id']+'_h')
        model.add(rw==w+(d-w)*rot);model.add(rh==d+(w-d)*rot)
        x=model.new_int_var(folga,math.floor(maximo[0]),o['id']+'_x');y=model.new_int_var(folga,math.floor(maximo[1]),o['id']+'_y')
        model.add(x+rw<=W-folga);model.add(y+rh<=H-folga)
        model.add(y>=uso+folga).only_enforce_if(rot.Not());model.add(x+rw+uso<=W-folga).only_enforce_if(rot)
        xe=model.new_int_var(0,math.floor(maximo[0]),o['id']+'_xe');ye=model.new_int_var(0,math.floor(maximo[1]),o['id']+'_ye')
        model.add(xe==x+rw);model.add(ye==y+rh)
        xis.append(model.new_interval_var(x,rw,xe,o['id']+'_ix'))
        yis.append(model.new_interval_var(y,rh,ye,o['id']+'_iy'))
        dados.append((o,x,y,rw,rh,rot,uso))
    model.add_no_overlap_2d(xis,yis)
    def separar(a,b,cond=None):
        bits=[model.new_bool_var('separa') for _ in range(4)]
        exprs=[a[0]+a[2]<=b[0],b[0]+b[2]<=a[0],a[1]+a[3]<=b[1],b[1]+b[3]<=a[1]]
        for bit,expr in zip(bits,exprs):model.add(expr).only_enforce_if([bit]+([cond] if cond is not None else []))
        c=model.add_bool_or(bits)
        if cond is not None:c.only_enforce_if(cond)
    for i,(obj,x,y,w,h,r,u) in enumerate(dados):
        for j,(_,xx,yy,ww,hh,rr,uu) in enumerate(dados):
            if i==j:continue
            separar((x,y-u,w,h+u),(xx,yy,ww,hh),r.Not())
            separar((x,y,w+u,h),(xx,yy,ww,hh),r)
        for b in reservas:separar((x,y,w,h),b)
        for a in pedido.get('aberturas',[]):
            z0=a.get('peitoril',0) if a['tipo']=='janela' else 0
            if obj['dimensoes_cm'][2]<=z0:continue
            d=80 if a['tipo']=='porta' else 50
            lo=math.floor(a['posicao']-a['largura']/2);hi=math.ceil(a['posicao']+a['largura']/2)
            b={'sul':(lo,0,hi-lo,d),'norte':(lo,H-d,hi-lo,d),
                'oeste':(0,lo,d,hi-lo),'leste':(W-d,lo,d,hi-lo)}[a['parede']]
            separar((x,y,w,h),b)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=float(pedido.get('segundos',5));solver.parameters.num_search_workers=1
    status=solver.solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        return {'ok':False,'estado':solver.status_name(status),'motivo':'sem proposta nas restricoes e prazo informados','solver':'OR-Tools '+ortools.__version__}
    items=[]
    for o,x,y,w,h,r,u in dados:
        xx,yy,ww,hh,rot=[solver.value(v) for v in (x,y,w,h,r)]
        use=[xx+ww/2,yy-u/2] if not rot else [xx+ww+u/2,yy+hh/2]
        items.append({'id':o['id'],'x_m':(xx+ww/2)/100,'y_m':(yy+hh/2)/100,'giro':90 if rot else 0,
                      'dimensoes_cm':o['dimensoes_cm'],'uso_frente_cm':u,'ponto_uso_cm':use})
    resultado={'ok':True,'estado':solver.status_name(status),'solver':'OR-Tools '+ortools.__version__,
        'dimensoes_cm':[solver.value(W),solver.value(H)],'area_m2':solver.value(area)/10000,'objetos':items,
        'otimo_no_modelo':status==cp_model.OPTIMAL,'nao_verificado':['circulacao e geometria real exigem verificar',
        'otimo apenas para retangulos, orientacoes e areas de uso modeladas; nao e minimo global arquitetonico']}
    from .espaco2d import avaliar
    obstaculos=list(pedido.get('obstaculos',[]))
    for o in items:
        w,d,h=o['dimensoes_cm']
        obstaculos.append({'id':o['id'],'x':o['x_m']*100,'y':o['y_m']*100,'giro':o['giro'],
            'largura':w,'profundidade':d,'altura':h})
    check=avaliar({'dimensoes_cm':resultado['dimensoes_cm'],'objetos':obstaculos,'aberturas':pedido.get('aberturas',[])})
    resultado['verificacao2d']=check
    if not check['aprovado']:
        resultado.update({'ok':False,'motivo':'filtro2d_reprovou','otimo_no_modelo':False})
        resultado.pop('objetos')
    return resultado


def compartilhadas(planta):
    salas=[(i,o) for i,o in planta['objetos'].items() if o['tipo']=='sala']
    saida=[]
    for n,(aid,a) in enumerate(salas):
        for bid,b in salas[n+1:]:
            for la,lb in [('norte','sul'),('sul','norte'),('leste','oeste'),('oeste','leste')]:
                aa=OP.faixa_da_parede(a,la);bb=OP.faixa_da_parede(b,lb)
                dx=min(aa[2],bb[2])-max(aa[0],bb[0]);dy=min(aa[3],bb[3])-max(aa[1],bb[1])
                if dx>.01 and dy>.01:
                    saida.append({'salas':[aid,bid],'lados':[la,lb],'comprimento_planejado_cm':max(dx,dy)})
    return saida


def planejar(cena,pedido,editor):
    p=PL.carregar(C.CENAS,cena);sid=pedido.get('sala');q=dict(pedido)
    if sid:
        med=relatorio.medir(p,editor,[sid])['medido'].get(sid)
        if med is None:return {'ok':False,'motivo':'medidas internas nao confirmadas'}
        q['dimensoes_cm']=[med['largura'],med['comprimento']]
        s=p['objetos'][sid]
        from .espaco2d import na_planta
        geometria=na_planta(p,sid)
        ids={x['id'] for x in q['objetos']}
        q['obstaculos']=[o for o in geometria['objetos'] if o['id'] not in ids]
        q['aberturas']=geometria['aberturas']
        reservas=list(q.get('reservas',[]))
        for oid,o in p['objetos'].items():
            if o.get('sala')!=sid:continue
            if o['tipo'] in OP.MOVEIS and oid not in {x['id'] for x in q['objetos']}:
                g=math.radians(o['giro']);w=abs(o['largura']*math.cos(g))+abs(o['profundidade']*math.sin(g));h=abs(o['largura']*math.sin(g))+abs(o['profundidade']*math.cos(g))
                reservas.append([o['x']-s['x']-w/2,o['y']-s['y']-h/2,w,h])
            if o['tipo']=='porta':
                u=o['largura'];pos=o['posicao'];W,H=q['dimensoes_cm']
                reservas.append({'sul':[pos-u/2,0,u,u],'norte':[pos-u/2,H-u,u,u],
                                 'oeste':[0,pos-u/2,u,u],'leste':[W-u,pos-u/2,u,u]}[o['parede']])
        q['reservas']=reservas
    try:r=resolver(q)
    except ImportError:
        exe=Path(C.RAIZ)/'.venv-planejamento'/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
        if not exe.is_file():return {'ok':False,'motivo':'instale requirements-planejamento.txt em .venv-planejamento; nucleo nao depende do solver'}
        proc=subprocess.run([str(exe),'-m','director.planejamento'],input=json.dumps(q).encode(),capture_output=True,cwd=C.RAIZ,timeout=float(q.get('segundos',5))+15)
        if proc.returncode:raise RuntimeError(proc.stderr.decode(errors='replace')[-1500:])
        r=json.loads(proc.stdout)
    r['aplicado']=False;r['sala']=sid
    proposta=p
    if r.get('ok') and pedido.get('nova_sala'):
        op={'operacao':'criar_sala',**pedido['nova_sala'],'largura_m':r['dimensoes_cm'][0]/100,'comprimento_m':r['dimensoes_cm'][1]/100}
        proposta,_=OP.aplicar_ficha(p,{'operacoes':[op]})
        r['ficha_sala']={'operacoes':[op]}
    r['paredes_compartilhadas_planejadas']=compartilhadas(proposta)
    return r


if __name__=='__main__':
    print(json.dumps(resolver(json.loads(sys.stdin.buffer.read())),ensure_ascii=True))
