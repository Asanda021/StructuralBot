from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Optional, Protocol

from .service import AIProvider, AIRequest, AIResponse


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    enabled: bool = True
    timeout: float = 30.0
    extra: Dict[str, Any] = field(default_factory=dict)


class ProviderFactory(Protocol):
    def __call__(self, config: ProviderConfig) -> AIProvider:
        ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._configs: Dict[str, ProviderConfig] = {}
        self._factories: Dict[str, ProviderFactory] = {}

    def register(
        self,
        config: ProviderConfig,
        factory: Optional[ProviderFactory] = None,
    ) -> None:
        name = config.name.strip().lower()
        if not name:
            raise ValueError("Provider name cannot be empty.")

        self._configs[name] = config

        if factory is not None:
            self._factories[name] = factory

    def unregister(self, name: str) -> None:
        key = name.strip().lower()
        self._configs.pop(key, None)
        self._factories.pop(key, None)

    def get_config(self, name: str) -> ProviderConfig:
        key = name.strip().lower()
        try:
            return self._configs[key]
        except KeyError as exc:
            raise KeyError(f"Unknown AI provider: {name}") from exc

    def get_factory(self, name: str) -> Optional[ProviderFactory]:
        return self._factories.get(name.strip().lower())

    def exists(self, name: str) -> bool:
        return name.strip().lower() in self._configs

    def list_providers(self) -> Iterable[ProviderConfig]:
        return tuple(self._configs.values())

    def create(self, name: str) -> AIProvider:
        config = self.get_config(name)

        if not config.enabled:
            raise RuntimeError(f"AI provider '{config.name}' is disabled.")

        factory = self.get_factory(name)

        if factory is None:
            return PlaceholderProvider(config)

        return factory(config)


class PlaceholderProvider:
    """
    Safe provider used when no external AI service is configured.

    It deliberately does not pretend to provide an actual AI response.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    def generate(self, request: AIRequest) -> AIResponse:
        message = (
            "AI provider is not configured. "
            "Please configure an enabled provider before using AI features."
        )

        return AIResponse(
            text=message,
            provider=self.config.name,
            model=self.config.model,
            usage={},
            metadata={
                "configured": False,
                "provider": self.config.name,
            },
        )


def create_provider(
    config: ProviderConfig,
    factory: Optional[ProviderFactory] = None,
) -> AIProvider:
    if not config.enabled:
        raise RuntimeError(f"AI provider '{config.name}' is disabled.")

    if factory is not None:
        return factory(config)

    return PlaceholderProvider(config)


def build_default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()

    registry.register(
        ProviderConfig(
            name="placeholder",
            model="placeholder",
            enabled=True,
        )
    )

    return registry


_default_registry = build_default_provider_registry()


def get_provider_registry() -> ProviderRegistry:
    return _default_registry


def register_provider(
    config: ProviderConfig,
    factory: Optional[ProviderFactory] = None,
) -> None:
    _default_registry.register(config, factory)


def get_provider(name: str) -> AIProvider:
    return _default_registry.create(name)


__all__ = [
    "ProviderConfig",
    "ProviderFactory",
    "ProviderRegistry",
    "PlaceholderProvider",
    "create_provider",
    "build_default_provider_registry",
    "get_provider_registry",
    "register_provider",
    "get_provider",
]
