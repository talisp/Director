"""Vista textual da planta desejada. Nao consulta nem modifica o Unreal."""
import math
import os
from .nucleo import planta as PL,operacoes as OP,portas
from . import config as C


def renderizar(planta,sala=None,escala_cm=None):
    from .planejamento import compartilhadas
    objs=planta['objetos']
    salas={i:o for i,o in objs.items() if o['tipo']=='sala' and (sala is None or i==sala)}
    if not salas:raise ValueError('nenhuma sala encontrada; informe id de sala existente')
    moveis={i:o for i,o in objs.items() if o.get('sala') in salas and o['tipo'] in OP.MOVEIS}
    if len(moveis)>26:raise ValueError('mais de 26 moveis: selecione uma sala para manter o desenho legivel')
    pontos=[]
    for s in salas.values():
        t=s['parede'];pontos += [(s['x']-t,s['y']-t),(s['x']+s['largura']+t,s['y']+s['comprimento']+t)]
    for o in moveis.values():pontos.extend(portas.movel_vertices(o))
    vaos={i:o for i,o in objs.items() if o.get('sala') in salas and o['tipo'] in OP.VAOS}
    for o in vaos.values():
        if o['tipo']=='porta':
            s=salas[o['sala']]
            pontos.extend((x+s['x'],y+s['y']) for x,y in portas.vertices({**o,'espessura_parede':s['parede']},s['largura'],s['comprimento']))
    x0,y0=min(p[0] for p in pontos),min(p[1] for p in pontos)
    x1,y1=max(p[0] for p in pontos),max(p[1] for p in pontos)
    escala=escala_cm or math.ceil(max(10,(x1-x0)/94,(y1-y0)/62)/10)*10
    if isinstance(escala,bool) or not math.isfinite(escala) or escala<=0:raise ValueError('escala positiva em cm')
    x0=math.floor(x0/escala)*escala;y0=math.floor(y0/escala)*escala
    cols=math.ceil((x1-x0)/escala)+1;linhas=math.ceil((y1-y0)/escala)+1
    if cols>100 or linhas>68:raise ValueError('desenho grande: selecione sala ou aumente escala_cm')
    norte=y0+(linhas-1)*escala;grade=[[' ']*cols for _ in range(linhas)]
    def celula(x,y):return round((norte-y)/escala),round((x-x0)/escala)
    def por(x,y,simbolo):
        row,col=celula(x,y)
        if 0<=row<linhas and 0<=col<cols:grade[row][col]=simbolo
    def retangulo(a,b,c,d,simbolo):
        for row in range(linhas):
            y=norte-row*escala
            for col in range(cols):
                x=x0+col*escala
                if a-1e-6<=x<=c+1e-6 and b-1e-6<=y<=d+1e-6:grade[row][col]=simbolo
    def linha(a,b,simbolo):
        n=max(1,math.ceil(max(abs(b[0]-a[0]),abs(b[1]-a[1]))/escala*2))
        for k in range(n+1):por(a[0]+(b[0]-a[0])*k/n,a[1]+(b[1]-a[1])*k/n,simbolo)
    for s in salas.values():retangulo(s['x'],s['y'],s['x']+s['largura'],s['y']+s['comprimento'],'.')
    # Zonas reservadas, nao declaradas livres: moveis/folhas podem ocupa-las.
    for o in vaos.values():
        s=salas[o['sala']];p=o['posicao'];w=o['largura'];d=80 if o['tipo']=='porta' else 50;W,H=s['largura'],s['comprimento']
        a,b,c,e={'sul':(p-w/2,0,p+w/2,d),'norte':(p-w/2,H-d,p+w/2,H),
                 'oeste':(0,p-w/2,d,p+w/2),'leste':(W-d,p-w/2,W,p+w/2)}[o['parede']]
        retangulo(s['x']+a,s['y']+b,s['x']+c,s['y']+e,':')
    for s in salas.values():
        for lado in OP.LADOS:
            a,b,c,d=OP.faixa_da_parede(s,lado)
            linha(((a+c)/2,b),((a+c)/2,d),'#') if lado in ('leste','oeste') else linha((a,(b+d)/2),(c,(b+d)/2),'#')
    legenda=[]
    for oid,o in sorted(vaos.items()):
        s=salas[o['sala']];p=o['posicao'];w=o['largura'];t=s['parede']/2
        pos={'sul':(s['x']+p,s['y']-t),'norte':(s['x']+p,s['y']+s['comprimento']+t),
             'oeste':(s['x']-t,s['y']+p),'leste':(s['x']+s['largura']+t,s['y']+p)}[o['parede']]
        dx,dy=(1,0) if o['parede'] in ('sul','norte') else (0,1)
        simbolo='+' if o['tipo']=='porta' else '='
        linha((pos[0]-dx*w/2,pos[1]-dy*w/2),(pos[0]+dx*w/2,pos[1]+dy*w/2),simbolo)
        entry={'simbolo':simbolo,'id':oid,'tipo':o['tipo'],'sala':o['sala'],'parede':o['parede'],'largura_cm':w}
        if o['tipo']=='porta':
            v=portas.vertices({**o,'espessura_parede':s['parede']},s['largura'],s['comprimento'])
            a,b=[(x+s['x'],y+s['y']) for x,y in v[:2]]
            linha(a,b,'/');por(*a,'o')
            entry.update(dobradica=portas.dobradica(o),sentido=o.get('sentido','dentro'),angulo=o['angulo'])
        legenda.append(entry)
    centros={}
    for n,(oid,o) in enumerate(sorted(moveis.items())):
        simbolo=chr(65+n);s=salas[o['sala']];g=math.radians(o.get('giro',0));c,si=math.cos(g),math.sin(g)
        for row in range(linhas):
            for col in range(cols):
                dx=x0+col*escala-o['x'];dy=norte-row*escala-o['y']
                if abs(dx*c+dy*si)<=o['largura']/2+1e-6 and abs(-dx*si+dy*c)<=o['profundidade']/2+1e-6:grade[row][col]=simbolo
        por(o['x'],o['y'],simbolo);centros[oid]=list(celula(o['x'],o['y']))
        vs=portas.movel_vertices(o)
        excesso={'oeste':max(0,s['x']-min(x for x,y in vs)),
                 'leste':max(0,max(x for x,y in vs)-(s['x']+s['largura'])),
                 'sul':max(0,s['y']-min(y for x,y in vs)),
                 'norte':max(0,max(y for x,y in vs)-(s['y']+s['comprimento']))}
        excesso={k:round(v,3) for k,v in excesso.items() if v>.01}
        legenda.append({'simbolo':simbolo,'id':oid,'tipo':o.get('categoria',o['tipo']),'sala':o['sala'],
                        'excesso_interno_planejado_cm':excesso,
                        'centro_cm':[o['x'],o['y']],'dimensoes_cm':[o['largura'],o['profundidade'],o['altura']]})
    return {'ok':True,'cena':planta['cena'],'revisao':planta['revisao'],'fonte':'planta_desejada',
            'escala_cm':escala,'orientacao':'norte em cima; leste a direita','origem_grade_cm':[x0,norte],
            'texto':'\n'.join(''.join(row).rstrip() for row in grade),'legenda':legenda,
            'simbolos':{'#':'parede','+':'vao de porta','=':'janela','/':'folha','o':'dobradica',':':'zona reservada','.':'chao',' ':'fora'},
            'salas':{i:{'interno_cm':[s['largura'],s['comprimento']],'sudoeste_cm':[s['x'],s['y']]} for i,s in salas.items()},
            'paredes_compartilhadas':[a for a in compartilhadas(planta) if any(i in salas for i in a['salas'])],
            'centros_grade':centros,'avisos':OP.avisos(planta),
            'limite':'desenho aproximado da planta, nao observacao do editor; zonas podem estar ocupadas; use estado/planta2d/medir para verificar'}


def cli(cena,sala=None):
    if not os.path.isfile(PL.caminho(C.CENAS,cena)):raise ValueError('cena sem planta registrada')
    return renderizar(PL.carregar(C.CENAS,cena),sala)
