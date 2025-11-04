from typing import Any, Callable


class Fact(dict[str, Any]): ...


class KnowledgeEngine:
    def reset(self) -> None: ...
    def run(self) -> None: ...


class _Match:
    def __getattr__(self, name: str) -> Any: ...


MATCH: _Match


def Rule(*patterns: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...
