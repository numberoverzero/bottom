import re

import pytest
from bottom.pack import pack_command

SPACES = re.compile(r"(\\?\s+)+")


def like(pattern, value):
    """ helper for ignoring extra spaces between arguments """
    # Escape special characters like : and *
    pattern = re.escape(pattern)
    # Split on : so we don't replace spaces in messages
    index = pattern.rfind(':')
    if index >= 0:
        pattern = SPACES.sub(r'\\s+', pattern[:index]) + pattern[index:]
    else:
        pattern = SPACES.sub(r'\\s+', pattern)
    # Ignore trailing spaces/newlines
    pattern += r"\s*?"
    return bool(re.match(pattern, value))


def test_no_command():

    """ raise when command is None or empty """

    with pytest.raises(ValueError):
        pack_command(None)

    with pytest.raises(ValueError):
        pack_command("")


def test_bad_command():

    """ raise when command doesn't have upper """

    with pytest.raises(ValueError):
        pack_command(object())


def test_unknown_command():

    """ raise when command isn't known """

    with pytest.raises(ValueError):
        pack_command("unknown_command", param="foo")


def test_ignore_case():

    """ input case doesn't matter """

    assert "PASS foo" == pack_command("pASs", password="foo")

# =====================================
# Specific command tests start here
# =====================================


def test_pass():
    """ PASS command """
    assert like("PASS foo", pack_command("PASS", password="foo"))


def test_nick():
    """ NICK command """
    assert like("NICK foo", pack_command("NICK", nick="foo"))


def test_user():
    """ USER command """
    assert like("USER user 1 * :real", pack_command("USER", user="user",
                                                    realname="real", mode=1))
    assert like("USER user 0 * :real", pack_command("USER", user="user",
                                                    realname="real"))


def test_oper():
    """ OPER command """
    assert like("OPER user pass", pack_command("OPER", user="user",
                                               password="pass"))


def test_usermode():
    """ USERMODE command """
    assert like("MODE nick +w", pack_command("USERMODE",
                                             nick="nick", modes="+w"))


def test_service():
    """ SERVICE command """
    assert like("SERVICE nick * distribution type 0 :info", pack_command(
        "SERVICE", nick="nick", distribution="distribution",
        type="type", info="info"))


def test_quit():
    """ QUIT command """
    assert like("QUIT", pack_command("QUIT"))
    assert like("QUIT :message", pack_command("QUIT", message="message"))


def test_squit():
    """ SQUIT command """
    assert like("SQUIT s.edu", pack_command("SQUIT", server="s.edu"))
    assert like("SQUIT s.edu :msg", pack_command("SQUIT", server="s.edu",
                                                 message="msg"))


def test_join():
    """ JOIN command """
    assert like("JOIN 0", pack_command("JOIN", channel=0))
    assert like("JOIN #chan", pack_command("JOIN", channel="#chan"))
    assert like("JOIN #chan key", pack_command("JOIN", channel="#chan",
                                               key="key"))
    assert like("JOIN ch1,ch2", pack_command("JOIN", channel=["ch1", "ch2"]))
    assert like("JOIN ch1,ch2 k1,k2", pack_command("JOIN",
                                                   channel=["ch1", "ch2"],
                                                   key=["k1", "k2"]))


def test_part():
    """ PART command """
    assert like("PART #chan", pack_command("PART", channel="#chan"))
    assert like("PART #chan :msg", pack_command("PART", channel="#chan",
                                                message="msg"))
    assert like("PART ch1,ch2", pack_command("PART", channel=["ch1", "ch2"]))
    assert like("PART ch1,ch2 :msg", pack_command("PART",
                                                  channel=["ch1", "ch2"],
                                                  message="msg"))


def test_channelmode():
    """ CHANNELMODE command """
    assert like("MODE #Finnish +imI *!*@*.fi", pack_command(
        "CHANNELMODE", channel="#Finnish", modes="+imI", params="*!*@*.fi"))
    assert like("MODE #en-ops +v WiZ", pack_command(
        "CHANNELMODE", channel="#en-ops", modes="+v", params="WiZ"))
    # CHANNELMODE #Fins -s
    assert like("MODE #Fins -s", pack_command(
        "CHANNELMODE", channel="#Fins", modes="-s"))


def test_topic():
    """ TOPIC command """
    assert like("TOPIC #test :New topic", pack_command(
        "TOPIC", channel="#test", message="New topic"))
    assert like("TOPIC #test :", pack_command("TOPIC", channel="#test",
                                              message=""))
    assert like("TOPIC #test", pack_command("TOPIC", channel="#test"))


def test_names():
    """ NAMES command """
    assert like("NAMES #twilight", pack_command("NAMES", channel="#twilight"))
    assert like("NAMES #ch1,#ch2", pack_command("NAMES",
                                                channel=["#ch1", "#ch2"]))
    assert like("NAMES", pack_command("NAMES"))


def test_list():
    """ LIST command """
    assert like("LIST #twilight", pack_command("LIST", channel="#twilight"))
    assert like("LIST #ch1,#ch2", pack_command(
        "LIST", channel=["#ch1", "#ch2"]))
    assert like("LIST", pack_command("LIST"))


def test_invite():
    """ INVITE command """
    assert like("INVITE nick #ch", pack_command("INVITE", nick="nick",
                                                channel="#ch"))


def test_command():
    """ KICK command """
    assert like("KICK #Finnish WiZ", pack_command(
        "KICK", channel="#Finnish", nick="WiZ"))
    assert like("KICK #Finnish WiZ :Speaking English", pack_command(
        "KICK", channel="#Finnish", nick="WiZ", message="Speaking English"))
    assert like("KICK #Finnish WiZ,Wiz-Bot :msg", pack_command(
        "KICK", channel="#Finnish", nick=["WiZ", "Wiz-Bot"], message="msg"))
    assert like("KICK #ch1,#ch2 n1,n2 :msg", pack_command(
        "KICK", channel=["#ch1", "#ch2"], nick=["n1", "n2"], message="msg"))


def test_privmsg():
    """ PRIVMSG command """
    assert like("PRIVMSG #ch :hello, world", pack_command(
        "PRIVMSG", target="#ch", message="hello, world"))
    assert like("PRIVMSG WiZ :hello, world", pack_command(
        "PRIVMSG", target="WiZ", message="hello, world"))


def test_notice():
    """ NOTICE command """
    assert like("NOTICE #ch :hello, world", pack_command(
        "NOTICE", target="#ch", message="hello, world"))
    assert like("NOTICE WiZ :hello, world", pack_command(
        "NOTICE", target="WiZ", message="hello, world"))


def test_motd():
    """ MOTD command """
    assert like("MOTD", pack_command("MOTD"))


def test_lusers():
    """ LUSERS command """
    assert like("LUSERS", pack_command("LUSERS"))
    assert like("LUSERS *.edu", pack_command("LUSERS", mask="*.edu"))


def test_version():
    """ VERSION command """
    assert like("VERSION", pack_command("VERSION"))


def test_stats():
    """ STATS command """
    assert like("STATS", pack_command("STATS"))
    assert like("STATS m", pack_command("STATS", query="m"))


def test_links():
    """ LINKS command """
    assert like("LINKS *.edu *.bu.edu", pack_command("LINKS", remote="*.edu",
                                                     mask="*.bu.edu"))
    assert like("LINKS *.au", pack_command("LINKS", mask="*.au"))
    assert like("LINKS", pack_command("LINKS"))

    with pytest.raises(KeyError):
        pack_command("LINKS", remote="*.edu")


def test_time():
    """ TIME command """
    assert like("TIME", pack_command("TIME"))


def test_connect():
    """ CONNECT command """
    assert like("CONNECT tolsun.oulu.fi 6667 *.edu", pack_command(
        "CONNECT", target="tolsun.oulu.fi", port=6667, remote="*.edu"))
    assert like("CONNECT tolsun.oulu.fi 6667", pack_command(
        "CONNECT", target="tolsun.oulu.fi", port=6667))


def test_trace():
    """ TRACE command """
    assert like("TRACE", pack_command("TRACE"))


def test_admin():
    """ ADMIN command """
    assert like("ADMIN", pack_command("ADMIN"))


def test_info():
    """ INFO command """
    assert like("INFO", pack_command("INFO"))


def test_servlist():
    """ SERVLIST command """
    assert like("SERVLIST *SERV 3", pack_command("SERVLIST",
                                                 mask="*SERV", type=3))
    assert like("SERVLIST *SERV", pack_command("SERVLIST", mask="*SERV"))
    assert like("SERVLIST", pack_command("SERVLIST"))


def test_squery():
    """ SQUERY command """
    assert like("SQUERY irchelp :HELP privmsg", pack_command(
        "SQUERY", target="irchelp", message="HELP privmsg"))


def test_who():
    """ WHO command """
    assert like("WHO jto* o", pack_command("WHO", mask="jto*", o=True))
    assert like("WHO *.fi", pack_command("WHO", mask="*.fi"))
    assert like("WHO", pack_command("WHO"))


def test_whois():
    """ WHOIS command """
    assert like("WHOIS jto* o", pack_command("WHOIS", mask="jto* o"))
    assert like("WHOIS *.fi", pack_command("WHOIS", mask="*.fi"))


def test_whowas():
    """ WHOWAS command """
    assert like("WHOWAS WiZ 9", pack_command("WHOWAS", nick="WiZ", count=9))
    assert like("WHOWAS WiZ", pack_command("WHOWAS", nick="WiZ"))


def test_kill():
    """ KILL command """
    assert like("KILL WiZ :Spamming joins", pack_command(
        "KILL", nick="WiZ", message="Spamming joins"))


def test_ping():
    """ PING command """
    assert like("PING :msg", pack_command("PING", message="msg"))
    assert like("PING", pack_command("PING"))


def test_pong():
    """ PONG command """
    assert like("PONG :msg", pack_command("PONG", message="msg"))
    assert like("PONG", pack_command("PONG"))


def test_away():
    """ AWAY command """
    assert like("AWAY :msg", pack_command("AWAY", message="msg"))
    assert like("AWAY", pack_command("AWAY"))


def test_rehash():
    """ REHASH command """
    assert like("REHASH", pack_command("REHASH"))


def test_die():
    """ DIE command """
    assert like("DIE", pack_command("DIE"))


def test_restart():
    """ RESTART command """
    assert like("RESTART", pack_command("RESTART"))


def test_summon():
    """ SUMMON command """
    assert like("SUMMON Wiz remote.*.edu #Finnish", pack_command(
        "SUMMON", nick="Wiz", target="remote.*.edu", channel="#Finnish"))
    assert like("SUMMON Wiz remote.*.edu", pack_command(
        "SUMMON", nick="Wiz", target="remote.*.edu"))
    assert like("SUMMON Wiz", pack_command(
        "SUMMON", nick="Wiz"))


def test_users():
    """ USERS command """
    assert like("USERS", pack_command("USERS"))


def test_wallops():
    """ WALLOPS command """
    assert like("WALLOPS :msg", pack_command("WALLOPS", message="msg"))


def test_userhost():
    """ USERHOST command """
    assert like("USERHOST Wiz Michael syrk", pack_command(
        "USERHOST", nick=["Wiz", "Michael", "syrk"]))
    assert like("USERHOST syrk", pack_command(
        "USERHOST", nick="syrk"))


def test_ison():
    """ ISON command """
    assert like("ISON Wiz Michael syrk", pack_command(
        "ISON", nick=["Wiz", "Michael", "syrk"]))
    assert like("ISON syrk", pack_command(
        "ISON", nick="syrk"))
