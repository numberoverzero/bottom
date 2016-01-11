import asyncio
from bottom.unpack import unpack_command
DELIM = b"\r\n"


class Protocol(asyncio.Protocol):
    @classmethod
    def factory(cls, client):
        """Creates a factory method appropriate for create_connection which
        returns an instance of the protocol bound to the given client.

        Example
        -------
        import bottom

        client = bottom.Client(...)
        protocol_factory = Protocol.factory(client)
        await client.loop.create_connection(protocol_factory, ...)
        """
        return lambda: cls(client)

    def __init__(self, client):
        self.client = client
        client.protocol = self
        self.transport = None
        self.connected = False
        self.buffer = b""

    def connection_made(self, transport):
        self.transport = transport
        self.connected = True
        self.client.trigger(
            "client_connect", host=self.client.host, port=self.client.port)

    def connection_lost(self, exc):
        self.connected = False
        self.client.trigger(
            "client_disconnect", host=self.client.host, port=self.client.port)
        self.close()


    def data_received(self, data):
        self.buffer += data
        # All but the last result of split should be pushed into the
        # client.  The last will be b"" if the buffer ends on b"\r\n"
        *lines, self.buffer = self.buffer.split(DELIM)
        for line in lines:
            message = line.decode(self.client.encoding, "ignore").strip()
            try:
                event, kwargs = unpack_command(message)
                self.client.trigger(event, **kwargs)
            except ValueError:
                print("PARSE ERROR {}".format(message))

    def write(self, message):
        data = message.encode(self.client.encoding)
        if not data.endswith(DELIM):
            data += DELIM
        self.transport.write(data)

    def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None
