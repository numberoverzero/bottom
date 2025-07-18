# ============================================================================
# tests for specific commands
# serialization primitives tests live in test_serialize.py
#
# note: you can generate a new test template with bin/generate-tests.py
#   copy the generated test (not the whole file) for your new command into this file
#   then fill out the argument map and add any permutations.
# ============================================================================
from tests.helpers.base_classes import BaseSerializeTest
from tests.helpers.fns import base_permutations


class Test_PASS(BaseSerializeTest):
    # PASS <password>
    # patterns:
    #   PASS {password}
    # examples:
    #   PASS hunter2
    command = "PASS"
    argument_map = [
        ("password", "hunter2"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (0,): "PASS hunter2",
        }
    )


class Test_NICK(BaseSerializeTest):
    # NICK <nick>
    # patterns:
    #   NICK {nick}
    # examples:
    #   NICK WiZ
    command = "NICK"
    argument_map = [
        ("nick", "n0"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (0,): "NICK n0",
        }
    )


class Test_USER(BaseSerializeTest):
    # USER <nick> [<mode>] :<realname>
    # patterns:
    #   USER {nick} {mode} * :{realname}
    #   USER {nick} 0 * :{realname}
    # examples:
    #   USER guest 8 :Ronnie Reagan
    #   USER guest :Ronnie Reagan
    command = "USER"
    argument_map = [
        ("nick", "n0"),
        ("mode", "+i"),
        ("realname", "my.realname"),
        ("realname", ""),
    ]
    permutations = base_permutations([0, 1, 2], ValueError)
    permutations.update(
        {
            (0, 2): "USER n0 0 * :my.realname",
            (0, 1, 2): "USER n0 +i * :my.realname",
            (0, 1, 3): "USER n0 +i * :",
        }
    )


class Test_OPER(BaseSerializeTest):
    # OPER <nick> <password>
    # patterns:
    #   OPER {nick} {password}
    # examples:
    #   OPER AzureDiamond hunter2
    command = "OPER"
    argument_map = [
        ("nick", "n0"),
        ("password", "hunter2"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "OPER n0 hunter2",
        }
    )


class Test_USERMODE(BaseSerializeTest):
    # MODE <nick> [<modes>]
    # patterns:
    #   MODE {nick} {modes}
    #   MODE {nick}
    # examples:
    #   MODE WiZ -w
    #   MODE Angel
    command = "USERMODE"
    argument_map = [
        ("nick", "n0"),
        ("modes", "-io"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0,): "MODE n0",
            (0, 1): "MODE n0 -io",
        }
    )


class Test_SERVICE(BaseSerializeTest):
    # SERVICE <nick> <distribution> <type> :<info>
    # patterns:
    #   SERVICE {nick} * {distribution} {type} 0 :{info}
    # examples:
    #   SERVICE dict *.fr 0 :French
    command = "SERVICE"
    argument_map = [
        ("nick", "dict"),
        ("distribution", "*.fr"),
        ("type", 3),
        ("info", "French"),
    ]
    permutations = base_permutations([0, 1, 2, 3], ValueError)
    permutations.update(
        {
            (0, 1, 2, 3): "SERVICE dict * *.fr 3 0 :French",
        }
    )


class Test_QUIT(BaseSerializeTest):
    # QUIT [:[<message>]]
    # patterns:
    #   QUIT :{message}
    #   QUIT
    # examples:
    #   QUIT :Gone to lunch
    #   QUIT
    command = "QUIT"
    argument_map = [
        ("message", "msg msg"),
        ("message", ""),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "QUIT",
            (0,): "QUIT :msg msg",
            (1,): "QUIT :",
        }
    )


class Test_SQUIT(BaseSerializeTest):
    # SQUIT <server> [:[<message>]]
    # patterns:
    #   SQUIT {server} :{message}
    #   SQUIT {server}
    # examples:
    #   SQUIT tolsun.oulu.fi :Bad Link
    #   SQUIT tolsun.oulu.fi
    command = "SQUIT"
    argument_map = [
        ("server", "tolsun.oulu.fi"),
        ("message", "msg msg"),
        ("message", ""),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0,): "SQUIT tolsun.oulu.fi",
            (0, 1): "SQUIT tolsun.oulu.fi :msg msg",
            (0, 2): "SQUIT tolsun.oulu.fi :",
        }
    )


class Test_JOIN(BaseSerializeTest):
    # JOIN <channel> [<key>]
    # patterns:
    #   JOIN {channel:comma} {key:comma}
    #   JOIN {channel:comma}
    # examples:
    #   JOIN #foo fookey
    #   JOIN #foo
    #   JOIN 0
    command = "JOIN"
    argument_map = [
        ("channel", ["#one", "#two"]),
        ("key", ["key1", "key2"]),
        ("channel", "#chan"),
        ("key", "key"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0,): "JOIN #one,#two",
            (0, 1): "JOIN #one,#two key1,key2",
            (2,): "JOIN #chan",
            (2, 3): "JOIN #chan key",
        }
    )


class Test_PART(BaseSerializeTest):
    # PART <channel> [:[<message>]]
    # patterns:
    #   PART {channel:comma} :{message}
    #   PART {channel:comma}
    # examples:
    #   PART #foo :I lost
    #   PART #foo
    command = "PART"
    argument_map = [
        ("channel", ["#one", "#two"]),
        ("message", "msg msg"),
        ("channel", "#chan"),
        ("message", ""),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0,): "PART #one,#two",
            (0, 1): "PART #one,#two :msg msg",
            (2,): "PART #chan",
            (2, 1): "PART #chan :msg msg",
            (2, 3): "PART #chan :",
        }
    )


class Test_CHANNELMODE(BaseSerializeTest):
    # MODE <channel> <modes-and-params>
    # patterns:
    #   MODE {channel} {params:space}
    # examples:
    #   MODE #Finnish +imI *!*@*.fi
    #   MODE #en-ops +v WiZ
    #   MODE #Fins -s
    command = "CHANNELMODE"
    argument_map = [
        ("channel", "#chan"),
        ("params", ["+imI", "*!*@*.fi"]),
        ("params", "+imI *!*@*.fi"),
    ]

    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "MODE #chan +imI *!*@*.fi",
            (0, 2): "MODE #chan +imI *!*@*.fi",
        }
    )


class Test_TOPIC(BaseSerializeTest):
    # TOPIC <channel> [:[<message>]]
    # patterns:
    #   TOPIC {channel} :{message}
    #   TOPIC {channel}
    # examples:
    #   TOPIC #test :New topic
    #   TOPIC #test :
    #   TOPIC #test
    command = "TOPIC"
    argument_map = [
        ("channel", "#chan"),
        ("message", "msg msg"),
        ("message", ""),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0,): "TOPIC #chan",
            (0, 1): "TOPIC #chan :msg msg",
            (0, 2): "TOPIC #chan :",
        }
    )


class Test_NAMES(BaseSerializeTest):
    # NAMES [<channel> [<target>]]
    # patterns:
    #   NAMES {channel:comma} {target}
    #   NAMES {channel:comma}
    #   NAMES
    # examples:
    #   NAMES #twilight_zone remote.*.edu
    #   NAMES #twilight_zone
    #   NAMES
    command = "NAMES"
    argument_map = [
        ("channel", ["#one", "#two"]),
        ("target", "remote.*.edu"),
        ("channel", "#chan"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "NAMES",
            (0,): "NAMES #one,#two",
            (1,): "NAMES",  # note: target is ignored
            (0, 1): "NAMES #one,#two remote.*.edu",
            (2,): "NAMES #chan",
        }
    )


class Test_LIST(BaseSerializeTest):
    # LIST [<channel> [<target>]]
    # patterns:
    #   LIST {channel:comma} {target}
    #   LIST {channel:comma}
    #   LIST
    # examples:
    #   LIST #twilight_zone remote.*.edu
    #   LIST #twilight_zone
    #   LIST
    command = "LIST"
    argument_map = [
        ("channel", ["#one", "#two"]),
        ("target", "remote.*.edu"),
        ("channel", "#chan"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "LIST",
            (0,): "LIST #one,#two",
            (1,): "LIST",  # note: target is ignored
            (0, 1): "LIST #one,#two remote.*.edu",
            (2,): "LIST #chan",
        }
    )


class Test_INVITE(BaseSerializeTest):
    # INVITE <nick> <channel>
    # patterns:
    #   INVITE {nick} {channel}
    # examples:
    #   INVITE Wiz #Twilight_Zone
    command = "INVITE"
    argument_map = [
        ("nick", "n0"),
        ("channel", "#chan"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "INVITE n0 #chan",
        }
    )


class Test_KICK(BaseSerializeTest):
    # KICK <channel> <nick> [:[<message>]]
    # patterns:
    #   KICK {channel:comma} {nick:comma} :{message}
    #   KICK {channel:comma} {nick:comma}
    # examples:
    #   KICK #Finnish WiZ :Speaking English
    #   KICK #Finnish WiZ,Wiz-Bot :Both speaking English
    #   KICK #Finnish,#English WiZ,ZiW :Speaking wrong language
    command = "KICK"
    argument_map = [
        ("channel", ["#one", "#two"]),
        ("nick", ["n0", "n1"]),
        ("message", "msg msg"),
        ("channel", "#chan"),
        ("nick", "n0"),
        ("message", ""),
    ]
    permutations = base_permutations([0, 1, 2], ValueError)
    permutations.update(
        {
            (0, 1): "KICK #one,#two n0,n1",
            (0, 1, 2): "KICK #one,#two n0,n1 :msg msg",
            (3, 4, 5): "KICK #chan n0 :",
            (0, 4): "KICK #one,#two n0",
            (1, 3): "KICK #chan n0,n1",
        }
    )


class Test_PRIVMSG(BaseSerializeTest):
    # PRIVMSG <target> :<message>
    # patterns:
    #   PRIVMSG {target} {message}
    # examples:
    #   PRIVMSG Angel :yes I'm receiving it !
    #   PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting.
    #   PRIVMSG #Finnish :This message is in english
    command = "PRIVMSG"
    argument_map = [
        ("target", "n0"),
        ("message", "msg msg"),
        ("message", ""),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "PRIVMSG n0 :msg msg",
            (0, 2): "PRIVMSG n0 :",
        }
    )


class Test_NOTICE(BaseSerializeTest):
    # NOTICE <target> :<message>
    # patterns:
    #   NOTICE {target} {message}
    # examples:
    #   NOTICE Angel :yes I'm receiving it !
    #   NOTICE $*.fi :Server tolsun.oulu.fi rebooting.
    #   NOTICE #Finnish :This message is in english
    command = "NOTICE"
    argument_map = [
        ("target", "n0"),
        ("message", "msg msg"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "NOTICE n0 :msg msg",
        }
    )


class Test_MOTD(BaseSerializeTest):
    # MOTD [<target>]
    # patterns:
    #   MOTD {target}
    #   MOTD
    # examples:
    #   MOTD remote.*.edu
    #   MOTD
    command = "MOTD"
    argument_map = [
        ("target", "remote.*.edu"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "MOTD",
            (0,): "MOTD remote.*.edu",
        }
    )


class Test_LUSERS(BaseSerializeTest):
    # LUSERS [<mask> [<target>]]
    # patterns:
    #   LUSERS {mask} {target}
    #   LUSERS {mask}
    #   LUSERS
    # examples:
    #   LUSERS *.edu remote.*.edu
    #   LUSERS *.edu
    #   LUSERS
    command = "LUSERS"
    argument_map = [
        ("mask", "*.edu"),
        ("target", "remote.*.edu"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "LUSERS",
            (0,): "LUSERS *.edu",
            (1,): "LUSERS",  # note: target is ignored
            (0, 1): "LUSERS *.edu remote.*.edu",
        }
    )


class Test_VERSION(BaseSerializeTest):
    # VERSION [<target>]
    # patterns:
    #   VERSION {target}
    #   VERSION
    # examples:
    #   VERSION remote.*.edu
    #   VERSION
    command = "VERSION"
    argument_map = [
        ("target", "remote.*.edu"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "VERSION",
            (0,): "VERSION remote.*.edu",
        }
    )


class Test_STATS(BaseSerializeTest):
    # STATS [<query> [<target>]]
    # patterns:
    #   STATS {query} {target}
    #   STATS {query}
    #   STATS
    # examples:
    #   STATS m remote.*.edu
    #   STATS m
    #   STATS
    command = "STATS"
    argument_map = [
        ("query", "m"),
        ("target", "remote.*.edu"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "STATS",
            (0,): "STATS m",
            (1,): "STATS",  # note: target is ignored
            (0, 1): "STATS m remote.*.edu",
        }
    )


class Test_LINKS(BaseSerializeTest):
    # LINKS [[<remote>] <mask>]
    # patterns:
    #   LINKS {remote} {mask}
    #   LINKS {mask}
    #   LINKS
    # examples:
    #   LINKS *.edu *.bu.edu
    #   LINKS *.au
    #   LINKS
    command = "LINKS"
    argument_map = [
        ("remote", "*.edu"),
        ("mask", "*.au"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "LINKS",
            (0,): "LINKS",  # note: remote is ignored
            (1,): "LINKS *.au",
            (0, 1): "LINKS *.edu *.au",
        }
    )


class Test_TIME(BaseSerializeTest):
    # TIME [<target>]
    # patterns:
    #   TIME {target}
    #   TIME
    # examples:
    #   TIME remote.*.edu
    #   TIME
    command = "TIME"
    argument_map = [
        ("target", "remote.*.edu"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "TIME",
            (0,): "TIME remote.*.edu",
        }
    )


class Test_CONNECT(BaseSerializeTest):
    # CONNECT <target> <port> [<remote>]
    # patterns:
    #   CONNECT {target} {port} {remote}
    #   CONNECT {target} {port}
    # examples:
    #   CONNECT tolsun.oulu.fi 6667 *.edu
    #   CONNECT tolsun.oulu.fi 6667
    command = "CONNECT"
    argument_map = [
        ("target", "tolsun.oulu.fi"),
        ("port", 6667),
        ("remote", "*.edu"),
    ]
    permutations = base_permutations([0, 1, 2], ValueError)
    permutations.update(
        {
            (0, 1): "CONNECT tolsun.oulu.fi 6667",
            (0, 1, 2): "CONNECT tolsun.oulu.fi 6667 *.edu",
        }
    )


class Test_TRACE(BaseSerializeTest):
    # TRACE [<target>]
    # patterns:
    #   TRACE {target}
    #   TRACE
    # examples:
    #   TRACE
    command = "TRACE"
    argument_map = [
        ("target", "*.oulu.fi"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "TRACE",
            (0,): "TRACE *.oulu.fi",
        }
    )


class Test_ADMIN(BaseSerializeTest):
    # ADMIN [<target>]
    # patterns:
    #   ADMIN {target}
    #   ADMIN
    # examples:
    #   ADMIN eff.org
    #   ADMIN WiZ
    #   ADMIN
    command = "ADMIN"
    argument_map = [
        ("target", "eff.org"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "ADMIN",
            (0,): "ADMIN eff.org",
        }
    )


class Test_INFO(BaseSerializeTest):
    # INFO [<target>]
    # patterns:
    #   INFO {target}
    #   INFO
    # examples:
    #   INFO eff.org
    #   INFO WiZ
    #   INFO
    command = "INFO"
    argument_map = [
        ("target", "eff.org"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "INFO",
            (0,): "INFO eff.org",
        }
    )


class Test_SERVLIST(BaseSerializeTest):
    # SERVLIST [<mask> [<type>]]
    # patterns:
    #   SERVLIST {mask} {type}
    #   SERVLIST {mask}
    #   SERVLIST
    # examples:
    #   SERVLIST *SERV 3
    #   SERVLIST *SERV
    #   SERVLIST
    command = "SERVLIST"
    argument_map = [
        ("mask", "*SERV"),
        ("type", 3),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "SERVLIST",
            (0,): "SERVLIST *SERV",
            (1,): "SERVLIST",  # note: type is ignored
            (0, 1): "SERVLIST *SERV 3",
        }
    )


class Test_SQUERY(BaseSerializeTest):
    # SQUERY <target> :<message>
    # patterns:
    #   SQUERY {target} :{message}
    # examples:
    #   SQUERY irchelp :HELP privmsg
    command = "SQUERY"
    argument_map = [
        ("target", "irchelp"),
        ("message", "msg msg"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "SQUERY irchelp :msg msg",
        }
    )


class Test_WHO(BaseSerializeTest):
    # WHO [<mask> ["o"]]
    # patterns:
    #   WHO {mask} {o:bool}
    #   WHO {mask}
    #   WHO
    # examples:
    #   WHO jto* o
    #   WHO *.fi
    #   WHO
    command = "WHO"
    argument_map = [
        ("mask", "*.fi"),
        ("o", True),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (): "WHO",
            (0,): "WHO *.fi",
            (1,): "WHO",  # note: o is ignored
            (0, 1): "WHO *.fi o",
        }
    )


class Test_WHOIS(BaseSerializeTest):
    # WHOIS [<target>] <mask>
    # patterns:
    #   WHOIS {target} {mask:comma}
    #   WHOIS {mask:comma}
    # examples:
    #   WHOIS WiZ
    #   WHOIS eff.org trillian
    command = "WHOIS"
    argument_map = [
        ("target", "eff.org"),
        ("mask", "n0"),
        ("mask", ["n0", "n1"]),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (1,): "WHOIS n0",
            (2,): "WHOIS n0,n1",
            (0, 1): "WHOIS eff.org n0",
            (0, 2): "WHOIS eff.org n0,n1",
        }
    )


class Test_WHOWAS(BaseSerializeTest):
    # WHOWAS <nick> [<count> [<target>]]
    # patterns:
    #   WHOWAS {nick:comma} {count} {target}
    #   WHOWAS {nick:comma} {count}
    #   WHOWAS {nick:comma}
    # examples:
    #   WHOWAS Wiz 9 remote.*.edu
    #   WHOWAS Wiz 9
    #   WHOWAS Mermaid
    command = "WHOWAS"
    argument_map = [
        ("nick", ["n0", "n1"]),
        ("count", 3),
        ("target", "remote.*.edu"),
        ("nick", "n0"),
    ]
    permutations = base_permutations([0, 1, 2], ValueError)
    permutations.update(
        {
            (0,): "WHOWAS n0,n1",
            (0, 1): "WHOWAS n0,n1 3",
            (0, 2): "WHOWAS n0,n1",  # note: target is ignored
            (0, 1, 2): "WHOWAS n0,n1 3 remote.*.edu",
            (3,): "WHOWAS n0",
            (3, 1): "WHOWAS n0 3",
        }
    )


class Test_KILL(BaseSerializeTest):
    # KILL <nick> :<message>
    # patterns:
    #   KILL {nick} :{message}
    # examples:
    #   KILL WiZ :Spamming joins
    command = "KILL"
    argument_map = [
        ("nick", "n0"),
        ("message", "msg msg"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0, 1): "KILL n0 :msg msg",
        }
    )


class Test_PING(BaseSerializeTest):
    # PING <message> [<target>]
    # patterns:
    #   PING {message:nospace} {target}
    #   PING {message:nospace}
    # examples:
    #   PING my-ping-token
    #   PING my-ping-token eff.org
    command = "PING"
    argument_map = [
        ("message", "msg.msg"),
        ("target", "eff.org"),
        ("message", "has a space"),
    ]
    permutations = base_permutations([0, 1], ValueError)
    permutations.update(
        {
            (0,): "PING msg.msg",
            (0, 1): "PING msg.msg eff.org",
            (2, 1): ValueError,
        }
    )


class Test_PONG(BaseSerializeTest):
    # PONG [:[<message>]]
    # patterns:
    #   PONG :{message}
    #   PONG
    # examples:
    #   PONG :I'm still here
    #   PONG
    command = "PONG"
    argument_map = [
        ("message", "msg msg"),
        ("message", ""),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "PONG",
            (0,): "PONG :msg msg",
            (1,): "PONG :",
        }
    )


class Test_AWAY(BaseSerializeTest):
    # AWAY [:[<message>]]
    # patterns:
    #   AWAY :{message}
    #   AWAY
    # examples:
    #   AWAY :Gone to lunch.
    #   AWAY
    command = "AWAY"
    argument_map = [
        ("message", "msg msg"),
        ("message", ""),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "AWAY",
            (0,): "AWAY :msg msg",
            (1,): "AWAY :",
        }
    )


class Test_REHASH(BaseSerializeTest):
    # REHASH
    # patterns:
    #   REHASH
    # examples:
    #   REHASH
    command = "REHASH"
    argument_map = []
    permutations = base_permutations([], ValueError)
    permutations.update(
        {
            (): "REHASH",
        }
    )


class Test_DIE(BaseSerializeTest):
    # DIE
    # patterns:
    #   DIE
    # examples:
    #   DIE
    command = "DIE"
    argument_map = []
    permutations = base_permutations([], ValueError)
    permutations.update(
        {
            (): "DIE",
        }
    )


class Test_RESTART(BaseSerializeTest):
    # RESTART
    # patterns:
    #   RESTART
    # examples:
    #   RESTART
    command = "RESTART"
    argument_map = []
    permutations = base_permutations([], ValueError)
    permutations.update(
        {
            (): "RESTART",
        }
    )


class Test_SUMMON(BaseSerializeTest):
    # SUMMON <nick> [<target> [<channel>]]
    # patterns:
    #   SUMMON {nick} {target} {channel}
    #   SUMMON {nick} {target}
    #   SUMMON {nick}
    # examples:
    #   SUMMON Wiz remote.*.edu #Finnish
    #   SUMMON Wiz remote.*.edu
    #   SUMMON Wiz
    command = "SUMMON"
    argument_map = [
        ("nick", "n0"),
        ("target", "remote.*.edu"),
        ("channel", "#chan"),
    ]
    permutations = base_permutations([0, 1, 2], ValueError)
    permutations.update(
        {
            (0,): "SUMMON n0",
            (0, 1): "SUMMON n0 remote.*.edu",
            (0, 2): "SUMMON n0",  # note: channel is ignored
            (0, 1, 2): "SUMMON n0 remote.*.edu #chan",
        }
    )


class Test_USERS(BaseSerializeTest):
    # USERS [<target>]
    # patterns:
    #   USERS {target}
    #   USERS
    # examples:
    #   USERS remote.*.edu
    #   USERS
    command = "USERS"
    argument_map = [
        ("target", "remote.*.edu"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (): "USERS",
            (0,): "USERS remote.*.edu",
        }
    )


class Test_WALLOPS(BaseSerializeTest):
    # WALLOPS :<message>
    # patterns:
    #   WALLOPS :{message}
    # examples:
    #   WALLOPS :Maintenance in 5 minutes
    command = "WALLOPS"
    argument_map = [
        ("message", "msg msg"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (0,): "WALLOPS :msg msg",
        }
    )


class Test_USERHOST(BaseSerializeTest):
    # USERHOST <nick>
    # patterns:
    #   USERHOST {nick:space}
    # examples:
    #   USERHOST Wiz Michael syrk
    #   USERHOST syrk
    command = "USERHOST"
    argument_map = [
        ("nick", ["n0", "n1"]),
        ("nick", "n0"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (0,): "USERHOST n0 n1",
            (1,): "USERHOST n0",
        }
    )


class Test_ISON(BaseSerializeTest):
    # ISON <nick>
    # patterns:
    #   ISON {nick:space}
    # examples:
    #   ISON Wiz Michael syrk
    #   ISON syrk
    command = "ISON"
    argument_map = [
        ("nick", ["n0", "n1"]),
        ("nick", "n0"),
    ]
    permutations = base_permutations([0], ValueError)
    permutations.update(
        {
            (0,): "ISON n0 n1",
            (1,): "ISON n0",
        }
    )
