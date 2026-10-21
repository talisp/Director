#!/usr/bin/env python3
"""Teste isolado dos scripts da skill (pasta temporária); não importa nem modifica o Director.
Cada defeito achado na auditoria de 16/10 tem um caso aqui que reprovava na v0.1."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CARD = HERE.parent / "templates" / "AVALIACAO.md"
sys.path.insert(0, str(HERE))
from verificar_avaliacao import check, check_experimentos  # noqa: E402
from medir_contexto import medir  # noqa: E402


def run(root, *parts, ok=True, env=None):
    cmd = [sys.executable, str(HERE / "fila.py"), "--root", str(root), *parts]
    ret = subprocess.run(cmd, text=True, capture_output=True, encoding="utf-8", env=env)
    if ok and ret.returncode:
        raise AssertionError(f"FAIL cmd={cmd} stdout={ret.stdout} stderr={ret.stderr}")
    if not ok and not ret.returncode:
        raise AssertionError(f"Expected failure cmd={cmd} stdout={ret.stdout}")
    return ret


def cartao(nome: str, linhas: dict, revisao: int = 5, foco: bool = False, para=True) -> str:
    """O modelo preenchido: `linhas` = {id: "| nota | escopo | evidência | justificativa |"}."""
    t = CARD.read_text(encoding="utf-8").replace("<owner/repo>", nome)
    t = t.replace("<frase concreta sobre engenharia, com E#>", "Teste mostra três funções implementadas — E01")
    t = t.replace("<1–2 frases sem marketing>", "Implementa algoritmo de teste")
    for num, resto in linhas.items():
        linha = next(x for x in t.splitlines() if x.startswith(f"| {num:02} |"))
        partes = linha.split("|")
        t = t.replace(linha, "|".join(partes[:3]) + "|" + resto)
    rev = "\n".join(f"- {n:02}: nota revista contra o código, mantida porque E01 confirma" for n in range(1, revisao + 1))
    if para:
        t = t.replace("<copiar>", "a função de fila atômica (E03), MIT").replace("<inspirar>", "checkpoints com o que falta")
        t = t.replace("<usar>", "nada")
    if foco:
        t = t.replace("**Resposta ao foco:** (só se", "**Resposta ao foco:** eles coordenam por regras e CI. (só se")
    else:
        t = t.replace("**Resposta ao foco:**", "Foco: nenhum pedido.")
    return t.replace("<revisão das notas>", rev)


BOAS = {1: " 5 | DENTRO_ESCOPO | CODIGO | E01 mostra o planejamento |", 2: " 5 | DENTRO_ESCOPO | CODIGO | E02 mostra a planta |",
        3: " 5 | DENTRO_ESCOPO | CODIGO | E03 mostra a geometria |"}
EXPERIMENTOS_OK = "# Experimentos\n\nResultado: 9 PASS · 0 FAIL · 2 OBSERVAÇÃO · 1 NÃO TESTADO\n\nMudanças de expectativa: nenhuma\n"


def avaliacao(tmp: Path, linhas: dict, revisao: int = 5) -> list:
    p = tmp / "AVALIACAO.md"
    p.write_text(cartao("ExampleOwner/Test-Repo", linhas, revisao), encoding="utf-8")
    return check(p)


def testes_do_verificador(tmp: Path) -> None:
    assert avaliacao(tmp, BOAS) == [], avaliacao(tmp, BOAS)
    # as três notas que a auditoria achou erradas no CityGenerator têm de reprovar
    casos = {
        "10 sem caminho (guia para outro agente lido como função)": {10: " 3 | DENTRO_ESCOPO | CODIGO | CLAUDE.md ensina o agente |"},
        "13 sem LLM (correção matemática não é segunda decisão)": {13: " 4 | DENTRO_ESCOPO | CODIGO | caminho: medir → ajustar → refazer, automático |"},
        "16 com tempo do autor": {16: " 5 | DENTRO_ESCOPO | CODIGO | README diz 30–60 min de cook |"},
        "nota numérica só com alegação": {6: " 7 | DENTRO_ESCOPO | ALEGADO | o autor diz que gera prédios |"},
    }
    for nome, extra in casos.items():
        assert avaliacao(tmp, {**BOAS, **extra}), f"tinha de reprovar: {nome}"
    # e as versões com prova passam
    certas = {10: " 0 | FORA_ESCOPO | CODIGO | sem entrada em linguagem natural no fluxo rastreado (E05) |",
              13: " 6 | DENTRO_ESCOPO | CODIGO | caminho: resultado da ferramenta volta à LLM em agent.py:88, nova chamada |",
              16: " 6 | DENTRO_ESCOPO | TESTE_ISOLADO | medi 12 s em EXP04, três repetições |",
              6: " ? | INCERTO | ALEGADO | o autor diz que gera prédios; não rodei |"}
    assert avaliacao(tmp, {**BOAS, **certas}) == [], avaliacao(tmp, {**BOAS, **certas})
    assert avaliacao(tmp, BOAS, revisao=4), "revisão crítica com 4 notas tinha de reprovar"
    p = tmp / "AVALIACAO.md"
    p.write_text(cartao("ExampleOwner/Test-Repo", BOAS, para=False), encoding="utf-8")
    assert check(p), "Para o Talis sem preencher (copiar/inspirar-se/usar) tinha de reprovar"
    e = tmp / "experimentos.md"
    e.write_text(EXPERIMENTOS_OK, encoding="utf-8")
    assert check_experimentos(e) == []
    e.write_text("# Experimentos\n\nTOTAL 34 checks, 0 FAIL\n", encoding="utf-8")
    assert len(check_experimentos(e)) == 2, "placar só com PASS e sem mudanças de expectativa tinha de reprovar"


def testes_da_fila(tmp: Path) -> None:
    root = tmp / "estudos"
    falso = tmp / "repo_protegido"
    subprocess.run(["git", "init", "-q", str(falso)], check=True)
    (falso / "ja_existia.txt").write_text("x", encoding="utf-8")
    env = {**os.environ, "DIRECTOR_RESEARCH_PROTEGIDOS": str(falso)}
    a = "https://github.com/ExampleOwner/Test-Repo"
    b = "https://github.com/AlexKorotkin-creator/CityGenerator"
    c = "https://github.com/Other/Third"
    run(root, "init", env=env)
    run(root, "add", a, "--foco", "nesse link pesquise sobre X, ele não tem 3d, mas vai ajudar a parte Y e Z", env=env)
    run(root, "add", a, b, c, env=env)
    run(root, "add", a.upper().replace("HTTPS://", "https://"), env=env)
    data = json.loads((root / "fila.json").read_text(encoding="utf-8"))
    assert len(data["items"]) == 3, data
    run(root, "foco", c, "como coordenam vários agentes", env=env)
    out = run(root, "next", env=env).stdout
    assert "Test-Repo" in out and "FOCO: nesse link pesquise sobre X" in out, out
    out = run(root, "begin", a, env=env).stdout
    assert "BASELINE" in out and "1 entradas" in out, out
    item = json.loads((root / "fila.json").read_text(encoding="utf-8"))["items"][0]
    assert item["skill"]["versao"] and "SKILL.md" in item["skill"]["hashes"], item.get("skill")
    run(root, "checkpoint", a, "P3: planejando pré-execução", ok=False, env=env)  # sem feito/falta/arquivos
    for n in (1, 2, 3):
        out = run(root, "checkpoint", a, f"feito: marco {n} | falta: o resto, medir contexto | arquivos: estado.md", env=env).stdout
        assert "CONTINUE" in out, out
    # 16/10: a v0.2 parou alegando contexto (200–240 mil de 1 milhão); checkpoint de pausa por contexto é recusado
    run(root, "checkpoint", a, "feito: x | falta: y | arquivos: z | motivo de pausa: limite real de contexto", ok=False, env=env)
    assert "EM_ANALISE" in run(root, "status", env=env).stdout
    run(root, "begin", b, ok=False, env=env)  # não processar dois ao mesmo tempo
    run(root, "finish", a, ok=False, env=env)  # exigir arquivos
    report = root / "repositorios" / "exampleowner--test-repo"
    report.mkdir(parents=True)
    (report / "AVALIACAO.md").write_text(cartao("ExampleOwner/Test-Repo", BOAS), encoding="utf-8")
    for name in ("analise.md", "evidencias.md", "estado.md"):
        (report / name).write_text("# Conteúdo de teste\n", encoding="utf-8")
    (report / "experimentos.md").write_text("# Experimentos\n\nTOTAL 34 checks, 0 FAIL\n", encoding="utf-8")
    run(root, "finish", a, ok=False, env=env)  # placar sem as quatro categorias
    (report / "experimentos.md").write_text(EXPERIMENTOS_OK, encoding="utf-8")
    run(root, "finish", a, ok=False, env=env)  # o Talis pediu foco e a avaliação não responde
    (report / "AVALIACAO.md").write_text(cartao("ExampleOwner/Test-Repo", BOAS, foco=True), encoding="utf-8")
    (falso / "novo_durante.txt").write_text("y", encoding="utf-8")
    out = run(root, "finish", a, env=env).stdout
    # finish manda começar o próximo e mede o git (sem bloquear)
    assert "PRÓXIMO DA FILA: " + b in out and "FAÇA AGORA" in out, out
    assert "MUDOU durante a pesquisa" in out and "novo_durante.txt" in out, out
    pain = (root / "PAINEL.md").read_text(encoding="utf-8")
    assert "**Copiar:** a função de fila atômica" in pain and "O que você pediu:** nesse link" in pain, pain
    assert "Ainda na fila" in pain and "como coordenam vários agentes" in pain, pain
    # PARCIAL: o next retoma antes de avançar para o pendente (a v0.1 ignorava e o teste antigo aceitava)
    run(root, "begin", b, env=env)
    run(root, "partial", b, "Acesso ao Editor não disponível", ok=False, env=env)  # sem o tipo da parada
    run(root, "partial", b, "cansaco", "sessão longa", ok=False, env=env)  # tipo inexistente
    run(root, "partial", b, "ferramenta", "contexto em ~241k tokens; dossiê frágil", ok=False, env=env)  # o caso real
    run(root, "partial", b, "ferramenta", "Acesso ao Editor não disponível", env=env)
    out = run(root, "next", env=env).stdout
    assert "CityGenerator" in out and "PARCIAL" in out and "RETOMAR" in out, out
    out = run(root, "begin", b, env=env).stdout
    assert "INICIADO/RETOMADO" in out and "CHECKPOINT ANTERIOR" in out and "PARCIAL: ferramenta: Acesso" in out, out
    # skill mudou entre o começo e a retomada: avisa
    data = json.loads((root / "fila.json").read_text(encoding="utf-8"))
    data["items"][1]["skill"]["hashes"]["SKILL.md"] = "000000000000"
    (root / "fila.json").write_text(json.dumps(data), encoding="utf-8")
    run(root, "partial", b, "decisao", "pausa", env=env)
    assert "AVISO: a skill mudou" in run(root, "begin", b, env=env).stdout
    run(root, "partial", b, "chamadas", "pausa", env=env)
    assert "FOCO: como coordenam" not in run(root, "next", env=env).stdout  # o parcial vem antes
    # raiz dentro de repositório protegido: recusada pelo caminho inteiro, não só pelo último nome
    for dentro in (tmp / "Director" / "work" / "estudos", tmp / "unreal-macros" / "x", falso / "estudos"):
        run(dentro, "status", ok=False, env=env)
        assert not dentro.exists(), f"criou pasta dentro do protegido: {dentro}"


def testes_do_contexto() -> None:
    log = []
    for n, tam in enumerate((20000, 60000, 160000, 170000), 1):
        log.append(f"x INFO [local-abc] agent.conversation_loop: API call #{n}: model=q provider=c in={tam} out=10 total=1")
    log.insert(4, 'x WARNING [local-abc] agent.tool_executor: Tool write_file returned error (0.00s): {"error": "write_file: missing required field"}')
    log.insert(2, 'x WARNING [local-abc] agent.tool_executor: Tool terminal returned error (1s): {"output": "AVALIAÇÃO REPROVADA"}')
    log.append("x INFO [local-outra] agent.conversation_loop: API call #1: model=q provider=c in=999 out=1 total=1")
    r = medir(log, "local-abc", 50000)
    assert r["chamadas"] == 4 and r["contexto_max"] == 170000, r
    faixas = {f["de"]: f for f in r["faixas"]}
    assert faixas[150000]["uso"] == 1 and faixas[0]["uso"] == 0, faixas
    # o erro de resultado vem logo depois da 2ª chamada (60 mil tokens): conta na faixa 50–100 mil, não como uso
    assert faixas[50000]["resultado"] == 1 and faixas[50000]["uso"] == 0, faixas
    assert medir(log, None, 50000)["sessao"] == "local-outra"  # sem sessão: a última do log


def main():
    with tempfile.TemporaryDirectory(prefix="director-research-test-") as tmp:
        tmp = Path(tmp)
        testes_do_verificador(tmp)
        testes_da_fila(tmp)
        testes_do_contexto()
    print("PASS: fila (PARCIAL retomado, finish manda seguir, checkpoints com feito/falta/arquivos, versão da skill, "
          "git medido), raiz protegida pelo caminho inteiro, notas 10/13/16 e alegação, revisão de 5 notas, placar dos "
          "experimentos, medição do contexto.")


if __name__ == "__main__":
    main()
