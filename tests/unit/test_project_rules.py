"""Reglas del proyecto que se verifican en cada corrida de pruebas."""

from src.core.config.settings import BASE_DIR


def test_no_init_files():
    """El proyecto usa paquetes de espacio de nombres: no se permiten archivos __init__.py."""
    found = [
        str(path.relative_to(BASE_DIR))
        for folder in ("src", "tests")
        for path in (BASE_DIR / folder).rglob("__init__.py")
    ]
    assert found == [], f"Elimina estos __init__.py: {found}"
