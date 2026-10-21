"""Assets novos de materiais CC0 para ensaio; nao modifica atores nem salva levels."""
from pathlib import Path
import unreal as U


def criar(cor,normal,roughness,destino,nome):
    if not destino.startswith('/Game/Director/Acervo/PilotoMateriais/'):
        raise ValueError('destino fora do piloto')
    if not nome.replace('_','').isalnum():raise ValueError('nome invalido')
    if U.EditorAssetLibrary.does_directory_exist(destino):
        raise ValueError('destino ja existe: conferir antes de repetir; nao sobrescrever')
    paths=[Path(p) for p in (cor,normal,roughness)]
    if any(not p.is_file() or p.suffix.lower() not in ('.png','.jpg','.jpeg') for p in paths):
        raise ValueError('texturas locais ausentes ou formato inesperado')
    tools=U.AssetToolsHelpers.get_asset_tools();texturas=[]
    for p in paths:
        t=U.AssetImportTask()
        for k,v in {'filename':str(p),'destination_path':destino,'automated':True,
                    'replace_existing':False,'save':False,'async_':False}.items():t.set_editor_property(k,v)
        t.set_editor_property('factory',U.TextureFactory())
        tools.import_asset_tasks([t])
        objs=[U.load_asset(x) for x in t.get_editor_property('imported_object_paths')]
        objs=[x for x in objs if isinstance(x,U.Texture2D)]
        if len(objs)!=1:raise ValueError('importacao parcial: inspecionar destino antes de repetir')
        texturas.append(objs[0])
    texturas[0].set_editor_property('srgb',True)
    texturas[1].set_editor_property('srgb',False)
    texturas[1].set_editor_property('compression_settings',U.TextureCompressionSettings.TC_NORMALMAP)
    texturas[2].set_editor_property('srgb',False)
    mat=tools.create_asset(nome,destino,U.Material,U.MaterialFactoryNew())
    if mat is None:raise ValueError('material nao criado; destino parcial preservado')
    L=U.MaterialEditingLibrary
    props=[U.MaterialProperty.MP_BASE_COLOR,U.MaterialProperty.MP_NORMAL,U.MaterialProperty.MP_ROUGHNESS]
    samplers=[U.MaterialSamplerType.SAMPLERTYPE_COLOR,U.MaterialSamplerType.SAMPLERTYPE_NORMAL,U.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR]
    for i,(tex,prop,sampler) in enumerate(zip(texturas,props,samplers)):
        node=L.create_material_expression(mat,U.MaterialExpressionTextureSample,-400,i*250)
        node.set_editor_property('texture',tex);node.set_editor_property('sampler_type',sampler)
        if not L.connect_material_property(node,'RGB' if i<2 else 'R',prop):
            raise ValueError('conexao do material falhou; inspecionar destino')
    L.recompile_material(mat)
    for asset in [*texturas,mat]:
        if not U.EditorAssetLibrary.save_loaded_asset(asset,only_if_is_dirty=False):
            raise ValueError('falha ao salvar asset novo; nao repetir importacao automaticamente')
    nodes=[L.get_material_property_input_node(mat,p) for p in props]
    return {'material':mat.get_path_name().rsplit('.',1)[0],
            'texturas':[t.get_path_name().rsplit('.',1)[0] for t in texturas],
            'conexoes':[n is not None for n in nodes],
            'salvo':True,'atores_modificados':False,
            'limite':'material nativo salvo; ainda exige conferir visualmente aplicado e escala UV; nao certifica fisica'}
