import typing as t

import pytest
from bottom.irc.serialize import GLOBAL_COMMAND_SERIALIZER, CommandSpec


@pytest.fixture(autouse=True)
def _reset_global_serializer(request: pytest.FixtureRequest) -> t.Iterable[None]:
    new: list[tuple[str, CommandSpec]] = []
    original_register = GLOBAL_COMMAND_SERIALIZER.register

    def register(command: str, fmt: str, defaults: dict[str, t.Any], deps: dict[str, str]) -> CommandSpec:
        command = command.strip().upper()
        spec = original_register(command, fmt=fmt, defaults=defaults, deps=deps)
        new.append((command, spec))
        return spec

    GLOBAL_COMMAND_SERIALIZER.register = register  # ty: ignore
    try:
        yield
    finally:
        GLOBAL_COMMAND_SERIALIZER.register = original_register  # ty: ignore
        to_cleanup = new[:]
        new.clear()
        for command, spec in to_cleanup:
            try:
                GLOBAL_COMMAND_SERIALIZER.commands[command].remove(spec)
            except Exception as exc:
                msg = f"failed to remove spec ({command}, {spec}) while resetting global serializer"
                raise RuntimeError(msg) from exc
