from __future__ import annotations

import ast
import datetime
import inspect
from contextlib import suppress
from pathlib import Path
from typing import Any, Callable, NamedTuple

from cachestore.common import ASTNormalizer
from cachestore.hashers import Hasher


class FunctionInfo(NamedTuple):
    name: str
    filename: Path
    source: str

    @classmethod
    def build(cls, func: Callable[..., Any]) -> "FunctionInfo":
        if hasattr(func, "__cachesore_funcinfo"):
            funcinfo = getattr(func, "__cachesore_funcinfo")
            assert isinstance(funcinfo, FunctionInfo)
            return funcinfo
        filename = Path(inspect.getabsfile(func))
        modulename = inspect.getmodulename(str(filename)) or ""
        name = f"{modulename}.{func.__qualname__}"
        lines, _ = inspect.getsourcelines(func)
        source = "".join(lines)
        with suppress(SyntaxError):
            source = ast.dump(ASTNormalizer().visit(ast.parse(source)))
        return cls(name, filename, source)

    def hash(self, hasher: Hasher) -> str:
        return hasher(self)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "filename": str(self.filename),
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "FunctionInfo":
        return cls(
            name=d["name"],
            filename=Path(d["filename"]),
            source=d["source"],
        )


class ExecutionInfo(NamedTuple):
    params: dict[str, Any]

    @classmethod
    def build(
        cls,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> "ExecutionInfo":
        signature = inspect.signature(func)
        arguments: list[tuple[str | None, Any]] = [(None, v) for v in args]
        arguments += list(kwargs.items())

        try:
            bound_args = signature.bind(*args, **kwargs)
            bound_args.apply_defaults()
            params = bound_args.arguments
        except TypeError as err:
            raise ValueError(
                f"Invalid arguments of {func.__module__}.{func.__name__}:\n\t"
                f"Signature : {signature}\n\t"
                f"Given args: {args=}, {kwargs=}"
            ) from err

        return cls(params)

    def hash(self, hasher: Hasher) -> str:
        return hasher(self)


class CacheInfo(NamedTuple):
    function: FunctionInfo
    parameters: dict[str, Any]
    executed_at: datetime.datetime
    expired_at: datetime.datetime | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "function": self.function.to_dict(),
            "parameters": {k: repr(v) for k, v in self.parameters.items()},
            "executed_at": self.executed_at.isoformat(),
            "expired_at": self.expired_at.isoformat() if self.expired_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CacheInfo":
        return cls(
            function=FunctionInfo.from_dict(d["function"]),
            parameters=d["parameters"],
            executed_at=datetime.datetime.fromisoformat(d["executed_at"]),
            expired_at=datetime.datetime.fromisoformat(d["expired_at"]) if d["expired_at"] else None,
        )
