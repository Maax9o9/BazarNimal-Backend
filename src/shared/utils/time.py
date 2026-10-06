from datetime import UTC, datetime


def utcnow() -> datetime:
    """Fecha y hora UTC sin zona horaria (la base de datos guarda UTC)."""
    return datetime.now(UTC).replace(tzinfo=None)
