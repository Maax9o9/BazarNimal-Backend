"""Autoregistro: escanea `features/**/di/*_module.py` y llama a `register(container)` de cada uno.

El proyecto no usa archivos __init__.py (paquetes de espacio de nombres), así que los módulos
se buscan en el sistema de archivos y se importan por su ruta con puntos.
"""

import importlib

from src.core.config.settings import BASE_DIR, SRC_DIR
from src.core.di.container import Container
from src.core.logger.logger import get_logger

logger = get_logger("di")

FEATURES_DIR = SRC_DIR / "features"


def discover_modules() -> list[str]:
    files = sorted(path for path in FEATURES_DIR.rglob("*_module.py") if path.parent.name == "di")
    return [".".join(path.relative_to(BASE_DIR).with_suffix("").parts) for path in files]


def autoload_modules(container: Container) -> list[str]:
    loaded: list[str] = []
    for name in discover_modules():
        module = importlib.import_module(name)
        register = getattr(module, "register", None)
        if not callable(register):
            raise RuntimeError(f"El módulo {name} no define register(container)")
        register(container)
        loaded.append(name)
    logger.info("di_modules_loaded", extra={"modules": loaded})
    return loaded
