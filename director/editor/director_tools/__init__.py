"""Ferramentas do Director dentro do editor do laboratório (ver toolset.py e ops.py)."""
from toolset_registry.registration import Registration

from .toolset import DirectorTools

_registration = Registration([DirectorTools])
