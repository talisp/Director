"""Importacao nativa, somente assets novos; nao cria atores nem altera level."""
import unreal as U


def importar(arquivo,destino):
    if U.EditorAssetLibrary.does_directory_exist(destino):raise ValueError('destino ja existe; nao sobrescrever nem repetir importacao')
    task=U.AssetImportTask()
    for k,v in {'filename':arquivo,'destination_path':destino,'automated':True,
                'replace_existing':False,'save':True,'async_':False}.items():task.set_editor_property(k,v)
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
            malhas.append({'asset':a.get_path_name().rsplit('.',1)[0],
                'dimensoes_cm':[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z],
                'centro_cm':[b.origin.x,b.origin.y,b.origin.z],
                'colisoes_simples':sub.get_simple_collision_count(a),'convexos':sub.get_convex_collision_count(a)})
    return {'ok':bool(malhas) and not falhas,'malhas':malhas,'assets':list(paths),'falhas':falhas,
            'destino':destino,'recuperacao':'assets novos preservados para inspecao; nao repetir em outro destino sem conferir a primeira tentativa'}
