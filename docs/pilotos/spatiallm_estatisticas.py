import json,csv,zipfile,collections,math,statistics
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Piloto offline SpatialLM: dados locais, sem inferencia, rede ou Unreal')
parser.add_argument('pasta',type=Path,help='pasta contendo spatiallm/split.csv, spatiallm/layout/chunk_000.zip e spatiallm-versao.json')
root=parser.parse_args().pasta
# Leitor independente restrito a dados; nao executa o leitor oficial (SciPy ausente).
from types import SimpleNamespace as N
import re
class Layout:
 def __init__(self,txt):
  self.walls=[];self.doors=[];self.windows=[];self.bboxes=[]
  for line in txt.splitlines():
   if not line.strip():continue
   m=re.fullmatch(r'(wall|door|window|bbox)_(\d+)=(Wall|Door|Window|Bbox)\(([^()]*)\)',line.strip())
   if not m:raise ValueError('linha fora da gramatica restrita')
   typ,ident,cl,args=m.groups();vals=[v.strip() for v in args.split(',')]
   if {'wall':'Wall','door':'Door','window':'Window','bbox':'Bbox'}[typ]!=cl:raise ValueError('tipo divergente')
   expected={'wall':8,'door':6,'window':6,'bbox':8}[typ]
   if len(vals)!=expected:raise ValueError('quantidade de campos divergente')
   nums=[float(v) for v in vals[(0 if typ=='wall' else 1):]]
   if not all(math.isfinite(v) for v in nums):raise ValueError('numero nao finito')
   if typ=='wall':obj=N()
   else:obj=N(position_x=nums[0],position_y=nums[1],position_z=nums[2])
   if typ=='bbox':obj.class_name=vals[0]
   getattr(self,{'wall':'walls','door':'doors','window':'windows','bbox':'bboxes'}[typ]).append(obj)
 def get_entities(self):return self.walls+self.doors+self.windows+self.bboxes
 def translate(self,v):
  for e in self.doors+self.windows+self.bboxes:e.position_x+=v[0];e.position_y+=v[1];e.position_z+=v[2]
 def rotate(self,a):
  for e in self.doors+self.windows+self.bboxes:
   x,y=e.position_x,e.position_y;e.position_x=x*math.cos(a)-y*math.sin(a);e.position_y=x*math.sin(a)+y*math.cos(a)
metadata={}
with (root/'spatiallm/split.csv').open(encoding='utf-8',newline='') as f:
 for r in csv.DictReader(f):metadata[r['id']]=r
quartos={};falhas=[];classes=collections.Counter();variacoes=[]
with zipfile.ZipFile(root/'spatiallm/layout/chunk_000.zip') as z:
 infos=z.infolist()
 if sum(i.file_size for i in infos)>16*1024*1024:raise RuntimeError('lote excede limite descomprimido')
 for i in infos:
  if not i.filename.endswith('.txt'):continue
  ident=Path(i.filename).stem;meta=metadata.get(ident)
  if not meta:falhas.append({'id':ident,'erro':'sem metadata'});continue
  key=(meta['scene_id'],meta['room_id'])
  # Cada quarto tem ate quatro amostragens. Preferir menor sample; nao inflar n.
  txt=z.read(i).decode('utf-8');layout=Layout(txt)
  esperado=sum(l.startswith(('wall_','door_','window_','bbox_')) for l in txt.splitlines())
  if len(layout.get_entities())!=esperado:falhas.append({'id':ident,'erro':'leitor descartou linhas','esperado':esperado,'obtido':len(layout.get_entities())});continue
  if key in quartos and int(quartos[key]['sample'])<=int(meta['sample']):continue
  camas=[b for b in layout.bboxes if b.class_name.strip().lower()=='bed']
  ds=[min(math.hypot(b.position_x-d.position_x,b.position_y-d.position_y) for d in layout.doors) for b in camas] if layout.doors else []
  quartos[key]={'id':ident,'sample':meta['sample'],'tipo':meta['room_type'],'janelas':len(layout.windows),'portas':len(layout.doors),'camas':len(camas),'distancias_centros_xy':ds}
  if ds and not variacoes:

   layout.translate([2.0,-3.0,0.0]);depois=[min(math.hypot(b.position_x-d.position_x,b.position_y-d.position_y) for d in layout.doors) for b in camas]
   layout.rotate(math.pi/2);girado=[min(math.hypot(b.position_x-d.position_x,b.position_y-d.position_y) for d in layout.doors) for b in camas]
   variacoes=[{'id':ident,'teste':'translacao','erro_max':max(abs(a-b) for a,b in zip(ds,depois))}, {'id':ident,'teste':'rotacao_90','erro_max':max(abs(a-b) for a,b in zip(ds,girado))}]
rooms=list(quartos.values());bedrooms=[q for q in rooms if 'bedroom' in q['tipo'].lower()];ds=[d for q in bedrooms for d in q['distancias_centros_xy']]
resultado={'dataset_revision':json.loads((root/'spatiallm-versao.json').read_bytes())['sha'],'code_revision':'8913c44d84a450c53e9340b13317f8cf7144a738','arquivos_layout':len(infos),'quartos_unicos':len(rooms),'tipos_quartos':dict(collections.Counter(q['tipo'] for q in rooms)),'criterio_dormitorio':'room_type contem bedroom; guest room e child room nao incluidos', 'dormitorios':len(bedrooms),'dormitorios_com_janela':sum(q['janelas']>0 for q in bedrooms),'dormitorios_com_porta':sum(q['portas']>0 for q in bedrooms),'dormitorios_com_cama':sum(q['camas']>0 for q in bedrooms),'distancia_centro_cama_porta_xy':{'n':len(ds),'mediana':statistics.median(ds) if ds else None,'minimo':min(ds) if ds else None,'maximo':max(ds) if ds else None,'unidade':'unidade nativa layout; conversao metrica nao validada neste piloto','limite':'centro a centro em XY, nao passagem livre nem caminho navegavel'},'falhas':falhas,'variacoes':variacoes,'escopo':'primeiro chunk; amostra nao aleatoria, nao estatistica populacional','licenca_dados':'CC-BY-NC-4.0','leitor':'independente restrito; leitor oficial nao executado por falta de SciPy; codigo oficial tem LicenseRef-Llama-3.2-Community e nao foi incorporado'}
(root/'spatiallm-estatisticas.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2),encoding='utf-8');(root/'spatiallm-quartos.json').write_text(json.dumps(rooms,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(resultado,ensure_ascii=True)[:3200])
