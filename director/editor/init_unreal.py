"""O editor do LABORATÓRIO roda este arquivo ao abrir (a pasta vai no UE_PYTHONPATH só daquele processo).
Registra o DirectorTools. Falha aqui nunca derruba o editor: só registra no log."""
import sys

import unreal

try:
    anterior = sys.modules.get("director_tools")
    if anterior is not None and hasattr(anterior, "_registration"):
        anterior._registration.unregister()
        for m in [m for m in sys.modules if m.startswith("director_tools")]:
            del sys.modules[m]
    from director_tools import _registration

    if _registration.register():
        unreal.log("DirectorTools registrado no ToolsetRegistry")
    else:
        unreal.log_warning("DirectorTools: ToolsetRegistry indisponível (plugin desligado?)")
except Exception as e:  # noqa: BLE001
    unreal.log_error(f"DirectorTools não carregou: {e}")
