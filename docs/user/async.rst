Using Async
===========

It's easy to do async wrong.  Check out some of bottom's `past issues`_ for an
example of how easy it is to use the ``async`` and ``await`` constructs
incorrectly.

To simplify things, bottom lets us to pass both synchronous and
async functions as callbacks.  Both of these are valid handlers for the
``privmsg`` event:

.. code-block:: python

    @client.on('privmsg')
    def synchronous_handler(**kwargs):
        print("Synchronous call")


    @client.on('privmsg')
    async def async_handler(**kwargs):
        await asyncio.sleep(1, loop=client.loop)
        print("Async call")

.. _past issues: https://github.com/numberoverzero/bottom/issues/12

Event Loop Gotchas
------------------

If none is provided, ``Client`` will use the default event loop.  This is fine
if we're only running the client by itself, but it's recommended to still
parameterize any async calls that have a loop parameter.

Here's an easy way to hang the client forever:

.. code-block:: python

    import asyncio
    import bottom

    client = bottom.Client(
        host='localhost', port=6697, ssl=True,
        loop=asyncio.new_event_loop())


    @client.on('client_connect')
    async def handle(**kwargs):
        print("Before await")
        await asyncio.sleep(1)
        print("After await")

    client.loop.run_until_complete(client.connect())
    client.loop.run_forever()

See the bug? Try running it.

In the second line of ``handle``, ``asyncio.sleep`` takes an **optional**
loop kwarg, which is the event loop to run on.  This defaults to
``asyncio.get_event_loop``.  However, we're running the client on
``client.loop``.  Since the default loop never runs, the code will
wait forever.

Here's the correct handle:

.. code-block:: python

    @client.on('client_connect')
    async def handle(**kwargs):
        print("Before await")
        await asyncio.sleep(1, loop=client.loop)
        print("After await")

Connect/Disconnect
------------------

Client connect and disconnect are coroutines so that we can easily wait for
their completion before performing more actions in a handler.  However, we
don't always want to wait for the action to complete.  How can we do both?

Let's say that on disconnect we want to reconnect, then notify the room that
we're back.  We need to ``await`` for the connection before sending anything:

.. code-block:: python

    @client.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(2, loop=client.loop)

        # Wait until we've reconnected
        await client.connect()

        # Notify the room
        client.send('privmsg', target='#bottom-dev',
                    message="I'm baaack!")

What about a handler that doesn't need an established connection to finish?
Instead of notifying the room, let's log the reconnect time and return:

.. code-block:: python

    import arrow
    import logging
    logger = logging.getLogger(__name__)


    @client.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(2, loop=client.loop)

        # Schedule a connection when the loop's next available
        client.loop.create_task(client.connect())

        # Record the time of the disconnect event
        now = arrow.now()
        logger.info("Reconnect started at " + now.isoformat())

We can also wait for the ``client_connect`` event to trigger, which is slightly
different than waiting for client.connect to complete:

.. code-block:: python

    @client.on('client_disconnect')
    async def reconnect(**kwargs):
        # Wait a second so we don't flood
        await asyncio.sleep(2, loop=client.loop)

        # Schedule a connection when the loop's next available
        client.loop.create_task(client.connect())

        # Wait until client_connect has triggered
        await client.wait("client_connect")

        # Notify the room
        client.send('privmsg', target='#bottom-dev',
                    message="I'm baaack!")

Existing Event Loop
-------------------

We can specify an event loop that the client will run on:

.. code-block:: python

    client = bottom.Client(..., loop=my_existing_event_loop)

Debugging
---------

You can get more asyncio debugging info by setting up an event loop with debugging enabled,
and pass that loop to ``bottom.Client``:

.. code-block:: python

    import asyncio
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    bot = bottom.Client(..., loop=loop)
