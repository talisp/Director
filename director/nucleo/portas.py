"""Orientacao da folha compartilhada pela derivacao, conciliacao e filtro geometrico."""
import math


def dobradica(o):
    return o.get('dobradica', 'fim' if o['parede'] in ('norte','oeste') else 'inicio')


def sinal(o):
    padrao = 'fim' if o['parede'] in ('norte','oeste') else 'inicio'
    return (1 if dobradica(o)==padrao else -1) * (-1 if o.get('sentido','dentro')=='fora' else 1)


def vertices(o, largura, comprimento, angulo=None):
    """Retangulo da folha de 4 cm, em coordenadas internas do comodo. Nao testa o arco varrido."""
    lado=o['parede'];fim=dobradica(o)=='fim';pos=o['posicao']+(1 if fim else -1)*o['largura']/2
    t=o.get('espessura_parede',0)/2
    x,y={'sul':(pos,-t),'norte':(pos,comprimento+t),'oeste':(-t,pos),'leste':(largura+t,pos)}[lado]
    giro=(0 if lado in ('sul','norte') else 90)+(180 if fim else 0)
    a=math.radians(giro+sinal(o)*(o.get('angulo',0) if angulo is None else angulo))
    dx,dy=math.cos(a),math.sin(a);nx,ny=-dy,dx;L=o['largura']
    # Construction Script: centro local Y=Espessura/2; a folha ocupa Y=0..4, nao -2..2.
    return [(x+u*dx+v*nx,y+u*dy+v*ny) for u,v in ((0,0),(L,0),(L,4),(0,4))]


def movel_vertices(o):
    a=math.radians(o.get('giro',0));c,s=math.cos(a),math.sin(a)
    return [(o['x']+x*c-y*s,o['y']+x*s+y*c) for x,y in
            ((-o['largura']/2,-o['profundidade']/2),(o['largura']/2,-o['profundidade']/2),
             (o['largura']/2,o['profundidade']/2),(-o['largura']/2,o['profundidade']/2))]


def sobrepoem(a,b,tolerancia=.01):
    """Separacao de retangulos orientados, com tolerancia em cm; sem dependencia opcional."""
    for p in (a,b):
        for i in range(len(p)):
            dx,dy=p[(i+1)%len(p)][0]-p[i][0],p[(i+1)%len(p)][1]-p[i][1]
            n=math.hypot(dx,dy)
            if not n:continue
            nx,ny=-dy/n,dx/n
            aa=[x*nx+y*ny for x,y in a];bb=[x*nx+y*ny for x,y in b]
            if min(max(aa),max(bb))-max(min(aa),min(bb))<=tolerancia:return False
    return True
