if __name__ == "__main__":
    # Common client setup for all examples
    from .common import NICK, client, run


    @client.on("privmsg")
    def on_privmsg(nick, target, message, **kwargs):
        """ Echo all messages """
        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            target = nick

        client.send("privmsg", target=target, message=message)

    run()
