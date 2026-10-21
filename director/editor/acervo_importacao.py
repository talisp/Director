"""Importacao nativa, somente assets novos; nao cria atores nem altera level."""
import unreal as U


def conferir(malhas):
    sub=U.get_editor_subsystem(U.StaticMeshEditorSubsystem)
    divergencias=[]
    for m in malhas:
        a=U.load_asset(m['asset'])
        if not isinstance(a,U.StaticMesh):
            divergencias.append({'asset':m['asset'],'motivo':'ausente ou classe diferente'});continue
        b=a.get_bounds()
        atual={'dimensoes_cm':[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z],
            'centro_cm':[b.origin.x,b.origin.y,b.origin.z],
            'complexidade_colisao':str(sub.get_collision_complexity(a)),
            'colisoes_simples':sub.get_simple_collision_count(a),'convexos':sub.get_convex_collision_count(a)}
        for k,v in atual.items():
            if m.get(k)!=v:divergencias.append({'asset':m['asset'],'campo':k,'atual':v,'anterior':m.get(k)})
    return {'ok':bool(malhas) and not divergencias,'divergencias':divergencias,
        'limite':'confere bounds e configuracao de colisao; nao prova forma completa, materiais nem fisica em simulacao'}


def importar(arquivo,destino,usd=False):
    if U.EditorAssetLibrary.does_directory_exist(destino):raise ValueError('destino ja existe; nao sobrescrever nem repetir importacao')
    if usd:
        from pxr import UsdUtils
        layers,assets,missing=UsdUtils.ComputeAllDependencies(arquivo)
        if missing:raise ValueError('dependencias USD ausentes: '+str(list(missing)))
    task=U.AssetImportTask()
    for k,v in {'filename':arquivo,'destination_path':destino,'automated':True,
                'replace_existing':False,'save':True,'async_':False}.items():task.set_editor_property(k,v)
    if usd:
        options=U.UsdStageImportOptions()
        for k,v in {'import_actors':False,'import_geometry':True,'import_materials':True,
            'import_level_sequences':False,'import_skeletal_animations':False,
            'override_stage_options':False,'use_prim_kinds_for_collapsing':False}.items():options.set_editor_property(k,v)
        task.set_editor_property('options',options)
        task.set_editor_property('factory',U.UsdStageAssetImportFactory())
    U.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    # Interchange pode criar varias malhas/materiais e nao preencher GetObjects por completo.
    paths=U.EditorAssetLibrary.list_assets(destino,recursive=True,include_folder=False)
    malhas=[];falhas=[]
    for path in paths:
        a=U.load_asset(path)
        if a is None:falhas.append(path);continue
        if not U.EditorAssetLibrary.save_loaded_asset(a,only_if_is_dirty=True):falhas.append(path)
        if isinstance(a,U.StaticMesh):
            b=a.get_bounds();sub=U.get_editor_subsystem(U.StaticMeshEditorSubsystem)
            caminhos=[str(x) for u in a.get_editor_property('asset_user_data') if hasattr(U,'UsdAssetUserData') and isinstance(u,U.UsdAssetUserData) for x in u.get_editor_property('prim_paths')] if usd else []
            malhas.append({'asset':a.get_path_name().rsplit('.',1)[0],'prim_paths':caminhos,
                'dimensoes_cm':[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z],
                'centro_cm':[b.origin.x,b.origin.y,b.origin.z],
                'complexidade_colisao':str(sub.get_collision_complexity(a)),
                'colisoes_simples':sub.get_simple_collision_count(a),'convexos':sub.get_convex_collision_count(a)})
    return {'ok':bool(malhas) and not falhas,'malhas':malhas,'assets':list(paths),'falhas':falhas,
            'formato':'usd_malhas' if usd else 'gltf','articulacao_chaos':'nao_validada',
            'destino':destino,'recuperacao':'assets novos preservados para inspecao; nao repetir em outro destino sem conferir a primeira tentativa'}
