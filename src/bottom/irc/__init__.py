import logging
from dataclasses import dataclass, field

from bottom.core import BaseClient, NextMessageHandler
from bottom.irc.serialize import register_pattern, serialize
from bottom.unpack import unpack_command

__all__ = ["disable_first_run_message", "register_pattern", "rfc2812_handler", "serialize"]


rfc2812_log = logging.getLogger("bottom.rfc2812_handler")
_suggest_issue = {
    "is_first_run": True,
    "extra_lines": [
        "Please consider filing an issue for the missing command:",
        "  https://github.com/numberoverzero/bottom/issues/new",
        "To prevent this message in the future:",
        "  from bottom.irc import disable_first_run_msg",
        "  disable_first_run_msg()",
        "To disable the logger entirely:",
        "  from bottom.irc import rfc2812_log",
        "  rfc2812_log.disabled = True",
    ],
}


def disable_first_run_message() -> None:
    _suggest_issue["is_first_run"] = False


async def rfc2812_handler(next_handler: NextMessageHandler[BaseClient], client: BaseClient, message: bytes) -> None:
    try:
        event, kwargs = unpack_command(message.decode(client._encoding))
        client.trigger(event, **kwargs)
    except ValueError:
        msg = f"Failed to parse: {message.decode(client._encoding)}"
        if _suggest_issue["is_first_run"]:
            disable_first_run_message()
            lines = [msg] + _suggest_issue["extra_lines"]
            rfc2812_log.info("\n".join(lines))
        else:
            rfc2812_log.info(msg)

    await next_handler(client, message)


# =============================================================================
# KNOWN COMMANDS
# =============================================================================


@dataclass(frozen=True, kw_only=True)
class Command:
    bottom: str
    irc: str
    refs: list[str]
    syntax: str
    examples: list[str]
    patterns: list[str]
    notes: list[str] = field(default_factory=list)


KNOWN_COMMANDS = [
    Command(
        bottom="PASS",
        irc="PASS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.1",
        ],
        syntax="PASS <password>",
        examples=[
            "PASS hunter2",
        ],
        patterns=[
            "PASS {password}",
        ],
    ),
    Command(
        bottom="NICK",
        irc="NICK",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.2",
        ],
        syntax="NICK <nick>",
        examples=[
            "NICK WiZ",
        ],
        patterns=[
            "NICK {nick}",
        ],
    ),
    Command(
        bottom="USER",
        irc="USER",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.3",
        ],
        syntax="USER <nick> [<mode>] :<realname>",
        examples=[
            "USER guest 8 :Ronnie Reagan",
            "USER guest :Ronnie Reagan",
        ],
        patterns=["USER {nick} {mode} * :{realname}", "USER {nick} 0 * :{realname}"],
    ),
    Command(
        bottom="OPER",
        irc="OPER",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.4",
        ],
        syntax="OPER <nick> <password>",
        examples=[
            "OPER AzureDiamond hunter2",
        ],
        patterns=[
            "OPER {nick} {password}",
        ],
    ),
    Command(
        bottom="USERMODE",
        irc="MODE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.5",
        ],
        syntax="MODE <nick> [<modes>]",
        examples=[
            "MODE WiZ -w",
            "MODE Angel",
        ],
        patterns=[
            "MODE {nick} {modes}",
            "MODE {nick}",
        ],
    ),
    Command(
        bottom="SERVICE",
        irc="SERVICE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.6",
        ],
        syntax="SERVICE <nick> <distribution> <type> :<info>",
        examples=[
            "SERVICE dict *.fr 0 :French",
        ],
        patterns=[
            "SERVICE {nick} * {distribution} {type} 0 :{info}",
        ],
    ),
    Command(
        bottom="QUIT",
        irc="QUIT",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.7",
        ],
        syntax="QUIT [:[<message>]]",
        examples=[
            "QUIT :Gone to lunch",
            "QUIT",
        ],
        patterns=["QUIT :{message}", "QUIT"],
    ),
    Command(
        bottom="SQUIT",
        irc="SQUIT",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.1.8",
        ],
        syntax="SQUIT <server> [:[<message>]]",
        examples=[
            "SQUIT tolsun.oulu.fi :Bad Link",
            "SQUIT tolsun.oulu.fi",
        ],
        patterns=["SQUIT {server} :{message}", "SQUIT {server}"],
    ),
    Command(
        bottom="JOIN",
        irc="JOIN",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.1",
        ],
        syntax="JOIN <channel> [<key>]",
        examples=[
            "JOIN #foo fookey",
            "JOIN #foo",
            "JOIN 0",
        ],
        patterns=["JOIN {channel:comma} {key:comma}", "JOIN {channel:comma}"],
    ),
    Command(
        bottom="PART",
        irc="PART",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.2",
        ],
        syntax="PART <channel> [:[<message>]]",
        examples=[
            "PART #foo :I lost",
            "PART #foo",
        ],
        patterns=["PART {channel:comma} :{message}", "PART {channel:comma}"],
    ),
    Command(
        bottom="CHANNELMODE",
        irc="MODE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.3",
        ],
        syntax="MODE <channel> <modes-and-params>",
        examples=[
            "MODE #Finnish +imI *!*@*.fi",
            "MODE #en-ops +v WiZ",
            "MODE #Fins -s",
        ],
        patterns=[
            "MODE {channel} {params:space}",
        ],
    ),
    Command(
        bottom="TOPIC",
        irc="TOPIC",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.4",
        ],
        syntax="TOPIC <channel> [:[<message>]]",
        examples=[
            "TOPIC #test :New topic",
            "TOPIC #test :",
            "TOPIC #test",
        ],
        patterns=[
            "TOPIC {channel} :{message}",
            "TOPIC {channel}",
        ],
    ),
    Command(
        bottom="NAMES",
        irc="NAMES",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.5",
        ],
        syntax="NAMES [<channel> [<target>]]",
        examples=[
            "NAMES #twilight_zone remote.*.edu",
            "NAMES #twilight_zone",
            "NAMES",
        ],
        patterns=[
            "NAMES {channel:comma} {target}",
            "NAMES {channel:comma}",
            "NAMES",
        ],
    ),
    Command(
        bottom="LIST",
        irc="LIST",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.6",
        ],
        syntax="LIST [<channel> [<target>]]",
        examples=[
            "LIST #twilight_zone remote.*.edu",
            "LIST #twilight_zone",
            "LIST",
        ],
        patterns=[
            "LIST {channel:comma} {target}",
            "LIST {channel:comma}",
            "LIST",
        ],
    ),
    Command(
        bottom="INVITE",
        irc="INVITE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.7",
        ],
        syntax="INVITE <nick> <channel>",
        examples=[
            "INVITE Wiz #Twilight_Zone",
        ],
        patterns=[
            "INVITE {nick} {channel}",
        ],
    ),
    Command(
        bottom="KICK",
        irc="KICK",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.2.8",
        ],
        syntax="KICK <channel> <nick> [:[<message>]]",
        examples=[
            "KICK #Finnish WiZ :Speaking English",
            "KICK #Finnish WiZ,Wiz-Bot :Both speaking English",
            "KICK #Finnish,#English WiZ,ZiW :Speaking wrong language",
        ],
        patterns=[
            "KICK {channel:comma} {nick:comma} :{message}",
            "KICK {channel:comma} {nick:comma}",
        ],
    ),
    Command(
        bottom="PRIVMSG",
        irc="PRIVMSG",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.3.1",
        ],
        syntax="PRIVMSG <target> :<message>",
        examples=[
            "PRIVMSG Angel :yes I'm receiving it !",
            "PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting.",
            "PRIVMSG #Finnish :This message is in english",
        ],
        patterns=[
            "PRIVMSG {target} :{message}",
        ],
    ),
    Command(
        bottom="NOTICE",
        irc="NOTICE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.3.2",
        ],
        syntax="NOTICE <target> :<message>",
        examples=[
            "NOTICE Angel :yes I'm receiving it !",
            "NOTICE $*.fi :Server tolsun.oulu.fi rebooting.",
            "NOTICE #Finnish :This message is in english",
        ],
        patterns=[
            "NOTICE {target} :{message}",
        ],
    ),
    Command(
        bottom="MOTD",
        irc="MOTD",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.1",
        ],
        syntax="MOTD [<target>]",
        examples=[
            "MOTD remote.*.edu",
            "MOTD",
        ],
        patterns=[
            "MOTD {target}",
            "MOTD",
        ],
    ),
    Command(
        bottom="LUSERS",
        irc="LUSERS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.2",
        ],
        syntax="LUSERS [<mask> [<target>]]",
        examples=[
            "LUSERS *.edu remote.*.edu",
            "LUSERS *.edu",
            "LUSERS",
        ],
        patterns=[
            "LUSERS {mask} {target}",
            "LUSERS {mask}",
            "LUSERS",
        ],
    ),
    Command(
        bottom="VERSION",
        irc="VERSION",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.3",
        ],
        syntax="VERSION [<target>]",
        examples=[
            "VERSION remote.*.edu",
            "VERSION",
        ],
        patterns=[
            "VERSION {target}",
            "VERSION",
        ],
    ),
    Command(
        bottom="STATS",
        irc="STATS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.4",
        ],
        syntax="STATS [<query> [<target>]]",
        examples=[
            "STATS m remote.*.edu",
            "STATS m",
            "STATS",
        ],
        patterns=[
            "STATS {query} {target}",
            "STATS {query}",
            "STATS",
        ],
    ),
    Command(
        bottom="LINKS",
        irc="LINKS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.5",
        ],
        syntax="LINKS [[<remote>] <mask>]",
        examples=[
            "LINKS *.edu *.bu.edu",
            "LINKS *.au",
            "LINKS",
        ],
        patterns=[
            "LINKS {remote} {mask}",
            "LINKS {mask}",
            "LINKS",
        ],
    ),
    Command(
        bottom="TIME",
        irc="TIME",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.6",
        ],
        syntax="TIME [<target>]",
        examples=[
            "TIME remote.*.edu",
            "TIME",
        ],
        patterns=[
            "TIME {target}",
            "TIME",
        ],
    ),
    Command(
        bottom="CONNECT",
        irc="CONNECT",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.7",
        ],
        syntax="CONNECT <target> <port> [<remote>]",
        examples=[
            "CONNECT tolsun.oulu.fi 6667 *.edu",
            "CONNECT tolsun.oulu.fi 6667",
        ],
        patterns=[
            "CONNECT {target} {port} {remote}",
            "CONNECT {target} {port}",
        ],
    ),
    Command(
        bottom="TRACE",
        irc="TRACE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.8",
        ],
        syntax="TRACE [<target>]",
        examples=[
            "TRACE",
        ],
        patterns=[
            "TRACE {target}",
            "TRACE",
        ],
    ),
    Command(
        bottom="ADMIN",
        irc="ADMIN",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.9",
        ],
        syntax="ADMIN [<target>]",
        examples=[
            "ADMIN eff.org",
            "ADMIN WiZ",
            "ADMIN",
        ],
        patterns=[
            "ADMIN {target}",
            "ADMIN",
        ],
    ),
    Command(
        bottom="INFO",
        irc="INFO",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.4.10",
        ],
        syntax="INFO [<target>]",
        examples=[
            "INFO eff.org",
            "INFO WiZ",
            "INFO",
        ],
        patterns=[
            "INFO {target}",
            "INFO",
        ],
    ),
    Command(
        bottom="SERVLIST",
        irc="SERVLIST",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.5.1",
        ],
        syntax="SERVLIST [<mask> [<type>]]",
        examples=[
            "SERVLIST *SERV 3",
            "SERVLIST *SERV",
            "SERVLIST",
        ],
        patterns=[
            "SERVLIST {mask} {type}",
            "SERVLIST {mask}",
            "SERVLIST",
        ],
    ),
    Command(
        bottom="SQUERY",
        irc="SQUERY",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.5.2",
        ],
        syntax="SQUERY <target> :<message>",
        examples=[
            "SQUERY irchelp :HELP privmsg",
        ],
        patterns=[
            "SQUERY {target} :{message}",
        ],
    ),
    Command(
        bottom="WHO",
        irc="WHO",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.6.1",
        ],
        syntax='WHO [<mask> ["o"]]',
        examples=[
            "WHO jto* o",
            "WHO *.fi",
            "WHO",
        ],
        patterns=[
            "WHO {mask} {o:bool}",
            "WHO {mask}",
            "WHO",
        ],
    ),
    Command(
        bottom="WHOIS",
        irc="WHOIS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.6.2",
        ],
        syntax="WHOIS [<target>] <mask>",
        examples=[
            "WHOIS WiZ",
            "WHOIS eff.org trillian",
        ],
        patterns=[
            "WHOIS {target} {mask:comma}",
            "WHOIS {mask:comma}",
        ],
    ),
    Command(
        bottom="WHOWAS",
        irc="WHOWAS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.6.3",
        ],
        syntax="WHOWAS <nick> [<count> [<target>]]",
        examples=[
            "WHOWAS Wiz 9 remote.*.edu",
            "WHOWAS Wiz 9",
            "WHOWAS Mermaid",
        ],
        patterns=[
            "WHOWAS {nick:comma} {count} {target}",
            "WHOWAS {nick:comma} {count}",
            "WHOWAS {nick:comma}",
        ],
    ),
    Command(
        bottom="KILL",
        irc="KILL",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.7.1",
        ],
        syntax="KILL <nick> :<message>",
        examples=[
            "KILL WiZ :Spamming joins",
        ],
        patterns=[
            "KILL {nick} :{message}",
        ],
    ),
    Command(
        bottom="PING",
        irc="PING",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.7.2",
            "https://github.com/ngircd/ngircd/blob/512af135d06e7dad93f51eae51b3979e1d4005cc/doc/Commands.txt#L146-L153",
        ],
        syntax="PING <message> [<target>]",
        examples=[
            "PING my-ping-token",
            "PING my-ping-token eff.org",
        ],
        patterns=[
            "PING {message:nospace} {target}",
            "PING {message:nospace}",
        ],
    ),
    Command(
        bottom="PONG",
        irc="PONG",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-3.7.3",
        ],
        syntax="PONG [:[<message>]]",
        examples=[
            "PONG :I'm still here",
            "PONG",
        ],
        patterns=[
            "PONG :{message}",
            "PONG",
        ],
    ),
    Command(
        bottom="AWAY",
        irc="AWAY",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.1",
        ],
        syntax="AWAY [:[<message>]]",
        examples=[
            "AWAY :Gone to lunch.",
            "AWAY",
        ],
        patterns=[
            "AWAY :{message}",
            "AWAY",
        ],
    ),
    Command(
        bottom="REHASH",
        irc="REHASH",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.2",
        ],
        syntax="REHASH",
        examples=[
            "REHASH",
        ],
        patterns=[
            "REHASH",
        ],
    ),
    Command(
        bottom="DIE",
        irc="DIE",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.3",
        ],
        syntax="DIE",
        examples=[
            "DIE",
        ],
        patterns=[
            "DIE",
        ],
    ),
    Command(
        bottom="RESTART",
        irc="RESTART",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.4",
        ],
        syntax="RESTART",
        examples=[
            "RESTART",
        ],
        patterns=[
            "RESTART",
        ],
    ),
    Command(
        bottom="SUMMON",
        irc="SUMMON",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.5",
        ],
        syntax="SUMMON <nick> [<target> [<channel>]]",
        examples=[
            "SUMMON Wiz remote.*.edu #Finnish",
            "SUMMON Wiz remote.*.edu",
            "SUMMON Wiz",
        ],
        patterns=[
            "SUMMON {nick} {target} {channel}",
            "SUMMON {nick} {target}",
            "SUMMON {nick}",
        ],
    ),
    Command(
        bottom="USERS",
        irc="USERS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.6",
        ],
        syntax="USERS [<target>]",
        examples=[
            "USERS remote.*.edu",
            "USERS",
        ],
        patterns=[
            "USERS {target}",
            "USERS",
        ],
    ),
    Command(
        bottom="WALLOPS",
        irc="WALLOPS",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.7",
        ],
        syntax="WALLOPS :<message>",
        examples=[
            "WALLOPS :Maintenance in 5 minutes",
        ],
        patterns=[
            "WALLOPS :{message}",
        ],
    ),
    Command(
        bottom="USERHOST",
        irc="USERHOST",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.8",
        ],
        syntax="USERHOST <nick>",
        examples=[
            "USERHOST Wiz Michael syrk",
            "USERHOST syrk",
        ],
        patterns=[
            "USERHOST {nick:space}",
        ],
    ),
    Command(
        bottom="ISON",
        irc="ISON",
        refs=[
            "https://tools.ietf.org/html/rfc2812#section-4.9",
        ],
        syntax="ISON <nick>",
        examples=[
            "ISON Wiz Michael syrk",
            "ISON syrk",
        ],
        patterns=[
            "ISON {nick:space}",
        ],
    ),
]


def _register_global_commands() -> None:
    for command in KNOWN_COMMANDS:
        for pattern in command.patterns:
            register_pattern(command.bottom, pattern)


_register_global_commands()
