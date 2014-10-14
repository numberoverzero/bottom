from bottom import rfc


def test_unique_command():

    ''' handle various cases, numeric codes, unknown commands '''
    tests = [
        ("RPL_WELCOME", "RPL_WELCOME"),  # Defined code
        ("Rpl_WElcOME", "RPL_WELCOME"),  # Defined code, case
        ("001", "RPL_WELCOME"),  # Numeric code
        ("UNKNOWN", "UNKNOWN"),  # Undefined code
        ("unknown", "UNKNOWN"),  # Undefined code, case
    ]

    for command, expected in tests:
        assert rfc.unique_command(command) == expected


def test_wire_command():

    ''' handle various cases, numeric codes, unknown commands '''
    tests = [
        ("RPL_WELCOME", "001"),  # Defined code
        ("Rpl_WElcOME", "001"),  # Defined code, case
        ("001", "001"),          # Numeric code
        ("UNKNOWN", "UNKNOWN"),  # Undefined code
        ("unknown", "UNKNOWN"),  # Undefined code, case
    ]

    for command, expected in tests:
        assert rfc.wire_command(command) == expected


def test_wire_format_args():

    ''' all arguments provided '''
    tests = [
        (("B", [],           "",  ""),   "B"),
        (("B", [],           "",  "a"),  ":a B"),
        (("B", ["c"],        "",  "a"),  ":a B c"),
        (("B", [],           "d", "a"),  ":a B :d"),
        (("B", ["c"],        "d", "a"),  ":a B c :d"),
        (("B", ["c"],        "",  ""),   "B c"),
        (("B", [],           "d", ""),   "B :d"),
        (("B", ["c"],        "d", ""),   "B c :d"),
        (("B", ["c1", "c2"], "",  ""),   "B c1 c2"),
    ]

    for args, expected in tests:
        assert rfc.wire_format(*args) == expected


def test_wire_format_kwargs():

    ''' some arguments provided '''
    tests = [
        ({
            "command": "b"}, "B"),
        ({
            "command": "b",
            "params": ["c1", "c2"]}, "B c1 c2"),
        ({
            "command": "b",
            "message": "d"}, "B :d"),
        ({
            "command": "b",
            "prefix": "a"}, ":a B"),
        ({
            "command": "b",
            "params": ["c1", "c2"],
            "message": "d"}, "B c1 c2 :d"),
        ({
            "command": "b",
            "message": "d",
            "prefix": "a"}, ":a B :d"),
        ({
            "command": "b",
            "params": ["c1", "c2"],
            "prefix": "a"}, ":a B c1 c2"),
        ({
            "command": "b",
            "params": ["c1", "c2"],
            "message": "d",
            "prefix": "a"}, ":a B c1 c2 :d")
    ]

    for kwargs, expected in tests:
        assert rfc.wire_format(**kwargs) == expected


def test_parse_invalid_lines():

    ''' non-conforming strings parse as None '''

    invalid_lines = [
        "",
        ":",
        ":a",
        "a:b"
    ]

    for line in invalid_lines:
        assert rfc.parse(line) is None


def test_parse_valid_lines():

    ''' conforming strings'''

    valid_lines = [
        ("b",         ("",  "B", [],           "")),
        (":a b",      ("a", "B", [],           "")),
        (":a b c",    ("a", "B", ["c"],        "")),
        (":a b :d",   ("a", "B", [],           "d")),
        (":a b c :d", ("a", "B", ["c"],        "d")),
        ("b c",       ("",  "B", ["c"],        "")),
        ("b :d",      ("",  "B", [],           "d")),
        ("b c :d",    ("",  "B", ["c"],        "d")),
        ("b c1 c2",   ("",  "B", ["c1", "c2"], "")),
    ]

    for line, expected in valid_lines:
        assert rfc.parse(line) == expected
