from __future__ import annotations

import collections
import collections.abc
import string
import typing as t
from dataclasses import dataclass, field

__all__ = ["CommandSerializer", "SerializerTemplate", "register_pattern", "serialize"]


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


class FormattingError(Exception):
    """
    Thrown to signal that the exception is from a component function

    This allows handling structural vs value exceptions differently
    """

    def __init__(self, cause: Exception) -> None:
        self.cause = cause


@dataclass(frozen=True)
class SerializerTemplate:
    """

    .. note::

        Do not instantiate SerializerTemplate directly.
        Use :meth:`SerializerTemplate.parse<bottom.irc.serialize.SerializerTemplate.parse>` instead.

    This is an optimized version of string.format() that can apply custom formatting functions::

        def upper(id: str, value: str) -> str:
            return value.upper()

        def reverse(id: str, value: str) -> str:
            return value[::-1]

        template = "hello, {name:up|rev}!"
        tpl = SerializedTemplate.parse(template, formatters={"up": upper, "rev": reverse})

        print(tpl.format("greet", {"name": "world"}))
        # prints: hello, DLROW!
    """

    type ComputedStr = t.Callable[[str, t.Any], t.Any]
    type Component = str | tuple[str, tuple[ComputedStr, ...]]

    _components: tuple[Component, ...]

    original: str
    """
    The original str this template was parsed from::

        src = "{foo} {bar}"
        assert SerializerTemplate.parse(src).original == src
    """

    params: tuple[str, ...]
    """
    unique names of the placeholders used in the string.

    ordered by first appearance left to right::

        src = "{foo},{bar},{foo}"
        tpl = SerializerTemplate.parse(src)
        assert tpl.params == ("foo", "bar")
    """

    score: int = field(init=False)
    """
    The number of unique arguments, not the number of replacements that occur::

        first = SerializerTemplate.parse("{foo}")
        second = SerializerTemplate.parse("{foo}{foo}{foo}")
        assert first.score == second.score
    """

    def __post_init__(self) -> None:
        # use object setattr since dict is frozen
        object.__setattr__(self, "score", len(self.params))

    def format(self, params: dict[str, t.Any], is_filtered: bool = False, wrap_exc: bool = False) -> str:
        """
        Similar to string.format()::

            template = SerializerTemplate.parse("{one} + {two} = {three}")

            params = {"one": "A", "two": "B", "three": "C"}
            print(template.format(params))
            # prints: A + B = C

        Args:
            params: the values to render into the template
            filtered: when False, removes any params whose value is None.  pass True if you have already
                done this, or if you want to pass explicit None values into the dict.
            wrap_exc: when True, any exceptions from formatter functions is wrapped in a FormattingError,
                whose ``cause`` attribute is the underlying error.
        """
        if not is_filtered:
            params = {k: v for (k, v) in params.items() if v is not None}
        parts = [""] * len(self._components)
        for i, component in enumerate(self._components):
            if isinstance(component, str):
                parts[i] = component
            else:
                key, fns = component
                value = params[key]
                for fn in fns:
                    try:
                        value = fn(key, value)
                    except Exception as cause:
                        if wrap_exc:
                            raise FormattingError(cause)
                        else:
                            raise cause
                parts[i] = value
        return "".join(parts).strip()

    @classmethod
    def parse(
        cls, template: str, formatters: dict[str, t.Callable[[str, t.Any], t.Any]] | None = None
    ) -> SerializerTemplate:
        """
        Parses a provided string into a SerializedTemplate, an optimized representation of the template for future
        rendering.  If provided, the formatters dict is used to look up any custom formatters referenced from the template
        string::

            def upper(id: str, value: str) -> str:
                return value.upper()

            def reverse(id: str, value: str) -> str:
                return value[::-1]

            template = "hello, {name:up|rev}!"
            tpl = SerializedTemplate.parse(template, formatters={"up": upper, "rev": reverse})

            print(tpl.format("greet", {"name": "world"}))
            # prints: hello, DLROW!
        """
        params: list[str] = []
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
                if name not in params:
                    params.append(name)
                components.append(computed)

        return SerializerTemplate(original=template, _components=tuple(components), params=tuple(params))


class CommandSerializer:
    """
    A mapping of command names to a list of templates (``dict[str, list[SerializerTemplate]]``) that can apply
    custom formatting to each parameter.

    When a command registers more than one template, then during serialization they are tried in order from most to
    least parameters, until the provided params are sufficient.  When two templates for the same command have the same
    number of arguments, they are tried in the order that they were registered.

    For example, the LIST command is implemented as follows::

        serializer.register("LIST", "LIST {channel:comma} {target}")
        serializer.register("LIST", "LIST {channel:comma}")
        serializer.register("LIST", "LIST")


    See: :meth:`serialize<bottom.irc.serialize.CommandSerializer.serialize>`
    """

    formatters: dict[str, t.Callable[[str, t.Any], t.Any]]
    """
    A dict of functions that can be referenced in templates.  Each function should take the name of the param
    being replaced, and the value for that param.  Its return value will be formatted into the template, or
    passed to the next function if there is a chain::

        def upper(id: str, value: str) -> str:
            return value.upper()

        def reverse(id: str, value: str) -> str:
            return value[::-1]

        serializer = CommandSerializer(formatters={"up": upper, "rev": reverse})
        template = "hello, {name:up|rev}!"
        serializer.register("greet", template)

        print(serializer.serialize("greet", {"name": "world"}))
        # prints: hello, DLROW!

    You may raise an error from a formatter as a way to guard values::

        def not_admin(id: str, user: User) -> str:
            if user.is_admin:
                raise ValueError("can't format an admin")
            return user.info.as_irc_line()

        template = "found user: {user|noadmin}"
        serializer = CommandSerializer(formatters={"noadmin": not_admin})

    """
    _templates: dict[str, list[SerializerTemplate]]

    def __init__(self, formatters: dict[str, t.Callable[[str, t.Any], t.Any]] | None = None) -> None:
        """
        Args:
            formatters: dict of functions that can be referenced in templates.  See :attr:`formatters<bottom.irc.serialize.CommandSerializer>`
        """
        self.formatters = formatters or {}
        self._templates = {}

    def register(
        self,
        command: str,
        template: str | SerializerTemplate,
    ) -> SerializerTemplate:
        """
        Register a template to a command.  Each command may have more than one template.  When serializing a command,
        the templates for that command will be tried in order from most -> least parameters until one matches.  If
        mutliple templates are registered with the same number of arguments, they will be tried in the order they were
        registered::

            serializer = CommandSerializer()
            serializer.register("foo", "{one} -> {two}")
            serializer.register("foo", "{two} <- {one}")

            print(serializer.serializer("foo", {"one": "A", "two": "B"}))
            # prints A -> B

        Returns the prepared template.
        """
        command = command.strip().upper()
        if isinstance(template, str):
            template = SerializerTemplate.parse(template, formatters=self.formatters)

        # maintain descending sort by max possible score
        # this way serialize can stop on the first non-error result
        commands = self._templates.setdefault(command, [])
        commands.append(template)
        commands.sort(key=lambda x: x.score, reverse=True)
        return template

    def serialize(self, command: str, params: dict[str, t.Any]) -> str:
        """
        Render a dict into a command.  This is like string.format()::

            "{greet}, {name}!".format({"greet": "hello", "name": "world"})

            serializer.serialize("greeting", {"greet": "hello", "name": "world"})

        Unlike string.format, each command may have more than one template.  When serializing a command, the templates
        for that command will be tried in order from most -> least parameters until one matches.  If mutliple templates
        are registered with the same number of arguments, they will be tried in the order they were registered::

            serializer = CommandSerializer()
            serializer.register("foo", "{one} -> {two}")
            serializer.register("foo", "{two} <- {one}")

            print(serializer.serializer("foo", {"one": "A", "two": "B"}))
            # prints A -> B
        """
        command = command.strip().upper()
        if command not in self._templates:
            raise ValueError(f"Unknown command {command!r}")

        params = {k: v for (k, v) in params.items() if v is not None}

        last_err = None
        for candidate in self._templates[command]:
            if candidate.score > len(params):
                continue
            try:
                return candidate.format(params, is_filtered=True, wrap_exc=True)
            except FormattingError as outer:
                # this error came from one of the formatters, which means we matched args
                # but the formatter rejected the value.  don't fall back to next formatter,
                # raise immediately
                raise outer.cause
            except Exception as err:
                last_err = err

        # last err was from the command with the least params that didn't match
        n = len(self._templates[command])
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
    serializer: CommandSerializer | None = None,
) -> SerializerTemplate:
    """
    register a template for the given command into the provided serializer (default: global).

    see: :meth:`CommandSerializer.register<bottom.irc.serialize.CommandSerializer.register>`
    """
    return (serializer or GLOBAL_SERIALIZER).register(command, template)


def serialize(command: str, params: dict[str, t.Any], *, serializer: CommandSerializer | None = None) -> str:
    """
    serialize a command with the given params, trying registered templates in order from most params to least.

    defaults to global serializer.

    see: :meth:`CommandSerializer.serialize<bottom.irc.serialize.CommandSerializer.serialize>`
    """
    return (serializer or GLOBAL_SERIALIZER).serialize(command, params)
