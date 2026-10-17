"""Inspecao FBX em processo Blender separado, sem abrir UI nem Unreal."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
entrada,saida=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
r=bpy.ops.import_scene.fbx(filepath=entrada)
if 'FINISHED' not in r:raise RuntimeError('importacao FBX nao terminou')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
pts=[o.matrix_world @ Vector(v) for o in meshes for v in o.bound_box]
if not pts:raise ValueError('FBX sem geometria')
lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
scale=bpy.context.scene.unit_settings.scale_length*100
result={'dimensoes_cm':[(b-a)*scale for a,b in zip(lo,hi)],'centro_cm':[(a+b)*scale/2 for a,b in zip(lo,hi)],
 'triangulos':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes),
 'materiais':len(bpy.data.materials),'texturas':len(bpy.data.images),
 'dependencias_ausentes':[im.filepath for im in bpy.data.images if not im.packed_file and im.filepath and not Path(bpy.path.abspath(im.filepath)).is_file()],
 'unidades':'cm apos importador FBX; eixos Blender XYZ, Z para cima','backend':'Blender '+bpy.app.version_string}
Path(saida).write_text(json.dumps(result,ensure_ascii=True),encoding='utf-8')
