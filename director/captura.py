"""Captura nativa com recorte local opcional; Pillow so e necessario para foto."""
import base64
import io
import math
from pathlib import Path
from .base.mcp_client import APP


def fotografar(ponte,sala,arquivo):
    from PIL import Image
    z=sala["z"]+max(sala["largura"],sala["comprimento"])*2
    r=ponte.cliente.call(APP,"CaptureViewport",captureTransform={
        "location":{"x":sala["x"]+sala["largura"]/2,"y":sala["y"]+sala["comprimento"]/2,"z":z},
        "rotation":{"pitch":-90,"yaw":0,"roll":0},"scale":{"x":1,"y":1,"z":1}},annotations=None,bShowUI=False)
    im=Image.open(io.BytesIO(base64.b64decode(r["image"]["data"])))
    w,h=im.size
    scale=w/(2*(z-sala["z"])*math.tan(math.radians(r["cameraFOV"]/2)))
    dx=sala["comprimento"]/2*scale;dy=sala["largura"]/2*scale
    crop=(max(0,int(w/2-dx)),max(0,int(h/2-dy)),min(w,int(w/2+dx)),min(h,int(h/2+dy)))
    alvo=Path(arquivo);alvo.parent.mkdir(parents=True,exist_ok=True)
    im.crop(crop).save(alvo)
    return {"arquivo":str(alvo),"pixels":[crop[2]-crop[0],crop[3]-crop[1]],"revisao_visual":"nao_executada"}
