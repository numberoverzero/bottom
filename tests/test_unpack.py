from bottom.unpack import unpack_command, parameters, synonym
import pytest


def test_no_command():
    ''' raise when command is None or empty '''
    with pytest.raises(AttributeError):
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
    with pytest.raises(ValueError):
        parameters("unknown_command")


def test_ignore_case():
    ''' input case doesn't matter '''
    assert ("PING", {"message": "m"}) == unpack_command("pInG :m")


def test_synonym():
    ''' numeric -> string '''
    # Defined commands
    assert synonym("001") == synonym("RPL_WELCOME") == "RPL_WELCOME"
    # Unkown, even impossible commands
    assert synonym("!@#test") == synonym("!@#TEST") == "!@#TEST"


# =====================================
# Specific command tests start here
# =====================================


def validate(command, message, expected_kwargs):
    ''' Basic case - expected_kwargs expects all parameters of the command '''
    assert (command, expected_kwargs) == unpack_command(message)
    assert set(expected_kwargs) == set(parameters(command))


def test_client_commands():
    ''' CLIENT_CONNECT and CLIENT_DISCONNECT '''
    expected = set(["host", "port"])
    assert expected == set(parameters("CLIENT_CONNECT"))
    assert expected == set(parameters("CLIENT_DISCONNECT"))


def test_ping():
    ''' PING command '''
    command = "PING"
    message = "PING :ping msg"
    expected_kwargs = {"message": "ping msg"}
    validate(command, message, expected_kwargs)


def test_privmsg():
    ''' PRIVMSG command '''
    command = "PRIVMSG"
    message = ":n!u@h PRIVMSG #t :m"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "message": "m", "target": "#t"}
    validate(command, message, expected_kwargs)


def test_notice():
    ''' NOTICE command '''
    command = "NOTICE"
    message = ":n!u@h NOTICE #t :m"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "message": "m", "target": "#t"}
    validate(command, message, expected_kwargs)

    # server notice - can't use validate since not all params are defined
    message = ":some.host.edu NOTICE #t :m"
    expected_kwargs = {"host": "some.host.edu", "message": "m", "target": "#t"}
    assert (command, expected_kwargs) == unpack_command(message)


def test_join():
    ''' JOIN command '''
    command = "JOIN"
    message = ":n!u@h JOIN #c"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "channel": "#c"}
    validate(command, message, expected_kwargs)


def test_part():
    ''' PART command '''
    command = "PART"
    message = ":n!u@h PART #c :m"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "channel": "#c", "message": "m"}
    validate(command, message, expected_kwargs)


def test_message_commands():
    ''' message-only commands '''
    cmds = ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD", "RPL_WELCOME",
            "RPL_YOURHOST", "RPL_CREATED", "RPL_LUSERCLIENT", "RPL_LUSERME"]
    expected_kwargs = {"message": "m"}
    for command in cmds:
        message = command + " :m"
        validate(command, message, expected_kwargs)


def test_count_commands():
    ''' count + message commands '''
    cmds = ["RPL_LUSEROP", "RPL_LUSERUNKNOWN", "RPL_LUSERCHANNELS"]
    expected_kwargs = {"message": "m", "count": 3}
    for command in cmds:
        message = "{} nick 3 :m".format(command)
        validate(command, message, expected_kwargs)


def test_info_commands():
    ''' *info + message commands '''
    cmds = ["RPL_MYINFO", "RPL_BOUNCE"]
    expected_kwargs = {"message": "m", "info": ["one", "two", "three"]}
    for command in cmds:
        message = "{} nick one two three :m".format(command)
        validate(command, message, expected_kwargs)
