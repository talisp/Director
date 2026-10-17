"""Propostas espaciais por CP-SAT existente; nao altera a cena."""
import json
import math
from pathlib import Path
import subprocess
import sys
from . import config as C,relatorio
from .nucleo import planta as PL,operacoes as OP


def _pegadas(itens,pedido):
    obstaculos=list(pedido.get('obstaculos',[]))
    for o in itens:
        w,d,h=o['dimensoes_cm']
        obstaculos.append({'id':o['id'],'x':o['x_m']*100,'y':o['y_m']*100,'giro':o['giro'],
            'largura':w,'profundidade':d,'altura':h})
    return obstaculos


def _diagnosticar(pedido):
    """Testa cada objeto sozinho, com as mesmas portas e reservas: quem nao cabe nem sozinho."""
    sozinhos=[]
    for o in pedido['objetos']:
        q=dict(pedido,objetos=[{k:v for k,v in o.items() if k not in ('na_frente_de','ao_lado_de')}],segundos=2,diagnostico=False)
        if not resolver(q,filtro=False).get('ok'):sozinhos.append(o['id'])
    return sozinhos


def resolver(pedido,filtro=True):
    from ortools.sat.python import cp_model
    import ortools
    import time
    minimo=pedido.get('minimo_cm',pedido.get('dimensoes_cm'))
    maximo=pedido.get('maximo_cm',pedido.get('dimensoes_cm'))
    if not minimo or not maximo or len(minimo)!=2 or len(maximo)!=2:raise ValueError('informe dimensoes_cm ou minimo_cm/maximo_cm')
    if any(not math.isfinite(v) or v<=0 for v in minimo+maximo) or any(a>b for a,b in zip(minimo,maximo)):raise ValueError('dimensoes positivas e limites coerentes')
    if not pedido.get('objetos'):raise ValueError('informe objetos com dimensoes_cm')
    ids=[o['id'] for o in pedido['objetos']]
    for o in pedido['objetos']:
        for campo in ('na_frente_de','ao_lado_de'):
            if o.get(campo) and o[campo] not in ids:raise ValueError(f"{campo} de {o['id']} cita objeto ausente: {o[campo]}")
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
        # Giro 0/90/180/270: a frente (e a area de uso) aponta para sul/leste/norte/oeste.
        ori=[model.new_bool_var(o['id']+f'_giro{90*k}') for k in range(4)]
        model.add_exactly_one(ori)
        if o.get('girar',True) is False:model.add(ori[0]==1)
        rot=model.new_bool_var(o['id']+'_rot');model.add(rot==ori[1]+ori[3])
        rw=model.new_int_var(min(w,d),max(w,d),o['id']+'_w');rh=model.new_int_var(min(w,d),max(w,d),o['id']+'_h')
        model.add(rw==w+(d-w)*rot);model.add(rh==d+(w-d)*rot)
        x=model.new_int_var(folga,math.floor(maximo[0]),o['id']+'_x');y=model.new_int_var(folga,math.floor(maximo[1]),o['id']+'_y')
        model.add(x+rw<=W-folga);model.add(y+rh<=H-folga)
        model.add(y>=uso+folga).only_enforce_if(ori[0]);model.add(x+rw+uso<=W-folga).only_enforce_if(ori[1])
        model.add(y+rh+uso<=H-folga).only_enforce_if(ori[2]);model.add(x>=uso+folga).only_enforce_if(ori[3])
        # Encostado: as costas na parede (padrao), menos o que fica na frente de outro objeto.
        if o.get('encostar',not o.get('na_frente_de')):
            model.add(y+rh==H-folga).only_enforce_if(ori[0]);model.add(x==folga).only_enforce_if(ori[1])
            model.add(y==folga).only_enforce_if(ori[2]);model.add(x+rw==W-folga).only_enforce_if(ori[3])
        xe=model.new_int_var(0,math.floor(maximo[0]),o['id']+'_xe');ye=model.new_int_var(0,math.floor(maximo[1]),o['id']+'_ye')
        model.add(xe==x+rw);model.add(ye==y+rh)
        xis.append(model.new_interval_var(x,rw,xe,o['id']+'_ix'))
        yis.append(model.new_interval_var(y,rh,ye,o['id']+'_iy'))
        dados.append((o,x,y,rw,rh,ori,uso))
    model.add_no_overlap_2d(xis,yis)
    def separar(a,b,cond=None):
        bits=[model.new_bool_var('separa') for _ in range(4)]
        exprs=[a[0]+a[2]<=b[0],b[0]+b[2]<=a[0],a[1]+a[3]<=b[1],b[1]+b[3]<=a[1]]
        for bit,expr in zip(bits,exprs):model.add(expr).only_enforce_if([bit]+([cond] if cond is not None else []))
        c=model.add_bool_or(bits)
        if cond is not None:c.only_enforce_if(cond)
    for i,(obj,x,y,w,h,r,u) in enumerate(dados):
        for j,(outro,xx,yy,ww,hh,rr,uu) in enumerate(dados):
            if i==j:continue
            # Cadeira "na frente de" uma mesa fica dentro da area de uso da mesa.
            zonas=[(x,y-u,w,u),(x+w,y,u,h),(x,y+h,w,u),(x-u,y,u,h)]
            if outro.get('na_frente_de')==obj['id']:
                # De frente para a mesa: o giro da cadeira e o da mesa mais 180.
                for k in range(4):model.add(rr[(k+2)%4]==r[k])
                encosta=[yy+hh==y,xx==x+w,yy==y+h,xx+ww==x]
                for k,(zx,zy,zw,zh) in enumerate(zonas):
                    for expr in (xx>=zx,xx+ww<=zx+zw,yy>=zy,yy+hh<=zy+zh,encosta[k]):model.add(expr).only_enforce_if(r[k])
                continue
            if outro.get('ao_lado_de')==obj['id']:
                # Mesmo giro e encostado de lado: com os dois encostados, fica junto da cabeceira.
                for k in range(4):model.add(rr[k]==r[k])
                lados=[model.new_bool_var('lado') for _ in range(4)]
                rot_alvo=model.new_bool_var('');model.add(rot_alvo==r[1]+r[3])
                model.add(xx+ww==x).only_enforce_if([lados[0],rot_alvo.Not()]);model.add(xx==x+w).only_enforce_if([lados[1],rot_alvo.Not()])
                model.add(yy+hh==y).only_enforce_if([lados[2],rot_alvo]);model.add(yy==y+h).only_enforce_if([lados[3],rot_alvo])
                model.add_bool_or(lados[:2]).only_enforce_if(rot_alvo.Not());model.add_bool_or(lados[2:]).only_enforce_if(rot_alvo)
            com_uso=[(x,y-u,w,h+u),(x,y,w+u,h),(x,y,w,h+u),(x-u,y,w+u,h)]
            for k,ret in enumerate(com_uso):separar(ret,(xx,yy,ww,hh),r[k])
        for b in reservas:separar((x,y,w,h),b)
        for a in pedido.get('aberturas',[]):
            z0=a.get('peitoril',0) if a['tipo']=='janela' else 0
            if obj['dimensoes_cm'][2]<=z0:continue
            d=max(80,math.ceil(a['largura'])) if a['tipo']=='porta' else 50
            lo=math.floor(a['posicao']-a['largura']/2);hi=math.ceil(a['posicao']+a['largura']/2)
            b={'sul':(lo,0,hi-lo,d),'norte':(lo,H-d,hi-lo,d),
                'oeste':(0,lo,d,hi-lo),'leste':(W-d,lo,d,hi-lo)}[a['parede']]
            separar((x,y,w,h),b)
    for a in pedido.get('aberturas',[]):
        # A abertura tem de caber na parede do tamanho testado.
        model.add((W if a['parede'] in ('sul','norte') else H)>=math.ceil(a['posicao']+a['largura']/2))
    versao='OR-Tools '+ortools.__version__
    limite=float(pedido.get('segundos',5));inicio=time.monotonic()
    maximo_tentativas=int(pedido.get('tentativas',40)) if filtro else 1
    passo=int(pedido.get('passo_cm',25))
    historico=[];solver=None;status=None
    por_tamanho=int(pedido.get("tentativas_por_tamanho",6));por_area={}
    for tentativa in range(1,maximo_tentativas+1):
        resta=limite-(time.monotonic()-inicio)
        if resta<=.05:break
        solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=resta;solver.parameters.num_search_workers=1
        status=solver.solve(model)
        if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):break
        items=[]
        for o,x,y,w,h,r,u in dados:
            xx,yy,ww,hh=[solver.value(v) for v in (x,y,w,h)];k=[solver.value(b) for b in r].index(1)
            use=[[xx+ww/2,yy-u/2],[xx+ww+u/2,yy+hh/2],[xx+ww/2,yy+hh+u/2],[xx-u/2,yy+hh/2]][k]
            # Alcance: o centro da capsula chega a ate raio+20 cm da frente, mesmo com area de uso rasa.
            a=max(u,int(pedido.get('raio_cm',34))+20)
            caixa=[[xx,yy-a,xx+ww,yy],[xx+ww,yy,xx+ww+a,yy+hh],[xx,yy+hh,xx+ww,yy+hh+a],[xx-a,yy,xx,yy+hh]][k]
            items.append({'id':o['id'],'x_m':(xx+ww/2)/100,'y_m':(yy+hh/2)/100,'giro':90*k,
                          'dimensoes_cm':o['dimensoes_cm'],'uso_frente_cm':u,'ponto_uso_cm':use,'zona_uso_cm':caixa,
                          **{c:o[c] for c in ('na_frente_de','ao_lado_de') if o.get(c)}})
        dims=[solver.value(W),solver.value(H)]
        resultado={'ok':True,'estado':solver.status_name(status),'solver':versao,
            'dimensoes_cm':dims,'area_m2':solver.value(area)/10000,'objetos':items,'tentativas':tentativa,
            'otimo_no_modelo':status==cp_model.OPTIMAL and tentativa==1,'nao_verificado':['circulacao e geometria real exigem verificar',
            'otimo apenas para retangulos, orientacoes e areas de uso modeladas; nao e minimo global arquitetonico']+
            (['objetos na_frente_de (cadeira) nao entram no filtro 2D: supoe-se que sao afastados para usar a mesa'] if any(i.get('na_frente_de') for i in items) else [])}
        if not filtro:return resultado
        from .espaco2d import avaliar
        # Cadeira "na frente de" e afastada por quem usa a mesa: nao bloqueia o acesso no filtro 2D.
        check=avaliar({'dimensoes_cm':dims,'objetos':_pegadas([i for i in items if not i.get('na_frente_de')],pedido),'aberturas':pedido.get('aberturas',[]),
                       'alvos':[{'id':i['id'],'caixa':i['zona_uso_cm']} for i in items if i['uso_frente_cm']>0]})
        resultado['verificacao2d']=check
        if check['aprovado']:
            if tentativa>1:resultado['nao_verificado'].append(f'{tentativa-1} arrumacoes anteriores foram reprovadas pelo filtro 2D; esta e a primeira aprovada, nao a menor possivel')
            return resultado
        historico.append({'tentativa':tentativa,'dimensoes_cm':dims,'regioes':check['regioes'],
            'bloqueadores_individuais':check['bloqueadores_individuais'],'violacoes':check['violacoes']})
        # Corte: a proxima arrumacao muda o tamanho, ou algum objeto gira ou anda pelo menos `passo` cm.
        bits=[]
        for o,x,y,w,h,r,u in dados:
            x0,y0=solver.value(x),solver.value(y)
            for expr in (x<=x0-passo,x>=x0+passo,y<=y0-passo,y>=y0+passo):
                b=model.new_bool_var('corte');model.add(expr).only_enforce_if(b);bits.append(b)
            bits+=[b.Not() for b in r if solver.value(b)]
        for var,v0 in ((W,dims[0]),(H,dims[1])):
            for expr in (var<=v0-1,var>=v0+1):
                b=model.new_bool_var('corte');model.add(expr).only_enforce_if(b);bits.append(b)
        model.add_bool_or(bits)
        # Depois de algumas tentativas no mesmo tamanho, passa para um tamanho maior.
        a0=solver.value(area);por_area[a0]=por_area.get(a0,0)+1
        if por_area[a0]>=por_tamanho:model.add(area>=math.ceil(a0*(1+float(pedido.get("passo_area",.03)))))
    estado=solver.status_name(status) if status is not None else 'SEM_TEMPO'
    falha={'ok':False,'estado':estado,'solver':versao,'tentativas':len(historico)}
    if historico:
        ultimo=historico[-1]
        esgotou=estado=='INFEASIBLE'
        falha.update({'motivo':'filtro2d_reprovou','verificacao2d_tentativas':historico[-5:],
            'detalhe':f"{len(historico)} arrumacoes foram reprovadas pelo filtro 2D (circulacao); "
                      f"a ultima deixou {ultimo['regioes']} regioes livres separadas"+
                      (f"; o que mais separa: {', '.join(ultimo['bloqueadores_individuais'])}" if ultimo['bloqueadores_individuais'] else '')+
                      ('; nao ha outra arrumacao diferente nesses limites' if esgotou else '; o prazo ou o limite de tentativas acabou antes de esgotar as opcoes')})
    elif estado=='INFEASIBLE':
        sozinhos=_diagnosticar(pedido) if pedido.get('diagnostico',True) else []
        falha.update({'motivo':'impossivel_no_modelo','nao_cabem_sozinhos':sozinhos,
            'detalhe':'provado: os objetos, areas de uso, portas e reservas nao cabem juntos nos limites informados'+
                      (f"; nao cabem nem sozinhos: {', '.join(sozinhos)}" if sozinhos else '; cada objeto cabe sozinho, o conflito e da combinacao')})
    elif estado=='MODEL_INVALID':
        falha.update({'motivo':'modelo_invalido','detalhe':'pedido inconsistente para o solver; confira medidas e campos'})
    else:
        falha.update({'motivo':'sem_prova_no_prazo','detalhe':f'o solver nao achou proposta em {limite:g} s e nao provou que e impossivel; aumente segundos'})
    return falha


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
    hipotese=bool(sid) and any(k in pedido for k in ('dimensoes_cm','minimo_cm','maximo_cm'))
    if sid:
        if sid not in p['objetos'] or p['objetos'][sid]['tipo']!='sala':raise ValueError(f'sala inexistente na planta: {sid}')
        s=p['objetos'][sid]
        if hipotese:
            # Testa outro tamanho com as portas e janelas reais, sem medir nem mudar a cena.
            origem={'dimensoes':'hipotese do pedido; a cena NAO foi alterada','planta_cm':[s['largura'],s['comprimento']],
                    'aplicar':'para usar, mude a sala com fazer (mudar_sala) e rode planejar de novo sem dimensoes'}
        else:
            med=relatorio.medir(p,editor,[sid])['medido'].get(sid)
            if med is None:return {'ok':False,'motivo':'medidas internas nao confirmadas'}
            q['dimensoes_cm']=[med['largura'],med['comprimento']]
            origem={'dimensoes':'medidas internas confirmadas no editor'}
        from .espaco2d import na_planta
        geometria=na_planta(p,sid)
        ids={x['id'] for x in q['objetos']}
        q['obstaculos']=[o for o in geometria['objetos'] if o['id'] not in ids]
        q['aberturas']=geometria['aberturas']
        reservas=list(q.get('reservas',[]));mantidos=[]
        for oid,o in p['objetos'].items():
            if o.get('sala')!=sid:continue
            if o['tipo'] in OP.MOVEIS and oid not in {x['id'] for x in q['objetos']}:
                g=math.radians(o['giro']);w=abs(o['largura']*math.cos(g))+abs(o['profundidade']*math.sin(g));h=abs(o['largura']*math.sin(g))+abs(o['profundidade']*math.cos(g))
                reservas.append([o['x']-s['x']-w/2,o['y']-s['y']-h/2,w,h]);mantidos.append(oid)
            if o['tipo']=='porta' and not hipotese:
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
    if sid:
        r['origem']=origem
        if mantidos:
            r['mantidos_da_cena']=mantidos
            if not r.get('ok'):r['detalhe']=r.get('detalhe','')+f"; a sala ja tem {', '.join(mantidos)} registrados, que ficam reservados: para replanejar algum, use o mesmo id no pedido"
    proposta=p
    if r.get('ok') and pedido.get('nova_sala'):
        op={'operacao':'criar_sala',**pedido['nova_sala'],'largura_m':r['dimensoes_cm'][0]/100,'comprimento_m':r['dimensoes_cm'][1]/100}
        proposta,_=OP.aplicar_ficha(p,{'operacoes':[op]})
        r['ficha_sala']={'operacoes':[op]}
    r['paredes_compartilhadas_planejadas']=compartilhadas(proposta)
    return r


if __name__=='__main__':
    print(json.dumps(resolver(json.loads(sys.stdin.buffer.read())),ensure_ascii=True))
