# ============================================================================
# tests for specific commands
# serialization primitives tests live in test_serialize.py
# ============================================================================
from tests.helpers.base_classes import BaseSerializeTest


class Test_WHOWAS(BaseSerializeTest):
    # WHOWAS <nick> [<count> [<target>]]
    command = "WHOWAS"
    arg_map = [
        ("nick", "n0"),
        ("count", 3),
        ("target", "eff.org"),
    ]
    expected_map = {
        "ERR": ValueError,
        "nick": "WHOWAS n0",
        "count": "WHOWAS n0 3",
        "all": "WHOWAS n0 3 eff.org",
    }
    permutations = {
        (): "ERR",
        (1): "ERR",
        (2): "ERR",
        (1, 2): "ERR",
        (0): "nick",
        (0, 1): "count",
        (0, 2): "nick",
        (0, 1, 2): "all",
    }
