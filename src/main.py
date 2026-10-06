"""Punto de entrada del backend.

    .\\.venv\\Scripts\\python.exe src/main.py

Host, puerto, recarga automática y proxies confiables se configuran en el .env
(APP_HOST, APP_PORT, APP_RELOAD, FORWARDED_ALLOW_IPS).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    # Al ejecutar `python src/main.py` Python solo agrega src/ al path; los imports usan `src.`.
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn  # noqa: E402

from src.core.config.settings import get_settings  # noqa: E402
from src.core.server.app import create_app  # noqa: E402

app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        # Con recarga, uvicorn necesita la ruta de importación en lugar del objeto.
        "src.main:app" if settings.app_reload else app,
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_reload,
        reload_dirs=[str(PROJECT_ROOT / "src")] if settings.app_reload else None,
        app_dir=str(PROJECT_ROOT),
        proxy_headers=True,
        forwarded_allow_ips=settings.forwarded_allow_ips,
        server_header=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
