"""Contenedor de inyección de dependencias con autowiring por type hints.

- singleton: una instancia para toda la aplicación (pool de BD, logger, configuración).
- scoped: una instancia por petición HTTP (sesión de BD, repositorios).
- transient: una instancia nueva cada vez que se resuelve (casos de uso, controladores).
"""

import inspect
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, TypeVar, get_type_hints

T = TypeVar("T")

Disposer = Callable[[Any], Awaitable[None] | None]


class Lifetime(StrEnum):
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


class DependencyError(RuntimeError):
    pass


class _Registration:
    __slots__ = ("provider", "lifetime", "dispose")

    def __init__(self, provider: Callable[..., Any], lifetime: Lifetime, dispose: Disposer | None) -> None:
        self.provider = provider
        self.lifetime = lifetime
        self.dispose = dispose


class Container:
    def __init__(self) -> None:
        self._registrations: dict[Any, _Registration] = {}
        self._singletons: dict[Any, Any] = {}

    def register(
        self,
        key: Any,
        provider: Callable[..., Any] | None = None,
        *,
        lifetime: Lifetime = Lifetime.TRANSIENT,
        dispose: Disposer | None = None,
    ) -> None:
        """Registra `key` (normalmente una interfaz) con su implementación o fábrica."""
        if key in self._registrations:
            raise DependencyError(f"{_name(key)} ya está registrado")
        self._registrations[key] = _Registration(provider or key, lifetime, dispose)

    def register_instance(self, key: Any, instance: Any) -> None:
        self.register(key, lambda: instance, lifetime=Lifetime.SINGLETON)
        self._singletons[key] = instance

    def override(self, key: Any, provider: Callable[..., Any], *, lifetime: Lifetime = Lifetime.TRANSIENT) -> None:
        """Reemplaza un registro existente (útil en pruebas)."""
        self._registrations[key] = _Registration(provider, lifetime, None)
        self._singletons.pop(key, None)

    def is_registered(self, key: Any) -> bool:
        return key in self._registrations

    def create_scope(self) -> "Scope":
        return Scope(self)

    def resolve(self, key: type[T]) -> T:
        """Resuelve fuera de una petición. No permite dependencias `scoped`."""
        return Scope(self, allow_scoped=False).resolve(key)


class Scope:
    def __init__(self, container: Container, *, allow_scoped: bool = True) -> None:
        self._container = container
        self._allow_scoped = allow_scoped
        self._instances: dict[Any, Any] = {}
        self._disposables: list[tuple[Any, Disposer]] = []

    def resolve(self, key: type[T], _chain: tuple[Any, ...] = ()) -> T:
        if key in _chain:
            cycle = " -> ".join(_name(k) for k in (*_chain, key))
            raise DependencyError(f"Dependencia circular: {cycle}")
        registration = self._container._registrations.get(key)
        if registration is None:
            raise DependencyError(f"{_name(key)} no está registrado en el contenedor")

        chain = (*_chain, key)
        match registration.lifetime:
            case Lifetime.SINGLETON:
                singletons = self._container._singletons
                if key not in singletons:
                    # Un singleton nunca puede capturar dependencias de una petición.
                    root = Scope(self._container, allow_scoped=False)
                    singletons[key] = root._build(registration.provider, chain)
                return singletons[key]
            case Lifetime.SCOPED:
                if not self._allow_scoped:
                    raise DependencyError(f"{_name(key)} es scoped y no puede resolverse fuera de una petición")
                if key not in self._instances:
                    instance = self._build(registration.provider, chain)
                    self._instances[key] = instance
                    if registration.dispose is not None:
                        self._disposables.append((instance, registration.dispose))
                return self._instances[key]
            case _:
                return self._build(registration.provider, chain)

    def _build(self, provider: Callable[..., Any], chain: tuple[Any, ...]) -> Any:
        if inspect.isclass(provider):
            target = provider.__init__
        elif inspect.isfunction(provider) or inspect.ismethod(provider):
            target = provider
        else:  # objeto invocable, por ejemplo async_sessionmaker
            target = provider.__call__
        signature = inspect.signature(target)
        hints = get_type_hints(target)
        kwargs: dict[str, Any] = {}
        for name, parameter in signature.parameters.items():
            if name == "self" or parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
                continue
            dependency = hints.get(name)
            if dependency is None or not self._container.is_registered(dependency):
                if parameter.default is not parameter.empty:
                    continue
                raise DependencyError(
                    f"No se puede resolver el parámetro '{name}' de {_name(provider)}"
                )
            kwargs[name] = self.resolve(dependency, chain)
        return provider(**kwargs)

    async def aclose(self) -> None:
        for instance, dispose in reversed(self._disposables):
            result = dispose(instance)
            if inspect.isawaitable(result):
                await result
        self._disposables.clear()
        self._instances.clear()


def _name(key: Any) -> str:
    return getattr(key, "__qualname__", repr(key))
