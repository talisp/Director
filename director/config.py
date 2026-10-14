"""Endereços do Director. O laboratório é um projeto do Unreal separado do projeto do filme, com porta própria.
Tudo pode ser trocado por variável de ambiente; nada aqui depende da máquina."""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LAB_DIR = os.environ.get("DIRECTOR_LAB_DIR", os.path.join(os.path.expanduser("~"), "unreal-director-lab"))
LAB_NOME = "DirectorLab"
LAB_UPROJECT = os.path.join(LAB_DIR, LAB_NOME + ".uproject")
LAB_PORTA = int(os.environ.get("DIRECTOR_LAB_PORTA", "8011"))  # a 8001 é a do projeto do filme: nunca apontar para ela
LAB_URL = f"http://127.0.0.1:{LAB_PORTA}/mcp"
EDITOR_EXE = os.environ.get("DIRECTOR_EDITOR_EXE", r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe")
EDITOR_PYTHON = os.path.join(RAIZ, "director", "editor")  # vai no UE_PYTHONPATH só do processo do laboratório

WORK = os.path.join(RAIZ, "work")  # fora do git: trava, estado do laboratório, pontos de restauração, medidas
TRAVA = os.path.join(WORK, "unreal_lab.trava")  # um operador por vez no laboratório
TRAVA_LOG = os.path.join(WORK, "trava.jsonl")
LAB_ESTADO = os.path.join(WORK, "lab_editor.json")
CENAS = os.path.join(RAIZ, "director", "cenas")  # plantas (texto, versionadas no git)

PASTA_UNREAL = "/Game/Director"  # o único lugar do projeto em que o Director grava
