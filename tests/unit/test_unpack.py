from bottom.unpack import unpack_command, parameters, synonym
import pytest


def test_no_command():
    """ raise when command is None or empty """
    with pytest.raises(AttributeError):
        unpack_command(None)
    with pytest.raises(ValueError):
        unpack_command("")


def test_bad_command():
    """ raise when command is incorrectly formatted """
    with pytest.raises(ValueError):
        unpack_command(":prefix_only")


def test_unknown_command():
    """ raise when command isn't known """
    with pytest.raises(ValueError):
        unpack_command("unknown_command")
    with pytest.raises(ValueError):
        parameters("unknown_command")


def test_ignore_case():
    """ input case doesn't matter """
    assert ("PING", {"message": "m"}) == unpack_command("pInG :m")


def test_synonym():
    """ numeric -> string """
    # Defined commands
    assert synonym("001") == synonym("RPL_WELCOME") == "RPL_WELCOME"
    # Unknown, even impossible commands
    assert synonym("!@#test") == synonym("!@#TEST") == "!@#TEST"


def validate(command, message, expected_kwargs):
    """ Basic case - expected_kwargs expects all parameters of the command """
    assert (command, expected_kwargs) == unpack_command(message)
    assert set(expected_kwargs) == set(parameters(command))


def test_param_positioning():
    """use of : shouldn't matter when parsing args"""
    command = "PING"
    message = "PING this_is_message"
    expected_kwargs = {"message": "this_is_message"}
    validate(command, message, expected_kwargs)

    command = "PING"
    message = "PING :this_is_message"
    expected_kwargs = {"message": "this_is_message"}
    validate(command, message, expected_kwargs)


# =====================================
# Specific command tests start here
# =====================================


def test_client_commands():
    """ CLIENT_CONNECT and CLIENT_DISCONNECT """
    expected = set(["host", "port"])
    assert expected == set(parameters("CLIENT_CONNECT"))
    assert expected == set(parameters("CLIENT_DISCONNECT"))


def test_ping():
    """ PING command """
    command = "PING"
    message = "PING :ping msg"
    expected_kwargs = {"message": "ping msg"}
    validate(command, message, expected_kwargs)


def test_privmsg():
    """ PRIVMSG command """
    command = "PRIVMSG"
    message = ":n!u@h PRIVMSG #t :m"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "message": "m", "target": "#t"}
    validate(command, message, expected_kwargs)


def test_notice():
    """ NOTICE command """
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
    """ JOIN command """
    command = "JOIN"
    message = ":n!u@h JOIN #c"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "channel": "#c"}
    validate(command, message, expected_kwargs)


def test_nick():
    """ NICK command """
    command = "NICK"
    message = ":n!u@h NICK new_user_nick"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "new_nick": "new_user_nick"}
    validate(command, message, expected_kwargs)


def test_quit():
    """ QUIT command """
    command = "QUIT"
    message = ":n!u@h QUIT :m"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "message": "m"}
    validate(command, message, expected_kwargs)


def test_quit_no_msg():
    """ QUIT command """
    command = "QUIT"
    message = ":n!u@h QUIT"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "message": ""}
    validate(command, message, expected_kwargs)


def test_part():
    """ PART command """
    command = "PART"
    message = ":n!u@h PART #c :m"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "channel": "#c", "message": "m"}
    validate(command, message, expected_kwargs)


def test_part_no_msg():
    """ PART command """
    command = "PART"
    message = ":n!u@h PART #c"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "channel": "#c", "message": ""}
    validate(command, message, expected_kwargs)


def test_invite():
    """ INVITE command """
    command = "INVITE"
    message = ":n!u@h INVITE n #c"
    expected_kwargs = {"nick": "n", "user": "u", "host": "h",
                       "target": "n", "channel": "#c"}
    validate(command, message, expected_kwargs)


def test_channel_message_commands():
    """ channel and message commands """
    cmds = ["RPL_TOPIC", "RPL_NOTOPIC", "RPL_ENDOFNAMES", "TOPIC"]
    expected_kwargs = {"channel": "#ch", "message": "m"}
    for command in cmds:
        message = command + " nick #ch :m"
        validate(command, message, expected_kwargs)
    # validate topic's optional message arg
    validate("TOPIC", "TOPIC nick #ch :", {"channel": "#ch", "message": ""})
    validate("TOPIC", "TOPIC nick #ch", {"channel": "#ch"})


def test_who_reply():
    """ WHO response """
    command = 'RPL_WHOREPLY'
    expected_kwargs = {"target": "#t", "channel": "#ch", "server": "srv",
                       "real_name": "rn", "host": "hst",
                       "nick": "nck", "hg_code": "H",
                       "hopcount": 27, "user": "usr"}
    message = command + " #t #ch usr hst srv nck H :27 rn"
    validate(command, message, expected_kwargs)


def test_end_of_who_reply():
    command = "RPL_ENDOFWHO"
    expected_kwargs = {"name": "#nm", "message": "m"}
    message = command + " #nm :m"
    validate(command, message, expected_kwargs)


def test_name_reply():
    command = "RPL_NAMREPLY"
    expected_kwargs = {"channel": "#ch", "target": "#t",
                       "users": ['aa', 'bb', 'cc'],
                       "channel_type": None}
    message = command + " #t #ch :aa bb cc"
    validate(command, message, expected_kwargs)


def test_name_reply_longer():
    command = "RPL_NAMREPLY"
    expected_kwargs = {"channel": "#ch", "target": "#t",
                       "users": ['aa', 'bb', 'cc'],
                       "channel_type": "="}
    message = command + " #t = #ch :aa bb cc"
    validate(command, message, expected_kwargs)


def test_message_commands():
    """ message-only commands """
    cmds = ["RPL_MOTDSTART", "RPL_MOTD", "RPL_ENDOFMOTD", "RPL_WELCOME",
            "RPL_YOURHOST", "RPL_CREATED", "RPL_LUSERCLIENT", "RPL_LUSERME",
            "ERR_NOMOTD"]
    expected_kwargs = {"message": "m"}
    for command in cmds:
        message = command + " :m"
        validate(command, message, expected_kwargs)


def test_count_commands():
    """ count + message commands """
    cmds = ["RPL_LUSEROP", "RPL_LUSERUNKNOWN", "RPL_LUSERCHANNELS"]
    expected_kwargs = {"message": "m", "count": 3}
    for command in cmds:
        message = "{} nick 3 :m".format(command)
        validate(command, message, expected_kwargs)


def test_count_commands_no_msg():
    """ count + message commands """
    cmds = ["RPL_LUSEROP", "RPL_LUSERUNKNOWN", "RPL_LUSERCHANNELS"]
    expected_kwargs = {"message": "", "count": 3}
    for command in cmds:
        message = "{} nick :3".format(command)
        validate(command, message, expected_kwargs)


def test_info_commands():
    """ *info + message commands """
    cmds = ["RPL_MYINFO", "RPL_BOUNCE"]
    expected_kwargs = {"message": "m", "info": ["one", "two", "three"]}
    for command in cmds:
        message = "{} nick one two three :m".format(command)
        validate(command, message, expected_kwargs)
