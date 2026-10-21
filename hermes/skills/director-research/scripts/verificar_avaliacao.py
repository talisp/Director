#!/usr/bin/env python3
"""Valida a forma da avaliação e dos experimentos. Não julga se a nota está certa (isso exigiria reler o código
pesquisado); só cobra que as notas que mais enganam digam o caminho real e a prova certa."""
from __future__ import annotations
import re
import sys
from pathlib import Path

SCOPE = {"DENTRO_ESCOPO", "FORA_ESCOPO", "INCERTO"}
EVIDENCE = {"ALEGADO", "CODIGO", "TESTE_ISOLADO", "UNREAL", "NAO_VERIFICADO"}
# notas que a v0.1 deu sem o caminho real (auditoria de 16/10, CityGenerator): positivas só com "caminho:" na justificativa
COM_CAMINHO = {10: "a entrada em linguagem natural e a operação que ela provoca",
               11: "o que sai do Unreal e quem recebe",
               13: "o resultado entregue à LLM e a segunda decisão dela"}
MEDIDA_PROPRIA = {"TESTE_ISOLADO", "UNREAL"}  # 16: tempo publicado pelo autor não é medição
REVISAO_MINIMA = 5
RESULTADO = re.compile(r"Resultado:\s*(\d+)\s*PASS\s*·\s*(\d+)\s*FAIL\s*·\s*(\d+)\s*OBSERVA[ÇC][ÃA]O\s*·\s*(\d+)\s*N[ÃA]O TESTADO", re.I)


def check(path: Path) -> list[str]:
    errors = []
    content = path.read_text(encoding="utf-8")
    rows = {}
    for line in content.splitlines():
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cols or not re.fullmatch(r"\d{1,2}", cols[0]):
            continue
        ident = int(cols[0])
        if ident < 1 or ident > 17:
            errors.append(f"ID inesperado: {ident}")
            continue
        if ident in rows:
            errors.append(f"Critério repetido: {ident:02}")
        rows[ident] = cols
        if len(cols) != 6:
            errors.append(f"Linha {ident:02} deve ter 6 campos, recebeu {len(cols)}")
            continue
        _, title, score, scope, evidence, reason = cols
        if not title:
            errors.append(f"{ident:02}: nome vazio")
        if score != "?":
            if not re.fullmatch(r"\d{1,2}", score) or not (0 <= int(score) <= 10):
                errors.append(f"{ident:02}: nota inválida: {score!r}")
                continue
        if scope not in SCOPE:
            errors.append(f"{ident:02}: escopo inválido: {scope!r}")
        if evidence not in EVIDENCE:
            errors.append(f"{ident:02}: evidência inválida: {evidence!r}")
        if len(reason) < 12 or reason.strip("-— ") == "":
            errors.append(f"{ident:02}: justificar com evidência concreta")
        if score == "?":
            if evidence not in ("NAO_VERIFICADO", "ALEGADO"):
                errors.append(f"{ident:02}: nota ? leva NAO_VERIFICADO (ou ALEGADO, quando só o autor afirma)")
            continue
        if evidence == "NAO_VERIFICADO":
            errors.append(f"{ident:02}: nota numérica não pode ter NAO_VERIFICADO")
        if evidence == "ALEGADO":
            errors.append(f"{ident:02}: alegação do autor não sustenta nota numérica; use ? com ALEGADO")
        n = int(score)
        if n > 0 and ident in COM_CAMINHO and "caminho:" not in reason.lower():
            errors.append(f"{ident:02}: nota {n} precisa de 'caminho:' na justificativa ({COM_CAMINHO[ident]}); "
                          "se não achou o caminho, use 0 (ausente no fluxo rastreado) ou ?")
        if ident == 13 and n > 0 and "llm" not in reason.lower():
            errors.append("13: nota positiva exige que o caminho chegue a uma LLM (correção automática sem LLM é 0)")
        if ident == 16 and n > 0 and evidence not in MEDIDA_PROPRIA:
            errors.append(f"16: nota {n} exige medição própria (TESTE_ISOLADO ou UNREAL); tempo publicado pelo autor fica ?")
    missing = sorted(set(range(1, 18)) - set(rows))
    if missing:
        errors.append("IDs ausentes: " + ", ".join(f"{x:02}" for x in missing))
    real_scores = sum(1 for cols in rows.values() if len(cols) == 6 and cols[2] != "?")
    if real_scores < 3:
        errors.append("Ao menos três critérios precisam ter nota fundamentada para concluir o dossiê")
    if "## Para o Talis" in content:
        para = content.split("## Para o Talis", 1)[1].split("\n## ", 1)[0]
        for rotulo in ("**Copiar:**", "**Inspirar-se:**", "**Usar:**"):
            if rotulo not in para:
                errors.append(f"Para o Talis: falta {rotulo} (escreva 'nada' se não houver)")
    if any(m in content for m in ("<owner/repo>", "<frase concreta", "<1–2 frases", "<copiar>", "<inspirar>", "<usar>", "<revisão das notas>")):
        errors.append("O cartão ainda contém marcadores de modelo não preenchidos")
    for term in ["Descoberta-chave", "Aproveitamento para Director", "Confiança da pesquisa", "Revisão crítica das notas", "Para o Talis"]:
        if term not in content:
            errors.append("Seção obrigatória ausente: " + term)
    if "Revisão crítica das notas" in content:
        trecho = content.split("Revisão crítica das notas", 1)[1].split("\n## ", 1)[0]
        revistas = {int(m) for m in re.findall(r"^\s*-\s*(\d{2})\s*:", trecho, re.M) if 1 <= int(m) <= 17}
        if len(revistas) < REVISAO_MINIMA:
            errors.append(f"Revisão crítica das notas: {len(revistas)} nota(s) revista(s); o mínimo são {REVISAO_MINIMA} "
                          "(linhas '- NN: ...', as mais importantes e as menos comprovadas)")
    return errors


def check_experimentos(path: Path) -> list[str]:
    """experimentos.md: placar com as quatro categorias e a lista de expectativas mudadas (ou 'nenhuma')."""
    if not path.is_file():
        return [f"experimentos.md ausente: {path}"]
    content = path.read_text(encoding="utf-8")
    errors = []
    if not RESULTADO.search(content):
        errors.append("experimentos.md: falta a linha 'Resultado: N PASS · N FAIL · N OBSERVAÇÃO · N NÃO TESTADO'")
    if not re.search(r"Mudanças de expectativa\s*:", content, re.I):
        errors.append("experimentos.md: falta 'Mudanças de expectativa:' (cada teste cujo esperado mudou depois de rodar: "
                      "esperava X, deu Y, porque Z; ou 'nenhuma')")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Uso: python verificar_avaliacao.py <arquivo_AVALIACAO.md>")
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print("ERRO: arquivo inexistente:", path)
        return 2
    errors = check(path) + check_experimentos(path.parent / "experimentos.md")
    if errors:
        print("AVALIAÇÃO REPROVADA:")
        for e in errors:
            print(" -", e)
        return 1
    print("AVALIAÇÃO ESTRUTURALMENTE VÁLIDA: 17 notas, caminhos nas notas 10/11/13/16, revisão de "
          f"{REVISAO_MINIMA}+ notas e placar dos experimentos. A veracidade precisa ser auditada à parte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
