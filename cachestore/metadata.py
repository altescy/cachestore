from __future__ import annotations

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
        filename = Path(inspect.getabsfile(func))
        modulename = inspect.getmodulename(str(filename)) or ""
        name = f"{modulename}.{func.__qualname__}"
        lines, _ = inspect.getsourcelines(func)
        source = "".join(lines)
        return cls(name, filename, source)

    def hash(self, hasher: Hasher) -> str:
        return hasher(self)


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
                assert position < len(arguments)
                if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                    assert arguments[position][0] is None and param.default == inspect.Parameter.empty
                    params[key] = arguments[position][1]
                    position += 1
                if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    if key == arguments[position][0] or arguments[position][0] is None:
                        params[key] = arguments[position][1]
                        position += 1
                    elif param.default != inspect.Parameter.empty:
                        params[key] = param.default
                elif param.kind == inspect.Parameter.VAR_POSITIONAL:
                    params[key] = []
                    while position < len(arguments) and arguments[position][0] not in signature.parameters:
                        params[key].append(arguments[position][1])
                        position += 1
                elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                    assert key == arguments[position][0], f"{key=}, {arguments[position][0]=}"
                    params[key] = arguments[position][1]
                    position += 1
                elif param.kind == inspect.Parameter.VAR_KEYWORD:
                    if key not in params:
                        params[key] = {}
                    while position < len(arguments) and arguments[position][0] not in signature.parameters:
                        params[key][arguments[position][0]] = arguments[position][1]
                        position += 1
                    params[key] = dict(sorted(params[key].items()))
                else:
                    raise AssertionError("This statement is never executed.")

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
