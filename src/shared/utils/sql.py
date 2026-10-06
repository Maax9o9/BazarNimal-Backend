LIKE_ESCAPE = "!"


def like_pattern(term: str) -> str:
    """Patrón para LIKE con los comodines del usuario escapados. Usar con `escape=LIKE_ESCAPE`."""
    escaped = term.replace("!", "!!").replace("%", "!%").replace("_", "!_")
    return f"%{escaped}%"
