from __future__ import annotations

import collections
import collections.abc
import math
import string
import typing as t
from dataclasses import dataclass

__all__ = ["CommandSerializer", "register_serializer_pattern", "serialize"]

type ParamDict = dict[str, t.Any]


@dataclass(frozen=True)
class SerializingTemplate:
    type ComputedStr = t.Callable[[str, t.Any], t.Any]
    type Component = str | tuple[str, tuple[ComputedStr, ...]]

    original: str
    components: tuple[Component, ...]

    def format(self, **kwargs: t.Any) -> str:
        parts = []
        for component in self.components:
            if isinstance(component, str):
                parts.append(component)
            else:
                key, fns = component
                value = kwargs[key]
                for fn in fns:
                    value = fn(key, value)
                parts.append(value)
        return "".join(parts).strip()

    @classmethod
    def from_str(cls, template: str, fns: dict[str, ComputedStr]) -> tuple[SerializingTemplate, set[str], set[str]]:
        required = set()
        optional = set()
        components: list[SerializingTemplate.Component] = []

        fields = string.Formatter().parse(template)
        for literal_text, field_name, format_spec, conversion in fields:
            format_spec = format_spec or ""
            if "{" in format_spec:
                raise ValueError(
                    f"invalid template {template!r} -- can't use nested formatter '{field_name}:{format_spec}'"
                )
            if conversion is not None:
                raise ValueError(f"invalid template {template!r} -- cannot use conversions")
            components.append(literal_text)

            if field_name is not None:
                formatters = format_spec.split("|")
                if formatters[0] == "opt":
                    formatters.pop(0)
                    optional.add(field_name)
                else:
                    required.add(field_name)
                if unknown := [f for f in formatters if f not in fns]:
                    raise ValueError(f"invalid template {template!r} -- unknown formatters {unknown}")
                if not formatters or formatters[-1] != "":
                    formatters.append("")
                field_formatters = tuple([fns[formatter_name] for formatter_name in formatters])
                computed: SerializingTemplate.Component = (field_name, field_formatters)
                components.append(computed)

        return SerializingTemplate(original=template, components=tuple(components)), required, optional


@dataclass(frozen=True, kw_only=True)
class ParamSpec[T]:
    name: str
    default: T | None
    depends_on: tuple[ParamSpec, ...]

    def has_dependencies(self, available: dict[ParamSpec, t.Any]) -> bool:
        return all(dep in available for dep in self.depends_on)


@dataclass(frozen=True, kw_only=True)
class CommandSpec:
    command: str
    params: tuple[ParamSpec, ...]
    template: SerializingTemplate

    def score(self, kw_params: ParamDict) -> int:
        """returns -1 if kw_params are missing required or missing dependencies, otherwise sum(available params)"""
        # TODO combine with pack?
        total = 0
        available: dict[ParamSpec, t.Any] = {}
        for param in self.params:
            value = kw_params.get(param.name)
            # required param is missing
            if value is None and param.default is None:
                return -1
            elif value is not None:
                available[param] = value
            elif param.default not in (None, ""):
                available[param] = param.default
            elif param.default is None:
                raise RuntimeError("programming error, all defaults should be non-None")
        for param in self.params:
            # already filtered out missing requirements
            if param in available:
                # ok: param and deps available
                if param.has_dependencies(available):
                    total += 1
                # error: missing dependency
                else:
                    return -1
        return total

    def pack(self, kw_params: ParamDict) -> str:
        # TODO combine with score?
        filtered: ParamDict = {}
        for param in self.params:
            value = kw_params.get(param.name)
            if value is None:
                value = param.default
            if value is not None:
                filtered[param.name] = value
            else:
                print("TODO: unexpected entry into failsafe branch")
                filtered[param.name] = ""
        return self.template.format(**filtered)

    def __repr__(self) -> str:  # pragma: no cover
        required = ", ".join(param.name for param in self.params if param.default is None)
        defaults = ", ".join(param.name for param in self.params if param.default in (None, ""))
        return f"CommandSpec({self.template!r}, req=({required}), def=({defaults}))"


class CommandSerializer:
    commands: dict[str, list[CommandSpec]]

    def __init__(self, formatters: dict[str, SerializingTemplate.ComputedStr] | None = None) -> None:
        self.commands = {}
        if formatters is None:
            formatters = dict(DEFAULT_FORMATTERS)
        self.formatters = formatters

    def register(
        self,
        command: str,
        fmt: str,
        defaults: dict[str, t.Any],
        deps: dict[str, str],
    ) -> CommandSpec:
        command = command.strip().upper()
        params: dict[str, ParamSpec] = dict()
        template, req, opt = SerializingTemplate.from_str(fmt, fns=self.formatters)

        # remove defaults from req; add defaults to opt
        req.difference_update(defaults.keys())
        opt.update(defaults.keys())

        # no overlap
        assert not req.intersection(opt)
        # all deps known
        known = req.union(opt)
        dep_refs = set(deps.keys()).union(deps.values())
        def_refs = set(defaults.keys())
        assert known.issuperset(dep_refs)
        assert known.issuperset(def_refs)

        # WARN: no circular dependency detection.  don't do that.
        names = collections.deque(known)
        while names:
            name = names.popleft()
            depends_on = ()
            if dependency_name := deps.get(name):
                if dependency := params.get(dependency_name):
                    depends_on = (dependency,)
                else:
                    # missing dependency for this param
                    # don't make a new param, just go around again
                    names.append(name)
                    continue

            if name in req:
                default = None
            else:
                default = defaults.get(name, "")
                assert default is not None

            param = ParamSpec(
                name=name,
                default=default,
                depends_on=depends_on,
            )
            params[name] = param
        spec = CommandSpec(command=command, params=tuple(params.values()), template=template)
        self.commands.setdefault(command, []).append(spec)
        return spec

    def serialize(self, command: str, kw_params: ParamDict) -> str:
        command = command.strip().upper()
        if command not in self.commands:
            raise ValueError(f"Unknown command {command!r}")
        spec, highest = None, -math.inf
        for candidate in self.commands[command]:
            score = candidate.score(kw_params)
            # on tie, first registered wins
            if score > highest:
                highest = score
                spec = candidate
        assert spec is not None
        if highest < 0:
            raise ValueError(f"Missing arguments for command {command!r}.  Closest match: {spec}")
        return spec.pack(kw_params).strip()


def join_iterable[T: t.Iterable | t.Any](_key: str, value: T, delim: str) -> T | str:
    if isinstance(value, str):
        return value
    if isinstance(value, collections.abc.Iterable):
        return delim.join(str(f) for f in value)
    return value


def guard_no_spaces[T: t.Any](key: str, value: T, delim: str) -> T | str:
    as_str = str(value)
    if " " in as_str:
        raise ValueError(f"error: {key} cannot contain spaces")
    return as_str


DEFAULT_FORMATTERS = {
    "bool": lambda key, value: key if value else "",
    "nospace": guard_no_spaces,
    "join": lambda key, value: join_iterable(key, value, ""),
    "comma": lambda key, value: join_iterable(key, value, ","),
    "space": lambda key, value: join_iterable(key, value, " "),
    "": lambda _, value: format(value),
}
GLOBAL_COMMAND_SERIALIZER = CommandSerializer(formatters=DEFAULT_FORMATTERS)


def register_serializer_pattern(
    command: str,
    fmt: str,
    defaults: dict[str, t.Any] | None = None,
    deps: dict[str, str] | None = None,
    serializer: CommandSerializer = GLOBAL_COMMAND_SERIALIZER,
) -> CommandSpec:
    return serializer.register(command, fmt, defaults=defaults or {}, deps=deps or {})


def serialize(command: str, kw_params: ParamDict, *, serializer: CommandSerializer = GLOBAL_COMMAND_SERIALIZER) -> str:
    return serializer.serialize(command, kw_params)


# PASS
# https://tools.ietf.org/html/rfc2812#section-3.1.1
# PASS <password>
# ----------
# PASS secretpasswordhere
register_serializer_pattern("PASS", "PASS {password}")

# NICK
# https://tools.ietf.org/html/rfc2812#section-3.1.2
# NICK <nick>
# ----------
# NICK Wiz
register_serializer_pattern("NICK", "NICK {nick}")

# USER
# https://tools.ietf.org/html/rfc2812#section-3.1.3
# USER <user> [<mode>] :<realname>
# ----------
# USER guest 8 :Ronnie Reagan
# USER guest :Ronnie Reagan
register_serializer_pattern("USER", "USER {user} {mode} * :{realname}", defaults={"mode": 0})

# OPER
# https://tools.ietf.org/html/rfc2812#section-3.1.4
# OPER <user> <password>
# ----------
# OPER AzureDiamond hunter2
register_serializer_pattern("OPER", "OPER {user} {password}")

# USERMODE (renamed from MODE)
# https://tools.ietf.org/html/rfc2812#section-3.1.5
# MODE <nick> [<modes>]
# ----------
# MODE WiZ -w
# MODE Angel +i
# MODE
register_serializer_pattern("USERMODE", "MODE {nick:opt} {modes:opt}", deps={"modes": "nick"})

# SERVICE
# https://tools.ietf.org/html/rfc2812#section-3.1.6
# SERVICE <nick> <distribution> <type> :<info>
# ----------
# SERVICE dict *.fr 0 :French
register_serializer_pattern("SERVICE", "SERVICE {nick} * {distribution} {type} 0 :{info}")

# QUIT
# https://tools.ietf.org/html/rfc2812#section-3.1.7
# QUIT :[<message>]
# ----------
# QUIT :Gone to lunch
# QUIT
register_serializer_pattern("QUIT", "QUIT :{message:opt}")
register_serializer_pattern("QUIT", "QUIT")

# SQUIT
# https://tools.ietf.org/html/rfc2812#section-3.1.8
# SQUIT <server> [<message>]
# ----------
# SQUIT tolsun.oulu.fi :Bad Link
# SQUIT tolsun.oulu.fi
register_serializer_pattern("SQUIT", "SQUIT {server} :{message:opt}")
register_serializer_pattern("SQUIT", "SQUIT {server}")

# JOIN
# https://tools.ietf.org/html/rfc2812#section-3.2.1
# JOIN <channel> [<key>]
# ----------
# JOIN #foo fookey
# JOIN #foo
# JOIN 0
register_serializer_pattern("JOIN", "JOIN {channel:comma} {key:opt|comma}")

# PART
# https://tools.ietf.org/html/rfc2812#section-3.2.2
# PART <channel> :[<message>]
# ----------
# PART #foo :I lost
# PART #foo
register_serializer_pattern("PART", "PART {channel:comma} :{message:opt}")

# CHANNELMODE (renamed from MODE)
# https://tools.ietf.org/html/rfc2812#section-3.2.3
# MODE <channel> <modes> [<params>]
# ----------
# MODE #Finnish +imI *!*@*.fi
# MODE #en-ops +v WiZ
# MODE #Fins -s
register_serializer_pattern("CHANNELMODE", "MODE {channel} {params:space}")

# TOPIC
# https://tools.ietf.org/html/rfc2812#section-3.2.4
# TOPIC <channel> :[<message>]
# ----------
# TOPIC #test :New topic
# TOPIC #test :
# TOPIC #test

register_serializer_pattern("TOPIC", "TOPIC {channel} :{message}")
register_serializer_pattern("TOPIC", "TOPIC {channel}")

# NAMES
# https://tools.ietf.org/html/rfc2812#section-3.2.5
# NAMES [<channel>] [<target>]
# ----------
# NAMES #twilight_zone remote.*.edu
# NAMES #twilight_zone
# NAMES
register_serializer_pattern("NAMES", "NAMES {channel:opt|comma} {target:opt}", deps={"target": "channel"})

# LIST
# https://tools.ietf.org/html/rfc2812#section-3.2.6
# LIST [<channel>] [<target>]
# ----------
# LIST #twilight_zone remote.*.edu
# LIST #twilight_zone
# LIST
register_serializer_pattern("LIST", "LIST {channel:opt|comma} {target:opt}", deps={"target": "channel"})

# INVITE
# https://tools.ietf.org/html/rfc2812#section-3.2.7
# INVITE <nick> <channel>
# ----------
# INVITE Wiz #Twilight_Zone
register_serializer_pattern("INVITE", "INVITE {nick} {channel}")

# KICK
# https://tools.ietf.org/html/rfc2812#section-3.2.8
# KICK <channel> <nick> :[<message>]
# ----------
# KICK #Finnish WiZ :Speaking English
# KICK #Finnish WiZ,Wiz-Bot :Both speaking English
# KICK #Finnish,#English WiZ,ZiW :Speaking wrong language
register_serializer_pattern("KICK", "KICK {channel:comma} {nick:comma} :{message}")
register_serializer_pattern("KICK", "KICK {channel:comma} {nick:comma}")

# PRIVMSG
# https://tools.ietf.org/html/rfc2812#section-3.3.1
# PRIVMSG <target> :<message>
# ----------
# PRIVMSG Angel :yes I'm receiving it !
# PRIVMSG $*.fi :Server tolsun.oulu.fi rebooting.
# PRIVMSG #Finnish :This message is in english
register_serializer_pattern("PRIVMSG", "PRIVMSG {target} {message}")

# NOTICE
# https://tools.ietf.org/html/rfc2812#section-3.3.2
# NOTICE <target> :<message>
# ----------
# NOTICE Angel :yes I'm receiving it !
# NOTICE $*.fi :Server tolsun.oulu.fi rebooting.
# NOTICE #Finnish :This message is in english
register_serializer_pattern("NOTICE", "NOTICE {target} {message}")

# MOTD
# https://tools.ietf.org/html/rfc2812#section-3.4.1
# MOTD [<target>]
# ----------
# MOTD remote.*.edu
# MOTD
register_serializer_pattern("MOTD", "MOTD {target:opt}")

# LUSERS
# https://tools.ietf.org/html/rfc2812#section-3.4.2
# LUSERS [<mask>] [<target>]
# ----------
# LUSERS *.edu remote.*.edu
# LUSERS *.edu
# LUSERS
register_serializer_pattern("LUSERS", "LUSERS {mask:opt} {target:opt}", deps={"target": "mask"})

# VERSION
# https://tools.ietf.org/html/rfc2812#section-3.4.3
# VERSION [<target>]
# ----------
# VERSION remote.*.edu
# VERSION
register_serializer_pattern("VERSION", "VERSION {target:opt}")

# STATS
# https://tools.ietf.org/html/rfc2812#section-3.4.4
# STATS [<query>] [<target>]
# ----------
# STATS m remote.*.edu
# STATS m
# STATS
register_serializer_pattern("STATS", "STATS {query:opt} {target:opt}", deps={"target": "query"})

# LINKS
# https://tools.ietf.org/html/rfc2812#section-3.4.5
# LINKS [<remote>] [<mask>]
# ----------
# LINKS *.edu *.bu.edu
# LINKS *.au
# LINKS
register_serializer_pattern("LINKS", "LINKS {remote} {mask}")
register_serializer_pattern("LINKS", "LINKS {mask:opt}")

# TIME
# https://tools.ietf.org/html/rfc2812#section-3.4.6
# TIME [<target>]
# ----------
# TIME remote.*.edu
# TIME
register_serializer_pattern("TIME", "TIME {target:opt}")

# CONNECT
# https://tools.ietf.org/html/rfc2812#section-3.4.7
# CONNECT <target> <port> [<remote>]
# ----------
# CONNECT tolsun.oulu.fi 6667 *.edu
# CONNECT tolsun.oulu.fi 6667
register_serializer_pattern("CONNECT", "CONNECT {target} {port} {remote:opt}")

# TRACE
# https://tools.ietf.org/html/rfc2812#section-3.4.8
# TRACE [<target>]
# ----------
# TRACE
register_serializer_pattern("TRACE", "TRACE {target:opt}")

# ADMIN
# https://tools.ietf.org/html/rfc2812#section-3.4.9
# ADMIN [<target>]
# ----------
# ADMIN
register_serializer_pattern("ADMIN", "ADMIN {target:opt}")

# INFO
# https://tools.ietf.org/html/rfc2812#section-3.4.10
# INFO [<target>]
# ----------
# INFO
register_serializer_pattern("INFO", "INFO {target:opt}")

# SERVLIST
# https://tools.ietf.org/html/rfc2812#section-3.5.1
# SERVLIST [<mask>] [<type>]
# ----------
# SERVLIST *SERV 3
# SERVLIST *SERV
# SERVLIST
register_serializer_pattern("SERVLIST", "SERVLIST {mask:opt} {type:opt}", deps={"type": "mask"})

# SQUERY
# https://tools.ietf.org/html/rfc2812#section-3.5.2
# SQUERY <target> :<message>
# ----------
# SQUERY irchelp :HELP privmsg
register_serializer_pattern("SQUERY", "SQUERY {target} :{message}")

# WHO
# https://tools.ietf.org/html/rfc2812#section-3.6.1
# WHO [<mask>] ["o"]
# ----------
# WHO jto* o
# WHO *.fi
# WHO
register_serializer_pattern("WHO", "WHO {mask:opt} {o:opt|bool}", deps={"o": "mask"})

# WHOIS
# https://tools.ietf.org/html/rfc2812#section-3.6.2
# WHOIS [<target>] <mask>
# ----------
# WHOIS WiZ
# WHOIS eff.org trillian
register_serializer_pattern("WHOIS", "WHOIS {target} {mask:comma}")
register_serializer_pattern("WHOIS", "WHOIS {mask:comma}")

# WHOWAS
# https://tools.ietf.org/html/rfc2812#section-3.6.3
# WHOWAS <nick> [<count>] [<target>]
# ----------
# WHOWAS Wiz 9 remote.*.edu
# WHOWAS Wiz 9
# WHOWAS Mermaid
register_serializer_pattern("WHOWAS", "WHOWAS {nick:comma} {count:opt} {target:opt}", deps={"target": "count"})

# KILL
# https://tools.ietf.org/html/rfc2812#section-3.7.1
# KILL <nick> :<message>
# ----------
# KILL WiZ :Spamming joins
register_serializer_pattern("KILL", "KILL {nick} :{message}")

# PING
# https://tools.ietf.org/html/rfc2812#section-3.7.2
# PING <message> [<target>]
# ----------
# PING my-ping-token
# PING my-ping-token eff.org
# note:
#   https://github.com/ngircd/ngircd/blob/512af135d06e7dad93f51eae51b3979e1d4005cc/doc/Commands.txt#L146-L153
register_serializer_pattern("PING", "PING {message:nospace} {target:opt}")

# PONG
# https://tools.ietf.org/html/rfc2812#section-3.7.3
# PONG :[<message>]
# ----------
# PONG :I'm still here
# PONG
register_serializer_pattern("PONG", "PONG :{message:opt}")

# AWAY
# https://tools.ietf.org/html/rfc2812#section-4.1
# AWAY [:<message>]
# ----------
# AWAY :Gone to lunch.
# AWAY
register_serializer_pattern("AWAY", "AWAY :{message:opt}")
register_serializer_pattern("AWAY", "AWAY")

# REHASH
# https://tools.ietf.org/html/rfc2812#section-4.2
# REHASH
# ----------
# REHASH
register_serializer_pattern("REHASH", "REHASH")

# DIE
# https://tools.ietf.org/html/rfc2812#section-4.3
# DIE
# ----------
# DIE
register_serializer_pattern("DIE", "DIE")

# RESTART
# https://tools.ietf.org/html/rfc2812#section-4.4
# RESTART
# ----------
# RESTART
register_serializer_pattern("RESTART", "RESTART")

# SUMMON
# https://tools.ietf.org/html/rfc2812#section-4.5
# SUMMON <nick> [<target>] [<channel>]
# ----------
# SUMMON Wiz remote.*.edu #Finnish
# SUMMON Wiz remote.*.edu
# SUMMON Wiz
register_serializer_pattern("SUMMON", "SUMMON {nick} {target:opt} {channel:opt}", deps={"channel": "target"})

# USERS
# https://tools.ietf.org/html/rfc2812#section-4.6
# USERS [<target>]
# ----------
# USERS remote.*.edu
# USERS
register_serializer_pattern("USERS", "USERS {target:opt}")

# WALLOPS
# https://tools.ietf.org/html/rfc2812#section-4.7
# WALLOPS [:<message>]
# ----------
# WALLOPS :Maintenance in 5 minutes
register_serializer_pattern("WALLOPS", "WALLOPS :{message:opt}")

# USERHOST
# https://tools.ietf.org/html/rfc2812#section-4.8
# USERHOST <nick>
# ----------
# USERHOST Wiz Michael syrk
# USERHOST syrk
register_serializer_pattern("USERHOST", "USERHOST {nick:space}")

# ISON
# https://tools.ietf.org/html/rfc2812#section-4.9
# ISON <nick>
# ----------
# ISON Wiz Michael syrk
# ISON syrk
register_serializer_pattern("USERHOST", "USERHOST {nick:space}")
