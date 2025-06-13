from __future__ import annotations

import collections
import collections.abc
import math
import string
import typing as t
from dataclasses import dataclass

__all__ = ["CommandSerializer", "register_serializer_pattern", "serialize"]

type ParamDict = dict[str, t.Any]


@dataclass(frozen=True)
class SerializingTemplate:
    type ComputedStr = t.Callable[[str, t.Any], t.Any]
    type Component = str | tuple[str, tuple[ComputedStr, ...]]

    original: str
    components: tuple[Component, ...]

    def format(self, **kwargs: t.Any) -> str:
        parts = []
        for component in self.components:
            if isinstance(component, str):
                parts.append(component)
            else:
                key, fns = component
                value = kwargs[key]
                for fn in fns:
                    value = fn(key, value)
                parts.append(value)
        return "".join(parts).strip()

    @classmethod
    def from_str(cls, template: str, fns: dict[str, ComputedStr]) -> tuple[SerializingTemplate, set[str], set[str]]:
        required = set()
        optional = set()
        components: list[SerializingTemplate.Component] = []

        fields = string.Formatter().parse(template)
        for literal_text, field_name, format_spec, conversion in fields:
            format_spec = format_spec or ""
            if "{" in format_spec:
                raise ValueError(
                    f"invalid template {template!r} -- can't use nested formatter '{field_name}:{format_spec}'"
                )
            if conversion is not None:
                raise ValueError(f"invalid template {template!r} -- cannot use conversions")
            components.append(literal_text)

            if field_name is not None:
                formatters = format_spec.split("|")
                if formatters[0] == "opt":
                    formatters.pop(0)
                    optional.add(field_name)
                else:
                    required.add(field_name)
                if unknown := [f for f in formatters if f not in fns]:
                    raise ValueError(f"invalid template {template!r} -- unknown formatters {unknown}")
                if not formatters or formatters[-1] != "":
                    formatters.append("")
                field_formatters = tuple([fns[formatter_name] for formatter_name in formatters])
                computed: SerializingTemplate.Component = (field_name, field_formatters)
                components.append(computed)

        return SerializingTemplate(original=template, components=tuple(components)), required, optional


@dataclass(frozen=True, kw_only=True)
class ParamSpec[T]:
    name: str
    default: T | None
    depends_on: tuple[ParamSpec, ...]

    def has_dependencies(self, available: dict[ParamSpec, t.Any]) -> bool:
        return all(dep in available for dep in self.depends_on)


@dataclass(frozen=True, kw_only=True)
class CommandSpec:
    command: str
    params: tuple[ParamSpec, ...]
    template: SerializingTemplate

    def score(self, kw_params: ParamDict) -> int:
        """returns -1 if kw_params are missing required or missing dependencies, otherwise sum(available params)"""
        # TODO combine with pack?
        total = 0
        available: dict[ParamSpec, t.Any] = {}
        for param in self.params:
            value = kw_params.get(param.name)
            # required param is missing
            if value is None and param.default is None:
                return -1
            elif value is not None:
                available[param] = value
            elif param.default not in (None, ""):
                available[param] = param.default
            elif param.default is None:
                raise RuntimeError("programming error, all defaults should be non-None")
        for param in self.params:
            # already filtered out missing requirements
            if param in available:
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
                print("TODO: unexpected entry into failsafe branch")
                filtered[param.name] = ""
        return self.template.format(**filtered)

    def __repr__(self) -> str:  # pragma: no cover
        required = ", ".join(param.name for param in self.params if param.default is None)
        defaults = ", ".join(param.name for param in self.params if param.default in (None, ""))
        return f"CommandSpec({self.template!r}, req=({required}), def=({defaults}))"


class CommandSerializer:
    commands: dict[str, list[CommandSpec]]

    def __init__(self, formatters: dict[str, SerializingTemplate.ComputedStr] | None = None) -> None:
        self.commands = {}
        if formatters is None:
            formatters = dict(DEFAULT_FORMATTERS)
        self.formatters = formatters

    def register(
        self,
        command: str,
        fmt: str,
        defaults: dict[str, t.Any],
        deps: dict[str, str],
    ) -> CommandSpec:
        command = command.strip().upper()
        params: dict[str, ParamSpec] = dict()
        template, req, opt = SerializingTemplate.from_str(fmt, fns=self.formatters)

        # remove defaults from req; add defaults to opt
        req.difference_update(defaults.keys())
        opt.update(defaults.keys())

        # no overlap
        assert not req.intersection(opt)
        # all deps known
        known = req.union(opt)
        dep_refs = set(deps.keys()).union(deps.values())
        def_refs = set(defaults.keys())
        assert known.issuperset(dep_refs)
        assert known.issuperset(def_refs)

        # WARN: no circular dependency detection.  don't do that.
        names = collections.deque(known)
        while names:
            name = names.popleft()
            depends_on = ()
            if dependency_name := deps.get(name):
                if dependency := params.get(dependency_name):
                    depends_on = (dependency,)
                else:
                    # missing dependency for this param
                    # don't make a new param, just go around again
                    names.append(name)
                    continue

            if name in req:
                default = None
            else:
                default = defaults.get(name, "")
                assert default is not None

            param = ParamSpec(
                name=name,
                default=default,
                depends_on=depends_on,
            )
            params[name] = param
        spec = CommandSpec(command=command, params=tuple(params.values()), template=template)
        self.commands.setdefault(command, []).append(spec)
        return spec

    def serialize(self, command: str, kw_params: ParamDict) -> str:
        command = command.strip().upper()
        if command not in self.commands:
            raise ValueError(f"Unknown command {command!r}")
        spec, highest = None, -math.inf
        for candidate in self.commands[command]:
            score = candidate.score(kw_params)
            # on tie, first registered wins
            if score > highest:
                highest = score
                spec = candidate
        assert spec is not None
        if highest < 0:
            raise ValueError(f"Missing arguments for command {command!r}.  Closest match: {spec}")
        return spec.pack(kw_params).strip()


def join_iterable[T: t.Iterable | t.Any](_key: str, value: T, delim: str) -> T | str:
    if isinstance(value, str):
        return value
    if isinstance(value, collections.abc.Iterable):
        return delim.join(str(f) for f in value)
    return value


def guard_no_spaces[T: t.Any](key: str, value: T, delim: str) -> T | str:
    as_str = str(value)
    if " " in as_str:
        raise ValueError(f"error: {key} cannot contain spaces")
    return as_str


DEFAULT_FORMATTERS = {
    "bool": lambda key, value: key if value else "",
    "nospace": guard_no_spaces,
    "join": lambda key, value: join_iterable(key, value, ""),
    "comma": lambda key, value: join_iterable(key, value, ","),
    "space": lambda key, value: join_iterable(key, value, " "),
    "": lambda _, value: format(value),
}
GLOBAL_COMMAND_SERIALIZER = CommandSerializer(formatters=DEFAULT_FORMATTERS)


def register_serializer_pattern(
    command: str,
    fmt: str,
    defaults: dict[str, t.Any] | None = None,
    deps: dict[str, str] | None = None,
    serializer: CommandSerializer = GLOBAL_COMMAND_SERIALIZER,
) -> CommandSpec:
    return serializer.register(command, fmt, defaults=defaults or {}, deps=deps or {})


def serialize(command: str, kw_params: ParamDict, *, serializer: CommandSerializer = GLOBAL_COMMAND_SERIALIZER) -> str:
    return serializer.serialize(command, kw_params)
