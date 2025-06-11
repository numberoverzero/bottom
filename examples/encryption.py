from __future__ import annotations

import asyncio
import base64
import typing as t

from bottom import Client, ClientMessageHandler, NextMessageHandler, wait_for

ACTUALLY_ENCRYPTING = False


class EncryptionContext:
    async def encrypt(self, data: bytes) -> bytes:
        # TODO implement encryption
        print("pretending to encrypt")
        await asyncio.sleep(0.2)
        return data

    async def decrypt(self, data: bytes) -> bytes:
        # TODO implement encryption
        print("pretending to decrypt")
        await asyncio.sleep(0.2)
        return data


def make_decrypt_handler(ctx: EncryptionContext) -> ClientMessageHandler:
    async def decrypt_message(next_handler: NextMessageHandler, message: str) -> None:
        if ACTUALLY_ENCRYPTING:
            # note: this won't work on a standard server because it won't just send us b64 encoded lines
            encrypted_bytes = base64.b64decode(message.encode())
        else:
            encrypted_bytes = message.encode()
        decrypted_bytes = await ctx.decrypt(encrypted_bytes)
        decrypted_str = decrypted_bytes.decode()
        print(f"next_handler got: {decrypted_str}")
        await next_handler(decrypted_str)

    return decrypt_message


class EncryptingClient(Client):
    ctx: EncryptionContext

    def __init__(self, ctx: EncryptionContext, *a: t.Any, **kw: t.Any) -> None:
        super().__init__(*a, **kw)
        self.ctx = ctx
        decrypt_handler = make_decrypt_handler(ctx)
        self.message_handlers.insert(0, decrypt_handler)

    async def send_message(self, message: str) -> None:
        plaintext_bytes = message.encode()
        ciphertext_bytes = await self.ctx.encrypt(plaintext_bytes)
        if ACTUALLY_ENCRYPTING:
            # note: this won't work on a standard server because it doesn't know wtf to do with a b64 encoded line
            ciphertext_str = base64.b64encode(ciphertext_bytes).decode()
        else:
            ciphertext_str = ciphertext_bytes.decode()
        await super().send_message(ciphertext_str)


if __name__ == "__main__":
    # Common client setup for all examples
    from examples.common import CHANNEL, NICK, host, port, run, ssl

    ctx = EncryptionContext()
    client = EncryptingClient(ctx, host=host, port=port, ssl=ssl)

    @client.on("client_connect")
    async def on_connect(**kwargs: t.Any) -> None:
        print("connecting")
        await client.send("nick", nick=NICK)
        await client.send("user", user=NICK, realname="https://github.com/numberoverzero/bottom")
        print("sent nick, user")

        # This waits for the 'rpl_endofmotd' and 'err_nomotd' commands,
        # returning when one of them is triggered. 'events' is a list,
        # but it will only contain one item in this case since only one
        # of these commands will be sent by the server.
        events = await wait_for(client, ["rpl_endofmotd", "err_nomotd"], mode="first")

        # The event names returned are the same as the ones given, so
        # we can easily check for them in the result.
        if "rpl_endofmotd" in events:
            print("MOTD returned")
        elif "err_nomotd" in events:
            print("No MOTD returned")

        await client.send("join", channel=CHANNEL)

    @client.on("ping")
    async def keepalive(message: str, **kwargs: t.Any) -> None:
        print(f"<<< ping {message}")
        await client.send("pong", message=message)
        print(f">>> ping {message}")

    @client.on("privmsg")
    async def echo(nick: str, target: str, message: str, **kwargs: t.Any) -> None:
        # Don't echo ourselves
        if nick == NICK:
            return
        # Respond directly to direct messages
        if target == NICK:
            target = nick
        await client.send("privmsg", target=target, message=message)

    run(client)
