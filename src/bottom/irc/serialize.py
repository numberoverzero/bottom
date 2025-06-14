from __future__ import annotations

import collections
import collections.abc
import string
import typing as t
from dataclasses import dataclass

__all__ = ["CommandSerializer", "register_pattern", "serialize"]

type ParamDict = dict[str, t.Any]


@dataclass(frozen=True)
class SerializerTemplate:
    type ComputedStr = t.Callable[[str, t.Any], t.Any]
    type Component = str | tuple[str, tuple[ComputedStr, ...]]

    original: str
    components: tuple[Component, ...]

    def format(self, kwargs: ParamDict) -> str:
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
    def parse(cls, template: str, formatters: dict[str, ComputedStr]) -> tuple[SerializerTemplate, set[str], set[str]]:
        req = set()
        opt = set()
        components: list[SerializerTemplate.Component] = []
        # otherwise "{x}" will fail to format
        formatters.setdefault("", lambda _, value: format(value))
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
                fnames = format_spec.split("|")
                if fnames[0] == "opt":
                    fnames.pop(0)
                    opt.add(field_name)
                else:
                    req.add(field_name)
                if not fnames or fnames[-1] != "":
                    fnames.append("")
                if unknown := [fname for fname in fnames if fname not in formatters]:
                    raise ValueError(f"invalid template {template!r} -- unknown formatters {unknown}")
                field_formatters = tuple([formatters[fname] for fname in fnames])
                computed: SerializerTemplate.Component = (field_name, field_formatters)
                components.append(computed)

        tpl = SerializerTemplate(original=template, components=tuple(components))
        return tpl, req, opt


@dataclass(frozen=True, kw_only=True)
class ParamSpec[T]:
    name: str
    default: T | None
    depends_on: tuple[ParamSpec, ...]


@dataclass(frozen=True, kw_only=True)
class CommandSpec:
    command: str
    params: tuple[ParamSpec, ...]
    template: SerializerTemplate

    @property
    def max_score(self) -> int:
        return len(self.params)

    def serialize(self, params: ParamDict) -> str:
        loaded = {}
        for param in self.params:
            key = param.name
            value = params.get(key, param.default)
            if value is None:
                raise ValueError(f"missing required param {key}")
            loaded[key] = value
        return self.template.format(loaded)

    @classmethod
    def parse(
        cls,
        command: str,
        template: SerializerTemplate,
        req: set[str],
        opt: set[str],
        defaults: dict[str, t.Any],
        deps: dict[str, str],
    ) -> CommandSpec:
        params: dict[str, ParamSpec] = dict()

        if any(v is None for v in defaults.values()):
            raise ValueError(f"default values must be non-null, but got: {defaults}")

        # when defaults isn't empty, we might be relaxing some
        req.difference_update(defaults.keys())
        opt.update(defaults.keys())

        # all deps known
        known = req.union(opt)

        if __debug__:  # ty: ignore https://github.com/astral-sh/ty/issues/577
            # no overlap
            assert not req.intersection(opt)

            # known includes all template variables, provided defaults, and all dependency information
            dep_refs = set(deps.keys()).union(deps.values())
            def_refs = set(defaults.keys())
            assert known.issuperset(dep_refs)
            assert known.issuperset(def_refs)

        # WARN: no circular dependency detection.  don't do that.
        # note: sorted so tests can ensure dependency deferral
        names = collections.deque(sorted(known))
        while names:
            name = names.popleft()
            depends_on = ()
            if dependency_name := deps.get(name):
                if maybe_dependency := params.get(dependency_name):
                    depends_on = (maybe_dependency,)
                else:
                    # has a dependency but we haven't defined it yet.
                    # process the next name.
                    names.append(name)
                    continue

            if name in req:
                default = None
            else:
                # optionals use "" unless we provided an explicit default
                default = defaults.get(name, "")

            params[name] = ParamSpec(
                name=name,
                default=default,
                depends_on=depends_on,
            )
        return CommandSpec(command=command, params=tuple(params.values()), template=template)


class CommandSerializer:
    formatters: dict[str, SerializerTemplate.ComputedStr]
    commands: dict[str, list[CommandSpec]]

    def __init__(self, formatters: dict[str, SerializerTemplate.ComputedStr]) -> None:
        self.formatters = formatters
        self.commands = {}

    def register(
        self,
        command: str,
        fmt: str,
        defaults: dict[str, t.Any],
        deps: dict[str, str],
    ) -> CommandSpec:
        command = command.strip().upper()
        template, req, opt = SerializerTemplate.parse(fmt, formatters=self.formatters)
        spec = CommandSpec.parse(command, template=template, req=req, opt=opt, defaults=defaults, deps=deps)

        # maintain descending sort by max possible score
        # this way serialize can stop on the first non-error result
        commands = self.commands.setdefault(command, [])
        commands.append(spec)
        commands.sort(key=lambda x: x.max_score, reverse=True)
        return spec

    def serialize(self, command: str, params: ParamDict) -> str:
        command = command.strip().upper()
        if command not in self.commands:
            raise ValueError(f"Unknown command {command!r}")

        # None is the same as not passing a value
        params = {key: value for (key, value) in params.items() if value is not None}

        last_err = None
        for candidate in self.commands[command]:
            try:
                return candidate.serialize(params)
            except Exception as err:
                last_err = err

        # last err was from the command with the least params that didn't match
        n = len(self.commands[command])
        summary = ValueError(f"params were invalid for {n} forms of the command {command}")
        raise summary from last_err


def join_iterable[T: t.Iterable | t.Any](_key: str, value: T, delim: str) -> T | str:
    if isinstance(value, str):
        return value
    if isinstance(value, collections.abc.Iterable):
        return delim.join(str(f) for f in value)
    return value


def guard_no_spaces[T: t.Any](key: str, value: T) -> T | str:
    as_str = str(value)
    if " " in as_str:
        raise ValueError(f"error: {key} cannot contain spaces")
    return as_str


GLOBAL_FORMATTERS = {
    "bool": lambda key, value: key if value else "",
    "nospace": guard_no_spaces,
    "join": lambda key, value: join_iterable(key, value, ""),
    "comma": lambda key, value: join_iterable(key, value, ","),
    "space": lambda key, value: join_iterable(key, value, " "),
    "": lambda _, value: format(value),
}
GLOBAL_SERIALIZER = CommandSerializer(formatters=GLOBAL_FORMATTERS)


def register_pattern(
    command: str,
    fmt: str,
    defaults: dict[str, t.Any] | None = None,
    deps: dict[str, str] | None = None,
    serializer: CommandSerializer = GLOBAL_SERIALIZER,
) -> CommandSpec:
    return serializer.register(command, fmt, defaults=defaults or {}, deps=deps or {})


def serialize(command: str, params: ParamDict, *, serializer: CommandSerializer = GLOBAL_SERIALIZER) -> str:
    return serializer.serialize(command, params)
