import typing as t
from dataclasses import dataclass, field

import pytest
from bottom.irc.serialize import CommandSerializer
from bottom.irc.serialize import register_serializer_pattern as module_register
from bottom.irc.serialize import serialize as module_serialize


@dataclass(frozen=True)
class SerializerTestPattern:
    fmt: str
    req: set[str] = field(default_factory=set)
    defaults: dict[str, t.Any] = field(default_factory=dict)
    deps: dict[str, str] = field(default_factory=dict)

    def register_into(self, command: str, serializer: CommandSerializer) -> None:
        serializer.register(
            command,
            fmt=self.fmt,
            req=self.req,
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
            stp("1 {a} {b}", req={"a", "b"}),
            stp("2 {a} {b}", req={"a"}, defaults={"b": "def:b"}),
        ],
        kw_params={"a": "kw:a"},
        expected="2 kw:a def:b",
    ),
    SerializerTestCase(
        # on ties, first registered wins
        patterns=[
            stp("1 {a} {b}", req={"a", "b"}),
            stp("2 {a} {b}", req={"a", "b"}),
        ],
        kw_params={"a": "kw:a", "b": "kw:b"},
        expected="1 kw:a kw:b",
    ),
    SerializerTestCase(
        # defaults count towards score, before tie breaks
        patterns=[
            stp("1 {a} {b}", req={"a", "b"}),
            stp("2 {a} {b} {c}", req={"a", "b"}, defaults={"c": "def:c"}),
        ],
        kw_params={"a": "kw:a", "b": "kw:b"},
        expected="2 kw:a kw:b def:c",
    ),
    SerializerTestCase(
        # required doesn't score higher than defaults; ordering still tie breaks
        patterns=[
            stp("1 {a} {b}", defaults={"a": "def:a", "b": "def:b"}),
            stp("2 {b} {c}", req={"b"}, defaults={"c": "def:c"}),
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
        # params unused in format string still count (but should probably be a bug)
        # note: tie breaking on order since both provide all of a, b, c
        patterns=[
            stp("1 {a}", req={"a", "b", "c"}),
            stp("2 {a} {b} {c}", defaults={"a": "def:a", "b": "def:b", "c": "def:c"}),
        ],
        kw_params={"a": "kw:a", "b": "kw:b", "c": "kw:c"},
        expected="1 kw:a",
    ),
    SerializerTestCase(
        # first pattern has more matched but missing dependency
        patterns=[
            stp("1 {a} {b} {c}", deps={"a": "c"}),
            stp("2 {a}", {"a"}),
        ],
        kw_params={"a": "kw:a", "b": "kw:b"},
        expected="2 kw:a",
    ),
    SerializerTestCase(
        # dependency-only gets an empty string when not provided
        # otherwise, the string template would break
        patterns=[
            stp("1 {a} {b} {c}", req={"a"}, deps={"b": "a", "c": "a"}),
        ],
        kw_params={"a": "kw:a"},
        expected="1 kw:a",
    ),
]


@pytest.fixture
def serializer() -> CommandSerializer:
    return CommandSerializer()


@pytest.mark.parametrize("command", ["hello", "HAS SPACES"])
@pytest.mark.parametrize(
    ("kw_params"),
    [
        {},
        {"foo": "bar"},
        {"hello": object()},
        {"world": str},
    ],
)
def test_no_params(serializer, command, kw_params: dict) -> None:
    serializer.register(command, command, set(), {}, {})
    assert serializer.serialize(command, kw_params) == command


@pytest.mark.parametrize("case", serializer_test_cases)
def test_serializer_cases(serializer, case: SerializerTestCase) -> None:
    command = "foo"
    for pattern in case.patterns:
        pattern.register_into(command, serializer)
    assert serializer.serialize(command, case.kw_params) == case.expected


def test_serializer_unknown_command(serializer) -> None:
    with pytest.raises(ValueError):
        serializer.serialize("unknown", {})


def test_serializer_missing_args(serializer) -> None:
    """knows command but none have all reqs satisfied by kw_params"""
    command = "foo"
    serializer.register(command, "1 {a} {b}", {"a", "b"}, {}, {})
    with pytest.raises(ValueError):
        serializer.serialize(command, {"a": "kw:a"})


def test_default_serializer(serializer) -> None:
    """module-level serialize function defaults to a global serializer"""

    command = "foo"
    pattern = stp("1 {a}", req={"a"}, defaults={}, deps={})
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
    module_register(command, fmt=pattern.fmt, req=pattern.req, defaults=pattern.defaults, deps=pattern.deps)
    actual = module_serialize(command, kw_params)
    assert actual == expected
