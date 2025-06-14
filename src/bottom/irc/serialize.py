from __future__ import annotations

import collections
import collections.abc
import string
import typing as t
from dataclasses import dataclass

__all__ = ["CommandSerializer", "register_pattern", "serialize"]

type ParamDict = dict[str, t.Any]


def default_formatter(key: str, value: t.Any) -> str:  # noqa: ANN401
    return format(value)


def guard_field_name(name: str) -> str:
    if not name:
        raise ValueError("param name cannot be empty")
    if name.strip() != name:
        raise ValueError(f"param name cannot have leading or trailing space: {name!r}")
    for disallowed in "{} ":
        if disallowed in name:
            raise ValueError(f"param name cannot contain {disallowed!r}: {name!r}")
    return name


@dataclass(frozen=True)
class SerializerTemplate:
    type ComputedStr = t.Callable[[str, t.Any], t.Any]
    type Component = str | tuple[str, tuple[ComputedStr, ...]]

    original: str
    components: tuple[Component, ...]
    score: int

    def format(self, params: ParamDict, filtered: bool = False) -> str:
        if not filtered:
            params = {k: v for (k, v) in params.items() if v is not None}
        parts = [""] * len(self.components)
        for i, component in enumerate(self.components):
            if isinstance(component, str):
                parts[i] = component
            else:
                key, fns = component
                value = params[key]
                for fn in fns:
                    value = fn(key, value)
                parts[i] = value
        return "".join(parts).strip()

    @classmethod
    def parse(cls, template: str, formatters: dict[str, ComputedStr] | None = None) -> SerializerTemplate:
        score = 0
        components: list[SerializerTemplate.Component] = []

        # otherwise "{x}" and "{x:}" will fail to format
        available_fns: dict[str, SerializerTemplate.ComputedStr] = {"": default_formatter}
        available_fns.update(formatters or {})

        for lit_text, name, spec, conversion in string.Formatter().parse(template):
            spec = spec or ""
            if "{" in spec:
                raise ValueError(f"template {template!r} -- can't use nested formatter '{name}:{spec}'")
            if conversion is not None:
                raise ValueError(f"template {template!r} -- cannot use conversions")

            if lit_text:
                components.append(lit_text)
            if name is not None:
                guard_field_name(name)

                fn_names = spec.split("|")
                if fn_names[-1] != "":
                    fn_names.append("")
                try:
                    field_formatters = tuple([available_fns[fn] for fn in fn_names])
                except KeyError:
                    raise ValueError(
                        f"template {template!r} -- unknown formatters (known: {list(available_fns.keys())})"
                    )
                computed = (name, field_formatters)
                score += 1
                components.append(computed)

        return SerializerTemplate(original=template, components=tuple(components), score=score)


class CommandSerializer:
    formatters: dict[str, SerializerTemplate.ComputedStr]
    templates: dict[str, list[SerializerTemplate]]

    def __init__(self, formatters: dict[str, SerializerTemplate.ComputedStr] | None = None) -> None:
        self.formatters = formatters or {}
        self.templates = {}

    def register(
        self,
        command: str,
        template: str | SerializerTemplate,
    ) -> SerializerTemplate:
        command = command.strip().upper()
        if isinstance(template, str):
            template = SerializerTemplate.parse(template, formatters=self.formatters)

        # maintain descending sort by max possible score
        # this way serialize can stop on the first non-error result
        commands = self.templates.setdefault(command, [])
        commands.append(template)
        commands.sort(key=lambda x: x.score, reverse=True)
        return template

    def serialize(self, command: str, params: ParamDict) -> str:
        command = command.strip().upper()
        if command not in self.templates:
            raise ValueError(f"Unknown command {command!r}")

        params = {k: v for (k, v) in params.items() if v is not None}

        last_err = None
        for candidate in self.templates[command]:
            if candidate.score > len(params):
                continue
            try:
                return candidate.format(params, filtered=True)
            except Exception as err:
                last_err = err

        # last err was from the command with the least params that didn't match
        n = len(self.templates[command])
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
    # formatters
    "bool": lambda key, value: key if value else "",
    "join": lambda key, value: join_iterable(key, value, ""),
    "comma": lambda key, value: join_iterable(key, value, ","),
    "space": lambda key, value: join_iterable(key, value, " "),
    "": default_formatter,
    # guards
    "nospace": guard_no_spaces,
}
GLOBAL_SERIALIZER = CommandSerializer(formatters=GLOBAL_FORMATTERS)


def register_pattern(
    command: str,
    template: str | SerializerTemplate,
    serializer: CommandSerializer = GLOBAL_SERIALIZER,
) -> SerializerTemplate:
    return serializer.register(command, template)


def serialize(command: str, params: ParamDict, *, serializer: CommandSerializer = GLOBAL_SERIALIZER) -> str:
    return serializer.serialize(command, params)
