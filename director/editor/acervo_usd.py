"""Leitura pelo OpenUSD incluido no Unreal; nao cria ator, asset ou simulacao."""
from pxr import Usd,UsdGeom,UsdUtils


def inspecionar(arquivo):
    stage=Usd.Stage.Open(arquivo)
    if not stage:raise ValueError('USD nao abriu')
    layers,assets,missing=UsdUtils.ComputeAllDependencies(arquivo)
    prims=list(stage.Traverse())
    return {'up_axis':str(UsdGeom.GetStageUpAxis(stage)),
        'metros_por_unidade':UsdGeom.GetStageMetersPerUnit(stage),'prims':len(prims),
        'meshes':sum(p.IsA(UsdGeom.Mesh) for p in prims),
        'juntas':[{'path':str(p.GetPath()),'tipo':p.GetTypeName()} for p in prims if 'Joint' in p.GetTypeName()],
        'dependencias_ausentes':list(missing),'layers':[l.identifier for l in layers],'assets':list(assets)}
