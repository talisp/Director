"""Leitura pelo OpenUSD incluido no Unreal; nao cria ator, asset ou simulacao."""
from pxr import Usd,UsdGeom,UsdUtils
import unreal


def inspecionar(arquivo):
    stage=Usd.Stage.Open(arquivo)
    if not stage:raise ValueError('USD nao abriu')
    layers,assets,missing=UsdUtils.ComputeAllDependencies(arquivo)
    prims=list(stage.Traverse())
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_,UsdGeom.Tokens.render],useExtentsHint=False)
    caixa=cache.ComputeWorldBound(stage.GetPseudoRoot()).ComputeAlignedRange()
    escala=UsdGeom.GetStageMetersPerUnit(stage)*100
    limites=None if caixa.IsEmpty() else {'minimo':[float(v)*escala for v in caixa.GetMin()],
        'maximo':[float(v)*escala for v in caixa.GetMax()],'dimensoes':[float(v)*escala for v in caixa.GetSize()]}
    return {'engine':unreal.SystemLibrary.get_engine_version(),'openusd':Usd.GetVersion(),
        'up_axis':str(UsdGeom.GetStageUpAxis(stage)),
        'metros_por_unidade':UsdGeom.GetStageMetersPerUnit(stage),'prims':len(prims),
        'caixa_stage_cm':limites,'caixa_escopo':'AABB mundial no eixo nativo do USD, propositos default/render no tempo padrao; nao e medida importada',
        'meshes':sum(p.IsA(UsdGeom.Mesh) for p in prims),
        'juntas':[{'path':str(p.GetPath()),'tipo':p.GetTypeName()} for p in prims if 'Joint' in p.GetTypeName()],
        'dependencias_ausentes':list(missing),'layers':[l.identifier for l in layers],'assets':list(assets)}
