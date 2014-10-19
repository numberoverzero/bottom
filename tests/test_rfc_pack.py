from bottom.rfc_pack import pack_command
import pytest


def test_no_command():

    ''' raise when command is None or empty '''

    with pytest.raises(ValueError):
        pack_command(None)

    with pytest.raises(ValueError):
        pack_command("")


def test_bad_command():

    ''' raise when commad doesn't have upper '''

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
    pass


def test_notice():
    ''' NOTICE command '''
    pass


def test_motd():
    ''' MOTD command '''
    pass


def test_lusers():
    ''' LUSERS command '''
    pass


def test_version():
    ''' VERSION command '''
    pass


def test_stats():
    ''' STATS command '''
    pass


def test_links():
    ''' LINKS command '''
    pass


def test_time():
    ''' TIME command '''
    pass


def test_connect():
    ''' CONNECT command '''
    pass


def test_trace():
    ''' TRACE command '''
    pass


def test_admin():
    ''' ADMIN command '''
    pass


def test_info():
    ''' INFO command '''
    pass


def test_servlist():
    ''' SERVLIST command '''
    pass


def test_squery():
    ''' SQUERY command '''
    pass


def test_who():
    ''' WHO command '''
    pass


def test_whois():
    ''' WHOIS command '''
    pass


def test_whowas():
    ''' WHOWAS command '''
    pass


def test_kill():
    ''' KILL command '''
    pass


def test_pong():
    ''' PONG command '''
    pass


def test_away():
    ''' AWAY command '''
    pass


def test_rehash():
    ''' REHASH command '''
    pass


def test_die():
    ''' DIE command '''
    pass


def test_restart():
    ''' RESTART command '''
    pass


def test_summon():
    ''' SUMMON command '''
    pass


def test_users():
    ''' USERS command '''
    pass


def test_wallops():
    ''' WALLOPS command '''
    pass


def test_userhost():
    ''' USERHOST command '''
    pass


def test_ison():
    ''' ISON command '''
    pass
