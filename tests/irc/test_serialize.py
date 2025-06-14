# ============================================================================
# tests for serialization primitives
# specific command tests live in test_serialize_rfc2812.py
# ============================================================================
import typing as t
from dataclasses import dataclass, field

import pytest
from bottom.irc.serialize import CommandSerializer, CommandSpec, SerializerTemplate
from bottom.irc.serialize import register_pattern as module_register
from bottom.irc.serialize import serialize as module_serialize


@dataclass(frozen=True)
class SerializerTestPattern:
    fmt: str
    defaults: dict[str, t.Any] = field(default_factory=dict)
    deps: dict[str, str] = field(default_factory=dict)

    def register_into(self, command: str, serializer: CommandSerializer) -> None:
        serializer.register(
            command,
            fmt=self.fmt,
            defaults=self.defaults,
            deps=self.deps,
        )


stp = SerializerTestPattern


@dataclass(frozen=True)
class SerializerTestCase:
    kw_params: dict
    expected: str
    # patterns: list[tuple[str, set[str], dict[str, t.Any], dict[str, str]]]
    patterns: list[SerializerTestPattern]


serializer_test_cases: list[SerializerTestCase] = [
    SerializerTestCase(
        # first missing required
        patterns=[
            stp("1 {a} {b}"),
            stp("2 {a} {b}", defaults={"b": "def:b"}),
        ],
        kw_params={"a": "kw:a"},
        expected="2 kw:a def:b",
    ),
    SerializerTestCase(
        # on ties, first registered wins
        patterns=[
            stp("1 {a} {b}"),
            stp("2 {a} {b}"),
        ],
        kw_params={"a": "kw:a", "b": "kw:b"},
        expected="1 kw:a kw:b",
    ),
    SerializerTestCase(
        # defaults count towards score, before tie breaks
        patterns=[
            stp("1 {a} {b}"),
            stp("2 {a} {b} {c}", defaults={"c": "def:c"}),
        ],
        kw_params={"a": "kw:a", "b": "kw:b"},
        expected="2 kw:a kw:b def:c",
    ),
    SerializerTestCase(
        # required doesn't score higher than defaults; ordering still tie breaks
        patterns=[
            stp("1 {a} {b}", defaults={"a": "def:a", "b": "def:b"}),
            stp("2 {b} {c}", defaults={"c": "def:c"}),
        ],
        kw_params={"b": "kw:b"},
        expected="1 def:a kw:b",
    ),
    SerializerTestCase(
        # when no params given, highest score is whichever has no reqs and
        # most defaults
        patterns=[
            stp("1 {a} {b}", defaults={"a": "def:a", "b": "def:b"}),
            stp("2 {a} {b} {c}", defaults={"a": "def:a", "b": "def:b", "c": "def:c"}),
        ],
        kw_params={},
        expected="2 def:a def:b def:c",
    ),
    SerializerTestCase(
        # first pattern has more matched but missing dependency
        patterns=[
            stp("1 {a} {b} {c}", deps={"a": "c"}),
            stp("2 {a}"),
        ],
        kw_params={"a": "kw:a", "b": "kw:b"},
        expected="2 kw:a",
    ),
    SerializerTestCase(
        # opt provides empty strings when missing
        patterns=[
            stp("1 {a}@{b:opt}@{c}"),
        ],
        kw_params={"a": "kw:a", "c": "kw:c"},
        expected="1 kw:a@@kw:c",
    ),
    SerializerTestCase(
        # forward dependency - relies on sorting the input to the deque
        patterns=[
            stp("1 {a}{b:opt}{c:opt}{z}", deps={"a": "z"}),
        ],
        kw_params={"a": "kw:a", "z": "kw:z"},
        expected="1 kw:akw:z",
    ),
]


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
    ],
)
def test_template_invalid_str(template) -> None:
    with pytest.raises(ValueError):
        SerializerTemplate.parse(template, {})


@pytest.mark.parametrize(
    ("template", "expected_req", "expected_opt"),
    [
        ("}}valid format str{{", set(), set()),
        ("{x:known_fn} recognized function", {"x"}, set()),
        ("{x:} every template supports empty string formatter", {"x"}, set()),
        ("{x:opt}", set(), {"x"}),
    ],
)
def test_template_valid_str(template: str, expected_req, expected_opt) -> None:
    tpl, req, opt = SerializerTemplate.parse(
        template,
        {"known_fn": lambda _, value: str(value)},
    )
    assert req == expected_req
    assert opt == expected_opt


@pytest.mark.parametrize(
    ("template", "expected"),
    [("}}ok{{", "}ok{"), ("foo bar", "foo bar")],
)
@pytest.mark.parametrize(
    "params",
    [{}, {"foo": "bar"}, {"hello": object()}, {"world": str}],
)
def test_template_no_params(template, expected, params: dict) -> None:
    tpl, _, _ = SerializerTemplate.parse(template, {})
    assert tpl.format(params) == expected


def test_template_chained_formats() -> None:
    # TODO
    pass


def test_command_spec_invalid_defaults() -> None:
    template, req, opt = SerializerTemplate.parse("{valid} {template}", {})
    with pytest.raises(ValueError):
        CommandSpec.parse("foo", template, req=req, opt=opt, defaults={"template": None}, deps={})


@pytest.mark.parametrize("case", serializer_test_cases)
def test_serializer_cases(serializer: CommandSerializer, case: SerializerTestCase) -> None:
    command = "foo"
    for pattern in case.patterns:
        pattern.register_into(command, serializer)
    assert serializer.serialize(command, case.kw_params) == case.expected


def test_serializer_unknown_command(serializer) -> None:
    with pytest.raises(ValueError):
        serializer.serialize("unknown", {})


def test_serializer_missing_args() -> None:
    """command is missing required params"""
    template, req, opt = SerializerTemplate.parse("{valid} {template}", {})
    command = CommandSpec.parse("foo", template=template, req=req, opt=opt, defaults={}, deps={})
    with pytest.raises(ValueError):
        command.serialize({"valid": "kw:a"})


def test_default_serializer(serializer: CommandSerializer) -> None:
    """module-level serialize function defaults to a global serializer"""

    command = "foo"
    pattern = stp("1 {a}")
    kw_params = {"a": "kw:a"}
    expected = "1 kw:a"

    # explicitly pass our serializer
    pattern.register_into(command, serializer)
    actual = module_serialize(command, kw_params, serializer=serializer)
    assert actual == expected

    # defaults to a serializer that doesn't know this command
    with pytest.raises(ValueError):
        module_serialize(command, kw_params)

    # register to global handler and it should succeed
    module_register(command, fmt=pattern.fmt, defaults=pattern.defaults, deps=pattern.deps)
    actual = module_serialize(command, kw_params)
    assert actual == expected


@pytest.mark.parametrize(
    ("template", "params", "expected"),
    [
        # bool formatter uses bool(param[name])
        ("{a:bool}", {"a": True}, "a"),
        ("{a:bool}", {"a": "foo"}, "a"),
        ("{a:bool}", {"a": ["foo"]}, "a"),
        ("{a:bool}b", {"a": False}, "b"),
        ("{a:bool}b", {"a": ""}, "b"),
        ("{a:bool}b", {"a": []}, "b"),
        # default formatter (str)
        ("{a:}", {"a": False}, "False"),
        ("{a:}", {"a": []}, "[]"),
        # join formatter -> "".join(param[name])
        ("{a:join}", {"a": []}, ""),
        ("{a:join}", {"a": ""}, ""),
        # join leaves non-str, non-iterable intact
        ("{a:join}", {"a": False}, "False"),
        # join leaves str intact
        ("{a:join}", {"a": "whole string"}, "whole string"),
        ("{a:join}", {"a": ["a", "b"]}, "ab"),
        # join converts non-str before joining
        ("{a:join}", {"a": [1, 2]}, "12"),
        # comma formatter -> ",".join(param[name])
        ("{a:comma}", {"a": []}, ""),
        ("{a:comma}", {"a": ""}, ""),
        # comma leaves non-str, non-iterable intact
        ("{a:comma}", {"a": False}, "False"),
        # comma leaves str intact
        ("{a:comma}", {"a": "whole string"}, "whole string"),
        ("{a:comma}", {"a": ["a", "b"]}, "a,b"),
        # comma converts non-str before joining
        ("{a:comma}", {"a": [1, 2]}, "1,2"),
        # space formatter -> " ".join(param[name])
        ("{a:space}", {"a": []}, ""),
        ("{a:space}", {"a": ""}, ""),
        # space leaves non-str, non-iterable intact
        ("{a:space}", {"a": False}, "False"),
        # space leaves str intact
        ("{a:space}", {"a": "whole string"}, "whole string"),
        ("{a:space}", {"a": ["a", "b"]}, "a b"),
        # space converts non-str before joining
        ("{a:space}", {"a": [1, 2]}, "1 2"),
        # successful guards
        ("{a:nospace}", {"a": ""}, ""),
        ("{a:nospace}", {"a": "ab"}, "ab"),
        ("{a:nospace}", {"a": True}, "True"),
    ],
)
def test_default_serializer_formatters(template: str, params: dict, expected: str) -> None:
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
