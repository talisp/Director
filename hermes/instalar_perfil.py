"""Instala as instruções do operador (SOUL.md e a skill `director`) num perfil do Hermes.

O repositório é a fonte: os arquivos daqui têm marcadores ({{DIRECTOR}}, {{PYTHON}}) que este
programa troca pelos caminhos desta máquina. O arquivo que já estava no perfil é guardado ao
lado, com a data no nome, antes de ser substituído (o Hermes edita a skill sozinho; compare antes
de trazer uma mudança dele para cá).

Uso, na raiz do Director, com o Python que roda o Director:
  python hermes/instalar_perfil.py [perfil]      (padrão: director)
"""
import io
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
ARQUIVOS = ("SOUL.md", os.path.join("skills", "director", "SKILL.md"))


def pasta_do_perfil(nome: str) -> str:
    base = os.environ.get("HERMES_HOME") or os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "hermes")
    return os.path.join(base, "profiles", nome)


def preencher(texto: str) -> str:
    texto = texto.replace("{{DIRECTOR}}", RAIZ.replace("\\", "/"))
    return texto.replace("{{PYTHON}}", sys.executable.replace("\\", "/"))


def main(argv: list) -> int:
    perfil = pasta_do_perfil(argv[0] if argv else "director")
    if not os.path.isdir(perfil):
        print(f"perfil não encontrado: {perfil}\ncrie antes: hermes profile create director --no-skills")
        return 2
    carimbo = time.strftime("%Y%m%d-%H%M%S")
    for rel in ARQUIVOS:
        novo = preencher(io.open(os.path.join(AQUI, rel), encoding="utf-8").read())
        destino = os.path.join(perfil, rel)
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        if os.path.exists(destino):
            velho = io.open(destino, encoding="utf-8").read()
            if velho == novo:
                print(f"igual: {rel}")
                continue
            os.replace(destino, f"{destino}.bak-{carimbo}")
        io.open(destino, "w", encoding="utf-8", newline="\n").write(novo)
        print(f"instalado: {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
