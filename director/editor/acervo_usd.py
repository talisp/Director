"""Leitura pelo OpenUSD incluido no Unreal; nao cria ator, asset ou simulacao."""
from pxr import Usd,UsdGeom,UsdUtils
import unreal
import math


def _valor(v):
    if v is None or isinstance(v,(str,bool,int)):return v
    if isinstance(v,float):return v if math.isfinite(v) else {'nao_finito':str(v)}
    if hasattr(v,'GetReal') and hasattr(v,'GetImaginary'):
        return {'real':_valor(float(v.GetReal())),'imaginario':[_valor(float(x)) for x in v.GetImaginary()]}
    try:return [_valor(x) for x in v]
    except TypeError:return str(v)


def _caixa(cache,prim,escala):
    caixa=cache.ComputeWorldBound(prim).ComputeAlignedRange()
    if caixa.IsEmpty():return None
    return {'minimo':[float(v)*escala for v in caixa.GetMin()],
            'maximo':[float(v)*escala for v in caixa.GetMax()],
            'dimensoes':[float(v)*escala for v in caixa.GetSize()]}


def _parte(prim,cache,xforms,escala):
    """O OpenUSD resolve a hierarquia e os bounds; Python apenas serializa."""
    path=str(prim.GetPath());xf=UsdGeom.Xformable(prim)
    junta='Joint' in prim.GetTypeName()
    attrs={str(a.GetName()):_valor(a.Get()) for a in prim.GetAttributes()
           if str(a.GetName()).startswith(('physics:','physx')) and a.HasAuthoredValueOpinion()}
    rels={str(r.GetName()):[str(p) for p in r.GetTargets()] for r in prim.GetRelationships()
          if str(r.GetName()).startswith('physics:')}
    if not xf and not UsdGeom.Scope(prim) and not junta and not attrs and not rels:return None
    d={'path':path,'pai':str(prim.GetParent().GetPath()),'tipo':prim.GetTypeName(),
       'atributos_fisica_declarados':attrs,'relacoes_fisica_declaradas':rels,
       'origem_tipo':'declaracao_fonte','montagem_chaos':'nao_validada'}
    if xf:
        d['transformacao_local']=_valor(xf.GetLocalTransformation())
        d['transformacao_mundial']=_valor(xforms.GetLocalToWorldTransform(prim))
        d['reseta_hierarquia']=xf.GetResetXformStack()
        if prim.IsA(UsdGeom.Mesh):
            d['caixa_stage_cm']=_caixa(cache,prim,escala)
            d['caixa_origem']='medida OpenUSD; AABB mundial da parte no stage, cm'
    return d


def inspecionar(arquivo):
    stage=Usd.Stage.Open(arquivo)
    if not stage:raise ValueError('USD nao abriu')
    layers,assets,missing=UsdUtils.ComputeAllDependencies(arquivo)
    prims=list(stage.Traverse())
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_,UsdGeom.Tokens.render],useExtentsHint=False)
    escala=UsdGeom.GetStageMetersPerUnit(stage)*100
    xforms=UsdGeom.XformCache(Usd.TimeCode.Default())
    partes=[d for p in prims if (d:=_parte(p,cache,xforms,escala)) is not None]
    juntas=[d for d in partes if 'Joint' in d['tipo']]
    return {'engine':unreal.SystemLibrary.get_engine_version(),'openusd':Usd.GetVersion(),
        'up_axis':str(UsdGeom.GetStageUpAxis(stage)),
        'metros_por_unidade':UsdGeom.GetStageMetersPerUnit(stage),'prims':len(prims),
        'caixa_stage_cm':_caixa(cache,stage.GetPseudoRoot(),escala),'caixa_escopo':'AABB mundial no eixo nativo do USD, propositos default/render no tempo padrao; nao e medida importada',
        'meshes':sum(p.IsA(UsdGeom.Mesh) for p in prims),
        'juntas':juntas,'partes':partes,
        'partes_escopo':'Usd.Stage.Traverse no tempo padrao; nao enumera instance proxies',
        'transformacoes_referencial':'Gf.Matrix4d indexada [linha][coluna]; unidades/eixos originais do stage; tempo padrao. Nao sao transforms de componentes Unreal.',
        'dependencias_ausentes':list(missing),'layers':[l.realPath or l.identifier for l in layers],'assets':list(assets)}
