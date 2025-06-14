import typing as t

import pytest
from bottom.irc.serialize import serialize

type ClassArgs = list[tuple[str, t.Any]]
type ClassExpected = dict[str, str | type[Exception]]
type ClassPermutations = dict[tuple | int, str]


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if metafunc.cls and issubclass(metafunc.cls, BaseTest):
        metafunc.cls.generate_tests(metafunc)


class BaseTest:
    """
    Base class for any test suite that wants to generate test parameters.

    The class's `generate_tests` will only be called when a test within that
    class is running.

    That filtering is done in tests/conftest.py::pytest_generate_tests
    """

    @classmethod
    def generate_tests(cls, metafunc: pytest.Metafunc) -> None:
        raise NotImplementedError


class BaseSerializeTest(BaseTest):
    command: t.ClassVar[str]
    arg_map: t.ClassVar[ClassArgs]
    expected_map: t.ClassVar[ClassExpected]
    permutations: t.ClassVar[ClassPermutations]

    def test_permutation(self, params: dict, expected: str | type[Exception]) -> None:
        if isinstance(expected, str):
            actual = serialize(self.command, params)
            assert actual == expected
        else:
            with pytest.raises(expected):
                serialize(self.command, params)

    @classmethod
    def generate_tests(cls, metafunc: pytest.Metafunc) -> None:
        argnames = ("params", "expected")
        argvalues = []
        for param_keys, expected_key in cls.permutations.items():
            argvalues.append(
                (
                    cls.build_params(param_keys),
                    cls.expected_map[expected_key],
                )
            )
        metafunc.parametrize(argnames, argvalues)

    @classmethod
    def build_params(cls, param_keys: int | tuple[int, ...]) -> dict[str, t.Any]:
        """
        Convert a list of arg indexes into a dict.

        (0, 1, 2, 3) -> {arg_map[0].name: arg_map[0].value, ..., arg_map[3].name: arg_map[3].value}
        """
        params = dict()
        if isinstance(param_keys, int):
            param_keys = (param_keys,)

        for index in param_keys:
            arg_spec = cls.arg_map[index]
            if len(arg_spec) == 2:
                name, value = arg_spec
            else:
                loc = f"{cls.__name__}.arg_map[{index}]"
                raise RuntimeError(f"{loc} had unexpected arg_spec: {arg_spec!r}")
            params[name] = value
        return params
