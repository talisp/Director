"""A planta: o registro declarativo do que o Director controla numa cena. Texto (JSON), versionado no git.

Não copia o estado do Unreal: guarda só os objetos lógicos (sala, porta, janela, mesa, prato, copo), cada um com
nome estável, tipo, medidas e ligações (`sala`, `sobre`). As peças do Unreal são derivadas dela (derivar.py).
"""
import json
import os
import time

FORMATO = 1


def nova(cena: str) -> dict:
    if not cena or not all(ch.isalnum() or ch == "_" for ch in cena):
        raise ValueError(f"nome de cena inválido: {cena!r} (use letras, números e _)")
    # base_z: o chão do level modelo do motor fica em z = 0; a sala assenta 1 cm acima para as faces não coincidirem
    return {"formato": FORMATO, "cena": cena, "nivel": f"/Game/Director/Cenas/L_{cena}", "base_z": 1.0, "revisao": 0, "objetos": {}}


def pasta(raiz_cenas: str, cena: str) -> str:
    return os.path.join(raiz_cenas, cena)


def caminho(raiz_cenas: str, cena: str) -> str:
    return os.path.join(raiz_cenas, cena, "planta.json")


def carregar(raiz_cenas: str, cena: str) -> dict:
    """A planta da cena; se a cena ainda não existe, uma planta vazia (revisão 0)."""
    try:
        with open(caminho(raiz_cenas, cena), encoding="utf-8") as f:
            p = json.load(f)
    except FileNotFoundError:
        return nova(cena)
    if p.get("formato") != FORMATO or p.get("cena") != cena:
        raise ValueError(f"planta de {cena!r} com formato ou nome inesperado")
    return p


def gravar(raiz_cenas: str, planta: dict) -> str:
    """Grava inteira ou não grava (arquivo temporário e troca)."""
    destino = caminho(raiz_cenas, planta["cena"])
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(planta, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, destino)
    return destino


def registrar(raiz_cenas: str, cena: str, evento: dict) -> None:
    """Uma linha no registro da cena. A linha de início é gravada ANTES de tocar no Unreal."""
    os.makedirs(pasta(raiz_cenas, cena), exist_ok=True)
    linha = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"), **evento}
    with open(os.path.join(pasta(raiz_cenas, cena), "registro.jsonl"), "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(linha, ensure_ascii=False, sort_keys=True) + "\n")
