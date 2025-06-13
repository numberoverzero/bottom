from __future__ import annotations

import collections
import typing as t
from dataclasses import dataclass

__all__ = ["CommandSerializer", "register_serializer_pattern", "serialize"]

type ParamDict = dict[str, t.Any]


@dataclass(frozen=True, kw_only=True)
class ParamSpec[T]:
    name: str
    required: bool
    default: T | None
    depends_on: tuple[ParamSpec, ...]

    def has_dependencies(self, available: dict[ParamSpec, t.Any]) -> bool:
        return all(dep in available for dep in self.depends_on)


@dataclass(frozen=True, kw_only=True)
class CommandSpec:
    command: str
    params: tuple[ParamSpec, ...]
    template: str

    def score(self, kw_params: ParamDict) -> int:
        """returns -1 if kw_params are missing required or missing dependencies, otherwise sum(available params)"""
        # TODO combine with pack?
        total = 0
        available: dict[ParamSpec, t.Any] = {}
        for param in self.params:
            value = kw_params.get(param.name)
            if value is None:
                value = param.default
            if value is not None:
                available[param] = value
        for param in self.params:
            # error: missing required param
            if param.required and param not in available:
                return -1
            elif param in available:
                # ok: param and deps available
                if param.has_dependencies(available):
                    total += 1
                # error: missing dependency
                else:
                    return -1
        return total

    def pack(self, kw_params: ParamDict) -> str:
        # TODO combine with score?
        filtered: ParamDict = {}
        for param in self.params:
            value = kw_params.get(param.name)
            if value is None:
                value = param.default
            if value is not None:
                filtered[param.name] = value
            else:
                filtered[param.name] = ""
        return self.template.format(**filtered).strip()

    def __repr__(self) -> str:  # pragma: no cover
        required = ", ".join(param.name for param in self.params if param.required and param.default is None)
        defaults = ", ".join(param.name for param in self.params if param.default is not None)
        return f"CommandSpec({self.template!r}, req=({required}), def=({defaults}))"


class CommandSerializer:
    commands: dict[str, list[CommandSpec]]

    def __init__(self) -> None:
        self.commands = {}

    def register(
        self,
        command: str,
        fmt: str,
        req: set[str],
        defaults: dict[str, t.Any],
        deps: dict[str, str],
    ) -> CommandSpec:
        command = command.strip().upper()
        params: dict[str, ParamSpec] = dict()
        names = collections.deque(set((*req, *deps.keys(), *deps.values(), *defaults.keys())))

        # WARN: no circular dependency detection.  don't do that.
        while names:
            name = names.popleft()
            dependency = None
            if dependency_name := deps.get(name):
                if dependency := params.get(dependency_name):
                    pass
                else:
                    # missing dependency for this param; go around again
                    names.append(name)
                    continue
            param = ParamSpec(
                name=name,
                required=name in req,
                default=defaults.get(name, None),
                depends_on=(dependency,) if dependency else (),
            )
            params[name] = param
        spec = CommandSpec(command=command, params=tuple(params.values()), template=fmt)
        self.commands.setdefault(command, []).append(spec)
        return spec

    def serialize(self, command: str, kw_params: ParamDict) -> str:
        command = command.strip().upper()
        if command not in self.commands:
            raise ValueError(f"Unknown command {command!r}")
        spec, highest = None, -1
        for candidate in self.commands[command]:
            score = candidate.score(kw_params)
            # on tie, first registered wins
            if score > highest:
                highest = score
                spec = candidate
        if highest < 0:
            raise ValueError(f"Missing arguments for command {command!r}.  Closest match: {spec}")
        assert spec is not None
        return spec.pack(kw_params)


GLOBAL_COMMAND_SERIALIZER = CommandSerializer()


def register_serializer_pattern(
    command: str,
    fmt: str,
    req: t.Iterable[str],
    defaults: dict[str, t.Any] | None = None,
    deps: dict[str, str] | None = None,
    serializer: CommandSerializer = GLOBAL_COMMAND_SERIALIZER,
) -> CommandSpec:
    return serializer.register(command, fmt, req=set(req), defaults=defaults or {}, deps=deps or {})


def serialize(command: str, kw_params: ParamDict, *, serializer: CommandSerializer = GLOBAL_COMMAND_SERIALIZER) -> str:
    return serializer.serialize(command, kw_params)
