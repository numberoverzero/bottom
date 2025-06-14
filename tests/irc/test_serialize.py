# ============================================================================
# tests for serialization primitives
# specific command tests live in test_serialize_rfc2812.py
# ============================================================================
import pytest
from bottom.irc.serialize import GLOBAL_FORMATTERS, CommandSerializer, SerializerTemplate
from bottom.irc.serialize import register_pattern as module_register
from bottom.irc.serialize import serialize as module_serialize


@pytest.fixture
def formatters() -> dict[str, SerializerTemplate.ComputedStr]:
    return {}


@pytest.fixture
def serializer(formatters: dict[str, SerializerTemplate.ComputedStr]) -> CommandSerializer:
    return CommandSerializer(formatters=formatters)


@pytest.mark.parametrize(
    "template",
    [
        "}invalid format str{",
        "{x:unknown_fn} unknown function",
        "{x:{nested}} no nested formatters",
        "{x!r} no converters",
        "{ x :} no space around",
        "{x y:} no space inside",
        "{{{} no brackets inside",
        "{}}} no brackets inside",
        "{} no anonymous params",
    ],
)
def test_template_parse_invalid(template) -> None:
    with pytest.raises(ValueError):
        SerializerTemplate.parse(template)


@pytest.mark.parametrize(
    "template",
    [
        "}}braces outside format_spec{{",
        "{x-_-y} punctuation in param name",
        "{x@y.~<>#$^\\/?} more punctuation in param name",
        "{x:known_fn} known function",
        "{x} default empty formatter",
        "{x:} explicit empty formatter",
        "no params",
        "",
    ],
)
def test_template_parse_valid(template: str) -> None:
    fns = {"known_fn": lambda _, value: str(value)}
    SerializerTemplate.parse(template, fns)


@pytest.mark.parametrize(
    ("template", "expected"),
    [("}}ok{{", "}ok{"), ("foo bar", "foo bar")],
)
@pytest.mark.parametrize(
    "params",
    [{}, {"foo": "bar"}, {"hello": object()}, {"world": str}],
)
def test_template_format_no_params(template, expected, params) -> None:
    tpl = SerializerTemplate.parse(template)
    assert tpl.format(params) == expected


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"valid": None, "template": None},
        {"valid": "valid"},
        {"valid": "valid", "template": None},
        {"template": "template"},
        {"template": "template", "valid": None},
    ],
    ids=str,
)
def test_template_missing_args(params) -> None:
    """command is missing required params"""
    template = SerializerTemplate.parse("{valid} {template}")
    with pytest.raises(KeyError):
        template.format(params)


@pytest.mark.parametrize(
    ("template", "params", "expected"),
    [
        ("{x:|||}", {"x": True}, "True"),
        ("{x:bool|bool|bool}", {"x": "y"}, "x"),
        ("{x:join|join|join}", {"x": [1, 2, 3]}, "123"),
        ("{x:comma|comma|comma}", {"x": [1, 2, 3]}, "1,2,3"),
        ("{x:space|space|space}", {"x": [1, 2, 3]}, "1 2 3"),
        ("{x:nospace|space}", {"x": "123"}, "123"),
        ("{x:join|bool}", {"x": False}, ""),
        ("{x:join|bool}", {"x": object()}, "x"),
    ],
)
def test_template_chained_formats(template, params, expected) -> None:
    tpl = SerializerTemplate.parse(template, formatters=GLOBAL_FORMATTERS)
    assert tpl.format(params) == expected


def test_serializer_register_existing(serializer) -> None:
    template = SerializerTemplate.parse("{foo} {bar}")
    same = serializer.register("foo", template)
    assert template is same


@pytest.mark.parametrize(
    ("_id", "templates", "params", "expected"),
    [
        (
            "same params: first registered",
            [
                "1 {a} {b}",
                "2 {a} {b}",
            ],
            {"a": "kw:a", "b": "kw:b"},
            "1 kw:a kw:b",
        ),
        (
            "diff params: first registered",
            [
                "1 {a} {b}",
                "2 {a} {c}",
            ],
            {"a": "kw:a", "b": "kw:b", "c": "kw:c"},
            "1 kw:a kw:b",
        ),
        (
            "most params",
            [
                "1 {a} {b}",
                "2 {a} {b} {c}",
            ],
            {"a": "kw:a", "b": "kw:b", "c": "kw:c"},
            "2 kw:a kw:b kw:c",
        ),
        (
            "noop: repetition",
            [
                "1 {a}",
                "2 {a} {a} {a}",
            ],
            {"a": "kw:a"},
            "1 kw:a",
        ),
        (
            "noop: param order",
            [
                "1 {a} {b}",
                "2 {b} {a}",
            ],
            {"b": "kw:b", "a": "kw:a"},
            "1 kw:a kw:b",
        ),
    ],
    ids=lambda *a: a[0],
)
def test_serializer_ordering(serializer: CommandSerializer, _id, templates, params, expected) -> None:
    command = "foo"
    for template in templates:
        serializer.register(command, template)
    assert serializer.serialize(command, params) == expected


def test_serializer_unknown_command(serializer) -> None:
    with pytest.raises(ValueError):
        serializer.serialize("unknown", {})


def test_global_serializer(serializer: CommandSerializer) -> None:
    """module-level serialize function defaults to a global serializer"""

    command = "foo"
    pattern = "1 {a}"
    params = {"a": "kw:a"}
    expected = "1 kw:a"

    # explicitly pass our serializer
    serializer.register(command, pattern)
    actual = module_serialize(command, params, serializer=serializer)
    assert actual == expected

    # defaults to a serializer that doesn't know this command
    with pytest.raises(ValueError):
        module_serialize(command, params)

    # register to global handler and it should succeed
    module_register(command, template=pattern)
    actual = module_serialize(command, params)
    assert actual == expected


@pytest.mark.parametrize(
    ("template", "params", "expected"),
    [
        # bool formatter uses bool(param[name])
        ("{a:bool}", {"a": True}, "a"),
        ("{a:bool}", {"a": "foo"}, "a"),
        ("{a:bool}", {"a": ["foo"]}, "a"),
        ("{a:bool}b", {"a": False}, "b"),
        ("{a:bool}b", {"a": []}, "b"),
        ("{a:bool}b", {"a": ""}, "b"),
        # default formatter (str)
        ("{a:}", {"a": False}, "False"),
        ("{a:}", {"a": []}, "[]"),
        ("{a:}", {"a": ""}, ""),
        # join formatter -> "".join(param[name])
        ("{a:join}", {"a": []}, ""),
        # join leaves non-str, non-iterable intact
        ("{a:join}", {"a": False}, "False"),
        # join leaves str intact
        ("{a:join}", {"a": "whole string"}, "whole string"),
        ("{a:join}", {"a": ["a", "b"]}, "ab"),
        ("{a:join}", {"a": ""}, ""),
        # join converts non-str before joining
        ("{a:join}", {"a": [1, 2]}, "12"),
        # comma formatter -> ",".join(param[name])
        ("{a:comma}", {"a": []}, ""),
        # comma leaves non-str, non-iterable intact
        ("{a:comma}", {"a": False}, "False"),
        # comma leaves str intact
        ("{a:comma}", {"a": "whole string"}, "whole string"),
        ("{a:comma}", {"a": ["a", "b"]}, "a,b"),
        ("{a:comma}", {"a": ""}, ""),
        # comma converts non-str before joining
        ("{a:comma}", {"a": [1, 2]}, "1,2"),
        # space formatter -> " ".join(param[name])
        ("{a:space}", {"a": []}, ""),
        # space leaves non-str, non-iterable intact
        ("{a:space}", {"a": False}, "False"),
        # space leaves str intact
        ("{a:space}", {"a": "whole string"}, "whole string"),
        ("{a:space}", {"a": ["a", "b"]}, "a b"),
        ("{a:space}", {"a": ""}, ""),
        # space converts non-str before joining
        ("{a:space}", {"a": [1, 2]}, "1 2"),
        # successful guards
        ("{a:nospace}", {"a": "ab"}, "ab"),
        ("{a:nospace}", {"a": True}, "True"),
        ("{a:nospace}", {"a": ""}, ""),
    ],
)
def test_global_serializer_formatters(template: str, params: dict, expected: str) -> None:
    command = "foo"
    module_register(command, template)
    actual = module_serialize(command, params)
    assert actual == expected


@pytest.mark.parametrize(
    ("template", "params", "expected_exception"),
    [
        ("{x:nospace}", {"x": "foo bar"}, ValueError),
        # object whose __str__ has a space
        ("{x:nospace}", {"x": object()}, ValueError),
        # bool formatter uses bool(param[name])
    ],
)
def test_default_serializer_guards(template: str, params: dict, expected_exception: type[Exception]) -> None:
    command = "foo"
    module_register(command, template)
    with pytest.raises(expected_exception):
        module_serialize(command, params)
