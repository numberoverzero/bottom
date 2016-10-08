Events
======

In bottom, an event is simply a string and set of ``**kwargs`` to be passed to
any handlers listening for that event:

.. code-block:: python

    @client.on('any string is fine')
    def handle(**kwargs):
        if 'potato' in kwargs:
            print("Found a potato!")

IRC Events
----------

While connected, a client will trigger events for valid IRC commands that it
receives, with kwargs according to that command's structure.  For example, the
"part" event will always include the nickmask (``nick``, ``user``, ``host``),
``message``, and ``channel`` kwargs, even if the message was empty:

.. code-block:: python

    @client.on("part")
    def handle(nick, user, host, message, channel, **kwargs):
        out = "User {}!{}@{} left {} with '{}'"
        print(out.format(nick, user, host, channel, message))

Because ``kwargs`` contains those fields, we could also use:

.. code-block:: python

    @client.on("part")
    def handle(**kwargs):
        out = ("User {nick}!{user}@{host} left"
               " {channel} with '{message}'")
        print(out.format(**kwargs))


Triggering
----------

The same mechanism that the client uses to dispatch events can be invoked
manually, either for custom events or to simulate receiving an irc command:

.. code-block:: python

    @client.on("privmsg")
    def handle(**kwargs):
        print("Someone sent a message!")

    client.trigger("privmsg")

Running the above won't print anything, however.  Triggering an event only
schedules the registered handlers (like the function we defined) to run *in
the future*.  Until we run the event loop, the triggered handlers won't be
invoked.  Let's see that print statement:

.. code-block:: python

    client.loop.run_forever()

We can pass arbitrary kwargs to handlers through ``trigger``:

.. code-block:: python

    client.trigger("event")
    client.trigger("event", **some_dict)
    client.trigger("event", nick="bot", message="hello, world")

Waiting
-------

Sometimes we need to wait for another event to occur before continuing.  For
example, consider a reconnect handler that wants to trigger the "reconnect"
event for some plugins, but only after the connection has actually been
established.  The following will incorrectly signal that the reconnect has
completed, while in reality the client has only scheduled a connection for the
future:

.. code-block:: python

    @client.on("client_disconnect")
    def reconnect(**kwargs):
        client.connect()
        client.trigger("reconnect", reconnect_msg="May not be connected!")


    @client.on("reconnect")
    def handle_reconnect(reconnect_msg="", **kwargs):
        if reconnect_msg:
            client.send("privmsg", target=CHANNEL, message=reconnect_msg)

Because both ``client.send`` and ``client.connect`` schedule coroutines, the
event loop may reorder (or process out of order).  In ``reconnect`` what we
really want to do is wait until the client_connect event is emitted, and then
trigger the reconnect event:

.. code-block:: python

    @client.on("client_disconnect")
    async def reconnect(**kwargs):
        client.connect()
        await client.wait("client_connect")
        client.trigger("reconnect", reconnect_msg="May not be connected!")

Whenever an event triggers, an ``asyncio.Event`` is set and cleared, which
allows any code that is waiting on that event to continue.  Be careful using
``client.wait`` - because we can call trigger with any string, ``wait`` will
allow us to wait (forever) for events that may never trigger.

Supported Events
----------------

.. code-block:: python

    # Local only events
    client.trigger('CLIENT_CONNECT')
    client.trigger('CLIENT_DISCONNECT')

* PING
* JOIN
* PART
* PRIVMSG
* NOTICE
* RPL_WELCOME (001)
* RPL_YOURHOST (002)
* RPL_CREATED (003)
* RPL_MYINFO (004)
* RPL_BOUNCE (005)
* RPL_MOTDSTART (375)
* RPL_MOTD (372)
* RPL_ENDOFMOTD (376)
* RPL_LUSERCLIENT (251)
* RPL_LUSERME (255)
* RPL_LUSEROP (252)
* RPL_LUSERUNKNOWN (253)
* RPL_LUSERCHANNELS (254)
* ERR_NOMOTD (422)
