from __future__ import annotations

import datetime
import inspect
from pathlib import Path
from typing import Any, Callable, NamedTuple

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

        position = 0
        params: dict[str, Any] = {}
        try:
            for key, param in signature.parameters.items():
                if position >= len(arguments):
                    if param.default != inspect.Parameter.empty:
                        params[key] = param.default
                    elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                        params[key] = []
                    elif param.kind == inspect.Parameter.VAR_KEYWORD:
                        params[key] = {}
                    else:
                        raise AssertionError("There are some missing arguments.")
                elif param.kind == inspect.Parameter.POSITIONAL_ONLY:
                    if arguments[position][0] is None and param.default == inspect.Parameter.empty:
                        params[key] = arguments[position][1]
                        position += 1
                elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    if key == arguments[position][0] or arguments[position][0] is None:
                        params[key] = arguments[position][1]
                        position += 1
                    elif param.default != inspect.Parameter.empty:
                        params[key] = param.default
                elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                    params[key] = []
                    while (
                        position < len(arguments)
                        and arguments[position][0] is None
                        and arguments[position][0] not in signature.parameters
                    ):
                        params[key].append(arguments[position][1])
                        position += 1
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    if key == arguments[position][0]:
                        params[key] = arguments[position][1]
                        position += 1
                    elif param.default != inspect.Parameter.empty:
                        params[key] = param.default
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    if key not in params:
                        params[key] = {}
                    while position < len(arguments) and arguments[position][0] not in signature.parameters:
                        params[key][arguments[position][0]] = arguments[position][1]
                        position += 1
                    params[key] = dict(sorted(params[key].items()))
                else:
                    raise AssertionError("This statement will be never executed.")

            for extrakey, value in arguments[position:]:
                assert extrakey is not None, extrakey
                assert extrakey not in params, extrakey
                params[extrakey] = value

            assert list(params.keys()) == list(signature.parameters.keys()), f"{params=}, {signature.parameters=}"
        except AssertionError as err:
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
