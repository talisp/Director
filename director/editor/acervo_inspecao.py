"""Leitura de assets salvos: sem spawn, setters, compilacao ou save."""
import unreal as U


def inventariar(pasta):
    reg=U.AssetRegistryHelpers.get_asset_registry();itens=[];erros=[];grafo={}
    opts=U.AssetRegistryDependencyOptions(include_hard_package_references=True,include_soft_package_references=True)
    for a in reg.get_assets_by_path('/Game',recursive=True):
        chave=str(a.package_name)
        try:
            deps=sorted(str(x) for x in (reg.get_dependencies(a.package_name,opts) or []));grafo[chave]=deps
            if chave.startswith(pasta.rstrip('/')+'/'):
                itens.append({'chave':chave,'nome':str(a.asset_name),'classe':str(a.asset_class_path.asset_name)})
        except Exception as exc:erros.append({'chave':chave,'erro':str(exc)})
    return {'itens':sorted(itens,key=lambda x:x['chave']),'grafo':grafo,'erros':erros,'motor':U.SystemLibrary.get_engine_version()}


def inspecionar(caminho,classe):
    d={'estado':'ok','classe':classe,'caminho':caminho,
       'limite':'configuracao do asset; nao testa estabilidade ou interacao'}
    if classe not in ('StaticMesh','SkeletalMesh','AnimSequence','PhysicsAsset'):
        return {**d,'estado':'nao_suportado','limite':'classe inventariada; sem inspetor especializado'}
    a=U.load_asset(caminho)
    if a is None:raise ValueError('asset nao carregou: '+caminho)
    if isinstance(a,U.StaticMesh):
        b=a.get_bounding_box();d['caixa_local_cm']={'min':[b.min.x,b.min.y,b.min.z],'max':[b.max.x,b.max.y,b.max.z]}
        d['dimensoes_cm']=[b.max.x-b.min.x,b.max.y-b.min.y,b.max.z-b.min.z]
        sub=U.get_editor_subsystem(U.StaticMeshEditorSubsystem);d['lods']=sub.get_lod_count(a)
        simples=sub.get_simple_collision_count(a);convexas=sub.get_convex_collision_count(a)
        if simples<0 or convexas<0:raise ValueError('motor nao conseguiu contar colisao')
        d['colisao_configurada']={'simples':simples,'convexas':convexas,'complexidade':str(sub.get_collision_complexity(a))}
        d['materiais']=[a.get_material(i).get_path_name() if a.get_material(i) else None for i in range(sub.get_number_materials(a))]
    elif isinstance(a,U.SkeletalMesh):
        b=a.get_bounds();d['dimensoes_cm']=[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z]
        d['esqueleto']=a.skeleton.get_path_name() if a.skeleton else None
        d['physics_asset']=a.physics_asset.get_path_name() if a.physics_asset else None
    elif isinstance(a,U.AnimSequence):
        d['duracao_s']=a.get_play_length();s=a.get_skeleton();d['esqueleto']=s.get_path_name() if s else None
    elif isinstance(a,U.PhysicsAsset):
        for campo in ['skeletal_body_setups','constraint_setup']:
            try:d[campo+'_quantidade']=len(a.get_editor_property(campo))
            except Exception as exc:d[campo+'_nao_verificado']=str(exc)
    return d
