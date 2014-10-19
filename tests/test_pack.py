from bottom.pack import pack_command
import pytest


def test_no_command():

    ''' raise when command is None or empty '''

    with pytest.raises(ValueError):
        pack_command(None)

    with pytest.raises(ValueError):
        pack_command("")


def test_bad_command():

    ''' raise when command doesn't have upper '''

    with pytest.raises(ValueError):
        pack_command(object())


def test_unknown_command():

    ''' raise when command isn't known '''

    with pytest.raises(ValueError):
        pack_command("unknown_command", param="foo")


def test_ignore_case():

    ''' input case doesn't matter '''

    assert "PASS foo" == pack_command("pASs", password="foo")

# =====================================
# Specific command tests start here
# =====================================


def test_pass():
    ''' PASS command '''
    assert "PASS foo" == pack_command("PASS", password="foo")


def test_nick():
    ''' NICK command '''
    assert "NICK foo" == pack_command("NICK", nick="foo")


def test_user():
    ''' USER command '''
    assert "USER user 1 * :real" == pack_command("USER", user="user",
                                                 realname="real", mode=1)
    assert "USER user 0 * :real" == pack_command("USER", user="user",
                                                 realname="real")


def test_oper():
    ''' OPER command '''
    assert "OPER user pass" == pack_command("OPER", user="user",
                                            password="pass")


def test_usermode():
    ''' USERMODE command '''
    assert "MODE nick +w" == pack_command("USERMODE", nick="nick", modes="+w")


def test_service():
    ''' SERVICE command '''
    assert "SERVICE nick * distribution type 0 :info" == pack_command(
        "SERVICE", nick="nick", distribution="distribution",
        type="type", info="info")


def test_quit():
    ''' QUIT command '''
    assert "QUIT" == pack_command("QUIT")
    assert "QUIT :message" == pack_command("QUIT", message="message")


def test_squit():
    ''' SQUIT command '''
    assert "SQUIT s.edu" == pack_command("SQUIT", server="s.edu")
    assert "SQUIT s.edu :msg" == pack_command("SQUIT", server="s.edu",
                                              message="msg")


def test_join():
    ''' JOIN command '''
    assert "JOIN 0" == pack_command("JOIN", channel=0)
    assert "JOIN #chan" == pack_command("JOIN", channel="#chan")
    assert "JOIN #chan key" == pack_command("JOIN", channel="#chan", key="key")
    assert "JOIN ch1,ch2" == pack_command("JOIN", channel=["ch1", "ch2"])
    assert "JOIN ch1,ch2 k1,k2" == pack_command("JOIN",
                                                channel=["ch1", "ch2"],
                                                key=["k1", "k2"])


def test_part():
    ''' PART command '''
    assert "PART #chan" == pack_command("PART", channel="#chan")
    assert "PART #chan :msg" == pack_command("PART", channel="#chan",
                                             message="msg")
    assert "PART ch1,ch2" == pack_command("PART", channel=["ch1", "ch2"])
    assert "PART ch1,ch2 :msg" == pack_command("PART", channel=["ch1", "ch2"],
                                               message="msg")


def test_channelmode():
    ''' CHANNELMODE command '''
    assert "MODE #Finnish +imI *!*@*.fi" == pack_command(
        "CHANNELMODE", channel="#Finnish", modes="+imI", params="*!*@*.fi")
    assert "MODE #en-ops +v WiZ" == pack_command(
        "CHANNELMODE", channel="#en-ops", modes="+v", params="WiZ")
    # CHANNELMODE #Fins -s
    assert "MODE #Fins -s" == pack_command(
        "CHANNELMODE", channel="#Fins", modes="-s")


def test_topic():
    ''' TOPIC command '''
    assert "TOPIC #test :New topic" == pack_command("TOPIC", channel="#test",
                                                    message="New topic")
    assert "TOPIC #test :" == pack_command("TOPIC", channel="#test",
                                           message="")
    assert "TOPIC #test" == pack_command("TOPIC", channel="#test")


def test_names():
    ''' NAMES command '''
    assert "NAMES #twilight" == pack_command("NAMES", channel="#twilight")
    assert "NAMES #ch1,#ch2" == pack_command("NAMES", channel=["#ch1", "#ch2"])
    assert "NAMES" == pack_command("NAMES")


def test_list():
    ''' LIST command '''
    assert "LIST #twilight" == pack_command("LIST", channel="#twilight")
    assert "LIST #ch1,#ch2" == pack_command("LIST", channel=["#ch1", "#ch2"])
    assert "LIST" == pack_command("LIST")


def test_invite():
    ''' INVITE command '''
    assert "INVITE nick #ch" == pack_command("INVITE", nick="nick",
                                             channel="#ch")


def test_command():
    ''' KICK command '''
    assert "KICK #Finnish WiZ" == pack_command(
        "KICK", channel="#Finnish", nick="WiZ")
    assert "KICK #Finnish WiZ :Speaking English" == pack_command(
        "KICK", channel="#Finnish", nick="WiZ", message="Speaking English")
    assert "KICK #Finnish WiZ,Wiz-Bot :msg" == pack_command(
        "KICK", channel="#Finnish", nick=["WiZ", "Wiz-Bot"], message="msg")
    assert "KICK #ch1,#ch2 n1,n2 :msg" == pack_command(
        "KICK", channel=["#ch1", "#ch2"], nick=["n1", "n2"], message="msg")


def test_privmsg():
    ''' PRIVMSG command '''
    assert "PRIVMSG #ch :hello, world" == pack_command(
        "PRIVMSG", target="#ch", message="hello, world")
    assert "PRIVMSG WiZ :hello, world" == pack_command(
        "PRIVMSG", target="WiZ", message="hello, world")


def test_notice():
    ''' NOTICE command '''
    assert "NOTICE #ch :hello, world" == pack_command(
        "NOTICE", target="#ch", message="hello, world")
    assert "NOTICE WiZ :hello, world" == pack_command(
        "NOTICE", target="WiZ", message="hello, world")


def test_motd():
    ''' MOTD command '''
    assert "MOTD" == pack_command("MOTD")


def test_lusers():
    ''' LUSERS command '''
    assert "LUSERS" == pack_command("LUSERS")
    assert "LUSERS *.edu" == pack_command("LUSERS", mask="*.edu")


def test_version():
    ''' VERSION command '''
    assert "VERSION" == pack_command("VERSION")


def test_stats():
    ''' STATS command '''
    assert "STATS" == pack_command("STATS")
    assert "STATS m" == pack_command("STATS", query="m")


def test_links():
    ''' LINKS command '''
    assert "LINKS *.edu *.bu.edu" == pack_command("LINKS", remote="*.edu",
                                                  mask="*.bu.edu")
    assert "LINKS *.au" == pack_command("LINKS", mask="*.au")
    assert "LINKS" == pack_command("LINKS")

    with pytest.raises(KeyError):
        pack_command("LINKS", remote="*.edu")


def test_time():
    ''' TIME command '''
    assert "TIME" == pack_command("TIME")


def test_connect():
    ''' CONNECT command '''
    assert "CONNECT tolsun.oulu.fi 6667 *.edu" == pack_command(
        "CONNECT", target="tolsun.oulu.fi", port=6667, remote="*.edu")
    assert "CONNECT tolsun.oulu.fi 6667" == pack_command(
        "CONNECT", target="tolsun.oulu.fi", port=6667)


def test_trace():
    ''' TRACE command '''
    assert "TRACE" == pack_command("TRACE")


def test_admin():
    ''' ADMIN command '''
    assert "ADMIN" == pack_command("ADMIN")


def test_info():
    ''' INFO command '''
    assert "INFO" == pack_command("INFO")


def test_servlist():
    ''' SERVLIST command '''
    assert "SERVLIST *SERV 3" == pack_command("SERVLIST", mask="*SERV", type=3)
    assert "SERVLIST *SERV" == pack_command("SERVLIST", mask="*SERV")
    assert "SERVLIST" == pack_command("SERVLIST")


def test_squery():
    ''' SQUERY command '''
    assert "SQUERY irchelp :HELP privmsg" == pack_command(
        "SQUERY", target="irchelp", message="HELP privmsg")


def test_who():
    ''' WHO command '''
    assert "WHO jto* o" == pack_command("WHO", mask="jto* o")
    assert "WHO *.fi" == pack_command("WHO", mask="*.fi")
    assert "WHO" == pack_command("WHO")


def test_whois():
    ''' WHOIS command '''
    assert "WHOIS jto* o" == pack_command("WHOIS", mask="jto* o")
    assert "WHOIS *.fi" == pack_command("WHOIS", mask="*.fi")


def test_whowas():
    ''' WHOWAS command '''
    assert "WHOWAS WiZ 9" == pack_command("WHOWAS", nick="WiZ", count=9)
    assert "WHOWAS WiZ" == pack_command("WHOWAS", nick="WiZ")


def test_kill():
    ''' KILL command '''
    assert "KILL WiZ :Spamming joins" == pack_command(
        "KILL", nick="WiZ", message="Spamming joins")


def test_pong():
    ''' PONG command '''
    assert "PONG :msg" == pack_command("PONG", message="msg")
    assert "PONG" == pack_command("PONG")


def test_away():
    ''' AWAY command '''
    assert "AWAY :msg" == pack_command("AWAY", message="msg")
    assert "AWAY" == pack_command("AWAY")


def test_rehash():
    ''' REHASH command '''
    assert "REHASH" == pack_command("REHASH")


def test_die():
    ''' DIE command '''
    assert "DIE" == pack_command("DIE")


def test_restart():
    ''' RESTART command '''
    assert "RESTART" == pack_command("RESTART")


def test_summon():
    ''' SUMMON command '''
    assert "SUMMON Wiz #Finnish" == pack_command(
        "SUMMON", nick="Wiz", channel="#Finnish")
    assert "SUMMON Wiz" == pack_command(
        "SUMMON", nick="Wiz")


def test_users():
    ''' USERS command '''
    assert "USERS" == pack_command("USERS")


def test_wallops():
    ''' WALLOPS command '''
    assert "WALLOPS :msg" == pack_command("WALLOPS", message="msg")


def test_userhost():
    ''' USERHOST command '''
    assert "USERHOST Wiz Michael syrk" == pack_command(
        "USERHOST", nick=["Wiz", "Michael", "syrk"])
    assert "USERHOST syrk" == pack_command(
        "USERHOST", nick="syrk")


def test_ison():
    ''' ISON command '''
    assert "ISON Wiz Michael syrk" == pack_command(
        "ISON", nick=["Wiz", "Michael", "syrk"])
    assert "ISON syrk" == pack_command(
        "ISON", nick="syrk")
