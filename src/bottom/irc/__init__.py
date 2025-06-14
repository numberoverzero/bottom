import logging

from bottom.core import BaseClient, NextMessageHandler
from bottom.irc.serialize import register_pattern, serialize
from bottom.unpack import unpack_command

__all__ = ["register_pattern", "rfc2812_handler", "serialize"]


rfc2812_log = logging.getLogger("bottom.rfc2812_handler")


async def rfc2812_handler(next_handler: NextMessageHandler[BaseClient], client: BaseClient, message: bytes) -> None:
    try:
        event, kwargs = unpack_command(message.decode(client._encoding))
        client.trigger(event, **kwargs)
    except ValueError:
        rfc2812_log.debug("Failed to parse line >>> {}".format(message.decode(client._encoding)))
    await next_handler(client, message)


# =============================================================================
# KNOWN COMMANDS
# =============================================================================

# PASS
# https://tools.ietf.org/html/rfc2812#section-3.1.1
# PASS <password>
# ----------
# PASS secretpasswordhere
register_pattern("PASS", "PASS {password}")

# NICK
# https://tools.ietf.org/html/rfc2812#section-3.1.2
# NICK <nick>
# ----------
# NICK Wiz
register_pattern("NICK", "NICK {nick}")

# USER
# https://tools.ietf.org/html/rfc2812#section-3.1.3
# USER <user> [<mode>] :<realname>
# ----------
# USER guest 8 :Ronnie Reagan
# USER guest :Ronnie Reagan
register_pattern("USER", "USER {user} {mode} * :{realname}", defaults={"mode": 0})

# OPER
# https://tools.ietf.org/html/rfc2812#section-3.1.4
# OPER <user> <password>
# ----------
# OPER AzureDiamond hunter2
register_pattern("OPER", "OPER {user} {password}")

# USERMODE (renamed from MODE)
# https://tools.ietf.org/html/rfc2812#section-3.1.5
# MODE <nick> [<modes>]
# ----------
# MODE WiZ -w
# MODE Angel +i
# MODE
register_pattern("USERMODE", "MODE {nick:opt} {modes:opt}", deps={"modes": "nick"})

# SERVICE
# https://tools.ietf.org/html/rfc2812#section-3.1.6
# SERVICE <nick> <distribution> <type> :<info>
# ----------
# SERVICE dict *.fr 0 :French
register_pattern("SERVICE", "SERVICE {nick} * {distribution} {type} 0 :{info}")

# QUIT
# https://tools.ietf.org/html/rfc2812#section-3.1.7
# QUIT :[<message>]
# ----------
# QUIT :Gone to lunch
# QUIT
register_pattern("QUIT", "QUIT :{message:opt}")
register_pattern("QUIT", "QUIT")

# SQUIT
# https://tools.ietf.org/html/rfc2812#section-3.1.8
# SQUIT <server> [<message>]
# ----------
# SQUIT tolsun.oulu.fi :Bad Link
# SQUIT tolsun.oulu.fi
register_pattern("SQUIT", "SQUIT {server} :{message:opt}")
register_pattern("SQUIT", "SQUIT {server}")

# JOIN
# https://tools.ietf.org/html/rfc2812#section-3.2.1
# JOIN <channel> [<key>]
# ----------
# JOIN #foo fookey
# JOIN #foo
# JOIN 0
register_pattern("JOIN", "JOIN {channel:comma} {key:opt|comma}")

# PART
# https://tools.ietf.org/html/rfc2812#section-3.2.2
# PART <channel> :[<message>]
# ----------
# PART #foo :I lost
# PART #foo
register_pattern("PART", "PART {channel:comma} :{message:opt}")

# CHANNELMODE (renamed from MODE)
# https://tools.ietf.org/html/rfc2812#section-3.2.3
# MODE <channel> <modes> [<params>]
# ----------
# MODE #Finnish +imI *!*@*.fi
# MODE #en-ops +v WiZ
# MODE #Fins -s
register_pattern("CHANNELMODE", "MODE {channel} {params:space}")

# TOPIC
# https://tools.ietf.org/html/rfc2812#section-3.2.4
# TOPIC <channel> :[<message>]
# ----------
# TOPIC #test :New topic
# TOPIC #test :
# TOPIC #test

register_pattern("TOPIC", "TOPIC {channel} :{message}")
register_pattern("TOPIC", "TOPIC {channel}")

# NAMES
# https://tools.ietf.org/html/rfc2812#section-3.2.5
# NAMES [<channel>] [<target>]
# ----------
# NAMES #twilight_zone remote.*.edu
# NAMES #twilight_zone
# NAMES
register_pattern("NAMES", "NAMES {channel:opt|comma} {target:opt}", deps={"target": "channel"})

# LIST
# https://tools.ietf.org/html/rfc2812#section-3.2.6
# LIST [<channel>] [<target>]
# ----------
# LIST #twilight_zone remote.*.edu
# LIST #twilight_zone
# LIST
register_pattern("LIST", "LIST {channel:opt|comma} {target:opt}", deps={"target": "channel"})

# INVITE
# https://tools.ietf.org/html/rfc2812#section-3.2.7
# INVITE <nick> <channel>
# ----------
# INVITE Wiz #Twilight_Zone
register_pattern("INVITE", "INVITE {nick} {channel}")

# KICK
# https://tools.ietf.org/html/rfc2812#section-3.2.8
# KICK <channel> <nick> :[<message>]
# ----------
# KICK #Finnish WiZ :Speaking English
# KICK #Finnish WiZ,Wiz-Bot :Both speaking English
# KICK #Finnish,#English WiZ,ZiW :Speaking wrong language
register_pattern("KICK", "KICK {channel:comma} {nick:comma} :{message}")
register_pattern("KICK", "KICK {channel:comma} {nick:comma}")

# PRIVMSG
# https://tools.ietf.org/html/rfc2812#section-3.3.1
# PRIVMSG <target> :<message>
# ----------
# PRIVMSG Angel :yes I'm receiving it !
# PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting.
# PRIVMSG #Finnish :This message is in english
register_pattern("PRIVMSG", "PRIVMSG {target} {message}")

# NOTICE
# https://tools.ietf.org/html/rfc2812#section-3.3.2
# NOTICE <target> :<message>
# ----------
# NOTICE Angel :yes I'm receiving it !
# NOTICE $*.fi :Server tolsun.oulu.fi rebooting.
# NOTICE #Finnish :This message is in english
register_pattern("NOTICE", "NOTICE {target} {message}")

# MOTD
# https://tools.ietf.org/html/rfc2812#section-3.4.1
# MOTD [<target>]
# ----------
# MOTD remote.*.edu
# MOTD
register_pattern("MOTD", "MOTD {target:opt}")

# LUSERS
# https://tools.ietf.org/html/rfc2812#section-3.4.2
# LUSERS [<mask>] [<target>]
# ----------
# LUSERS *.edu remote.*.edu
# LUSERS *.edu
# LUSERS
register_pattern("LUSERS", "LUSERS {mask:opt} {target:opt}", deps={"target": "mask"})

# VERSION
# https://tools.ietf.org/html/rfc2812#section-3.4.3
# VERSION [<target>]
# ----------
# VERSION remote.*.edu
# VERSION
register_pattern("VERSION", "VERSION {target:opt}")

# STATS
# https://tools.ietf.org/html/rfc2812#section-3.4.4
# STATS [<query>] [<target>]
# ----------
# STATS m remote.*.edu
# STATS m
# STATS
register_pattern("STATS", "STATS {query:opt} {target:opt}", deps={"target": "query"})

# LINKS
# https://tools.ietf.org/html/rfc2812#section-3.4.5
# LINKS [<remote>] [<mask>]
# ----------
# LINKS *.edu *.bu.edu
# LINKS *.au
# LINKS
register_pattern("LINKS", "LINKS {remote} {mask}")
register_pattern("LINKS", "LINKS {mask:opt}")

# TIME
# https://tools.ietf.org/html/rfc2812#section-3.4.6
# TIME [<target>]
# ----------
# TIME remote.*.edu
# TIME
register_pattern("TIME", "TIME {target:opt}")

# CONNECT
# https://tools.ietf.org/html/rfc2812#section-3.4.7
# CONNECT <target> <port> [<remote>]
# ----------
# CONNECT tolsun.oulu.fi 6667 *.edu
# CONNECT tolsun.oulu.fi 6667
register_pattern("CONNECT", "CONNECT {target} {port} {remote:opt}")

# TRACE
# https://tools.ietf.org/html/rfc2812#section-3.4.8
# TRACE [<target>]
# ----------
# TRACE
register_pattern("TRACE", "TRACE {target:opt}")

# ADMIN
# https://tools.ietf.org/html/rfc2812#section-3.4.9
# ADMIN [<target>]
# ----------
# ADMIN
register_pattern("ADMIN", "ADMIN {target:opt}")

# INFO
# https://tools.ietf.org/html/rfc2812#section-3.4.10
# INFO [<target>]
# ----------
# INFO
register_pattern("INFO", "INFO {target:opt}")

# SERVLIST
# https://tools.ietf.org/html/rfc2812#section-3.5.1
# SERVLIST [<mask>] [<type>]
# ----------
# SERVLIST *SERV 3
# SERVLIST *SERV
# SERVLIST
register_pattern("SERVLIST", "SERVLIST {mask:opt} {type:opt}", deps={"type": "mask"})

# SQUERY
# https://tools.ietf.org/html/rfc2812#section-3.5.2
# SQUERY <target> :<message>
# ----------
# SQUERY irchelp :HELP privmsg
register_pattern("SQUERY", "SQUERY {target} :{message}")

# WHO
# https://tools.ietf.org/html/rfc2812#section-3.6.1
# WHO [<mask>] ["o"]
# ----------
# WHO jto* o
# WHO *.fi
# WHO
register_pattern("WHO", "WHO {mask:opt} {o:opt|bool}", deps={"o": "mask"})

# WHOIS
# https://tools.ietf.org/html/rfc2812#section-3.6.2
# WHOIS [<target>] <mask>
# ----------
# WHOIS WiZ
# WHOIS eff.org trillian
register_pattern("WHOIS", "WHOIS {target} {mask:comma}")
register_pattern("WHOIS", "WHOIS {mask:comma}")

# WHOWAS
# https://tools.ietf.org/html/rfc2812#section-3.6.3
# WHOWAS <nick> [<count> [<target>]]
# ----------
# WHOWAS Wiz 9 remote.*.edu
# WHOWAS Wiz 9
# WHOWAS Mermaid
register_pattern("WHOWAS", "WHOWAS {nick:comma} {count} {target}")
register_pattern("WHOWAS", "WHOWAS {nick:comma} {count}")
register_pattern("WHOWAS", "WHOWAS {nick:comma}")


# KILL
# https://tools.ietf.org/html/rfc2812#section-3.7.1
# KILL <nick> :<message>
# ----------
# KILL WiZ :Spamming joins
register_pattern("KILL", "KILL {nick} :{message}")

# PING
# https://tools.ietf.org/html/rfc2812#section-3.7.2
# PING <message> [<target>]
# ----------
# PING my-ping-token
# PING my-ping-token eff.org
# note:
#   https://github.com/ngircd/ngircd/blob/512af135d06e7dad93f51eae51b3979e1d4005cc/doc/Commands.txt#L146-L153
register_pattern("PING", "PING {message:nospace} {target:opt}")

# PONG
# https://tools.ietf.org/html/rfc2812#section-3.7.3
# PONG :[<message>]
# ----------
# PONG :I'm still here
# PONG
register_pattern("PONG", "PONG :{message:opt}")

# AWAY
# https://tools.ietf.org/html/rfc2812#section-4.1
# AWAY [:<message>]
# ----------
# AWAY :Gone to lunch.
# AWAY
register_pattern("AWAY", "AWAY :{message:opt}")
register_pattern("AWAY", "AWAY")

# REHASH
# https://tools.ietf.org/html/rfc2812#section-4.2
# REHASH
# ----------
# REHASH
register_pattern("REHASH", "REHASH")

# DIE
# https://tools.ietf.org/html/rfc2812#section-4.3
# DIE
# ----------
# DIE
register_pattern("DIE", "DIE")

# RESTART
# https://tools.ietf.org/html/rfc2812#section-4.4
# RESTART
# ----------
# RESTART
register_pattern("RESTART", "RESTART")

# SUMMON
# https://tools.ietf.org/html/rfc2812#section-4.5
# SUMMON <nick> [<target>] [<channel>]
# ----------
# SUMMON Wiz remote.*.edu #Finnish
# SUMMON Wiz remote.*.edu
# SUMMON Wiz
register_pattern("SUMMON", "SUMMON {nick} {target:opt} {channel:opt}", deps={"channel": "target"})

# USERS
# https://tools.ietf.org/html/rfc2812#section-4.6
# USERS [<target>]
# ----------
# USERS remote.*.edu
# USERS
register_pattern("USERS", "USERS {target:opt}")

# WALLOPS
# https://tools.ietf.org/html/rfc2812#section-4.7
# WALLOPS [:<message>]
# ----------
# WALLOPS :Maintenance in 5 minutes
register_pattern("WALLOPS", "WALLOPS :{message:opt}")

# USERHOST
# https://tools.ietf.org/html/rfc2812#section-4.8
# USERHOST <nick>
# ----------
# USERHOST Wiz Michael syrk
# USERHOST syrk
register_pattern("USERHOST", "USERHOST {nick:space}")

# ISON
# https://tools.ietf.org/html/rfc2812#section-4.9
# ISON <nick>
# ----------
# ISON Wiz Michael syrk
# ISON syrk
register_pattern("USERHOST", "USERHOST {nick:space}")
