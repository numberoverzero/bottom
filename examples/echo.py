import typing as t

if __name__ == "__main__":
    # Common client setup for all examples
    from examples.common import NICK, client, run

    @client.on("privmsg")
    async def on_privmsg(nick: str, target: str, message: str, **kwargs: t.Any) -> None:
        """Echo all messages"""
        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            target = nick

        await client.send("privmsg", target=target, message=message)

    run()
