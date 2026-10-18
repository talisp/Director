"""Vinculo explicito entre laboratorio e plantas, independente do checkout de codigo."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def resolver(lab_dir, legado, vinculo):
    """Ler nao cria estado. Vinculo invalido nunca volta silenciosamente ao legado."""
    p = Path(vinculo)
    if not p.is_file():
        return str(legado)
    dados = json.loads(p.read_text(encoding="utf-8"))
    if dados.get("formato") != 1 or Path(dados["laboratorio"]).resolve() != Path(lab_dir).resolve():
        raise ValueError("vinculo de plantas pertence a outro laboratorio ou formato")
    raiz = Path(dados["cenas"])
    if not raiz.is_absolute() or not raiz.is_dir():
        raise ValueError("fonte de plantas vinculada ausente; nao usar uma copia antiga como fallback")
    return str(raiz)


def vincular(origem, editor, lab_dir, vinculo):
    """Confere todas as plantas e copia para Saved/Director. Nao modifica atores nem plantas fonte.

    Publica o vinculo por ultimo. Qualquer falha deixa o vinculo anterior intacto.
    Requer a trava da Ponte. Nao escolhe revisoes por data ou numero.
    """
    from .nucleo import planta as PL, derivar as D, plano as PN, pecas as P
    origem = Path(origem).resolve()
    manifesto = Path(vinculo)
    destino = manifesto.parent / "cenas"
    if manifesto.exists() or destino.exists():
        raise ValueError("estado compartilhado ja existe; confira-o, sem substituir automaticamente")
    fontes = sorted(origem.glob("*/planta.json"))
    if not fontes:
        raise ValueError("origem sem plantas")
    inicio = editor.chamar("info")
    if inicio["em_play"] or inicio.get("por_salvar") or not inicio.get("level"):
        raise ValueError("salve e pare o Play antes de vincular plantas")
    verificadas = []
    try:
        for arquivo in fontes:
            bruto = arquivo.read_bytes()
            planta = PL.carregar(str(origem), arquivo.parent.name)
            if not planta["nivel"].startswith("/Game/Director/Cenas/L_"):
                raise ValueError("level fora das cenas do Director")
            editor.chamar("level_ensure", caminho=planta["nivel"], criar=False)
            inv = editor.chamar("inventory", variaveis=P.variaveis())
            if inv.get("por_salvar"):
                raise ValueError("level com alteracoes nao salvas; vinculacao recusada")
            diferencas = PN.diferencas(D.derivar(planta), inv["controlados"])
            if diferencas:
                return {"ok": False, "motivo": "planta_editor_divergentes", "cena": planta["cena"],
                        "planta": str(arquivo), "diferencas": diferencas, "vinculo_ativado": False}
            verificadas.append((arquivo, bruto, planta))
    finally:
        editor.chamar("level_ensure", caminho=inicio["level"], criar=False)
    # Nao publicar uma planta que mudou enquanto era verificada.
    if any(arq.read_bytes() != bruto for arq, bruto, _ in verificadas):
        raise ValueError("fonte mudou durante a verificacao; vinculacao recusada")
    manifesto.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=manifesto.parent, prefix="vincular-") as tmp:
        preparada = Path(tmp) / "cenas"
        preparada.mkdir()
        evidencias = []
        for arquivo, bruto, planta in verificadas:
            pasta = preparada / planta["cena"]
            pasta.mkdir()
            (pasta / "planta.json").write_bytes(bruto)
            registro = arquivo.with_name("registro.jsonl")
            if registro.is_file():
                shutil.copy2(registro, pasta / "registro.jsonl")
            evidencias.append({"cena": planta["cena"], "revisao": planta["revisao"],
                "origem": str(arquivo), "sha256": hashlib.sha256(bruto).hexdigest(), "diferencas": 0})
        dados = {"formato": 1, "laboratorio": str(Path(lab_dir).resolve()),
                 "cenas": str(destino.resolve()), "migracao": evidencias}
        temporario = Path(tmp) / "vinculo.json"
        temporario.write_text(json.dumps(dados, ensure_ascii=True, indent=2), encoding="utf-8")
        os.rename(preparada, destino)  # recusa se apareceu outro destino; nunca substitui plantas
        # Publicacao atomica e exclusiva no mesmo volume (NTFS no Windows).
        # Falha preserva o destino para diagnostico, sem ativar vinculo parcial.
        os.link(temporario, manifesto)
    return {"ok": True, "vinculo": str(manifesto), "cenas": str(destino), "verificadas": evidencias,
            "fontes_preservadas": True, "nivel_restaurado": inicio["level"]}
