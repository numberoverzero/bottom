from bottom import route


def test_user_prefix():

    ''' nick, nick!user, nick!user@host '''

    tests = [
        ("", {}),
        ("nick", {"nick": "nick"}),
        ("nick!user", {"nick": "nick", "user": "user"}),
        ("nick!user@host", {"nick": "nick", "user": "user", "host": "host"}),
    ]

    for prefix, expected in tests:
        actual = {}
        route.user_prefix(prefix, actual)
        assert actual == expected
