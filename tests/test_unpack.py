from bottom.unpack import unpack_command
import pytest


def test_no_command():

    ''' raise when command is None or empty '''

    with pytest.raises(TypeError):
        unpack_command(None)

    with pytest.raises(ValueError):
        unpack_command("")


def test_bad_command():

    ''' raise when command is incorrectly formatted '''

    with pytest.raises(ValueError):
        unpack_command(":prefix_only")


def test_unknown_command():

    ''' raise when command isn't known '''

    with pytest.raises(ValueError):
        unpack_command("unknown_command")


def test_ignore_case():

    ''' input case doesn't matter '''

    assert ("PING", {"message": "m"}) == unpack_command("pInG :m")
