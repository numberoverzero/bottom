.. _Migrations:

Migrating from 2.2.0 to 3.0
^^^^^^^^^^^^^^^^^^^^^^^^^^^


bottom changed substantially from 2.2.0 to 3.0 including a number of breaking changes.  below you'll find a summary of
the changes; an example of updating a small irc bot; and finally detailed sections per change.

If you encounter issues migrating, please use either the `existing issue`_  or `open a new issue`_.


.. _existing issue: https://github.com/numberoverzero/bottom/issues/71
.. _open a new issue: https://github.com/numberoverzero/bottom/issues/new


Summary
=======

3.0.0 comes with a number of improvements, both in tooling (static typing) and a simpler model (protocol decoupling).
In return for the breaking changes covered below, bottom now has:

* rich typing that survives subclassing and arbitrary function signatures, taking advantage of:

  * ParamSpec and Concatenate (`PEP 612 <https://docs.python.org/3/library/typing.html#typing.ParamSpec>`_)
  * Type Parameter Lists and Variance Inference (`PEP 695 <https://typing.python.org/en/latest/spec/generics.html#variance-inference>`_)
  * Deferred Type Annotations (`PEP 649 <https://peps.python.org/pep-0649/>`_)

  * combined, you can easily maintain the type of your client in a :data:`ClientMessageHandler<bottom.ClientMessageHandler>`
    to access custom attributes on that client:

    .. code-block:: python

        async def handle_spatial_query(
            next_handler: NextMessageHandler[SpatialClient],
            client: SpatialClient,
            message: bytes
        ) -> None:
            if not message.startswith(b"!q"):
                await next_handler(client, message)
            else:
                res = await client.db.process(message.decode(client._encoding)[2:])
                await client.send_packed_coords(res.coords, res.ctx)

* Decoupling of :class:`Client<bottom.Client>` and ``Protocol`` along the str/bytes boundary:

  * Previously clients and protocols knew about each other, making it hard to subclass one without also reimplementing
    the other.  Now you can use a Protcol without a Client, or the reverse.
  * Although not part of the public API, the Protocol can be used on its own with only implementing two callback functions.
  * Because the protocol no longer has to call ``Client.handle_raw(str)`` it avoids encodings entirely.
  * Because the Client's :attr:`message_handlers<bottom.Client.message_handlers>` have access to the incoming bytes,
    they can handle arbitrary bytes, including other encodings and encryptions.
  * The stack processing functionality has been simplified, and retains narrowed type checking for subclasses of Client.

* consistent behavior between an :meth:`Client.on<bottom.Client.on>` decorated handler and an awaited
  :meth:`Client.wait<bottom.Client.wait>` return value.  this allows you to not just wait for an event in an arbitrary
  function, but to also use the same ``**kwargs`` that were sent to each handler:

  .. code-block:: python

      @client.on("privmsg")
      async def print_nick(nick: str, **kw) -> None:
          print(f"saw nick {nick}")


      async def some_processor() -> None:
          res = await client.wait("privmsg")
          nick = res["nick"]
          print(f"saw nick {nick}")

* Blocking on a :meth:`Client.trigger<bottom.Client.trigger>` call until all handlers have run.  Implementing this
  before required one of two brittle solutions:

  #. Each handler sets an :py:class:`asyncio.Event` and the waiting code waits on the join of the events.  Clearing
     and resetting (eg. recursive triggers) gets much harder.
  #. Each handler trigger its own "ack" event that the waiting code would wait on the join of.  This usually results
     in a constants file to track all the event names, or a lot of whiteboard space.

  Instead you can wait on the return value from :meth:`trigger<bottom.Client.trigger>` -- when this completes, all
  handlers have finished running for this instance of the event.  The ``await`` is only on the single execution of
  each handler at the time you trigger the event, not any additional times the same event is triggered while waiting:

  .. code-block:: python

      import pandas

      @client.on("org.fizzbuzz.process")
      async def main_proc(cohort: pandas.DataFrame, **kw) -> None:
          log.debug("starting processing")
          await asyncio.sleep(60 * 5)
          log.debug("finished processing")

      @client.on("org.fizzbuzz.process")
      async def record_cohort(cohort, pandas.DataFrame, nick: str, name: str, **kw) -> None:
          external_audit_log.info(f"{nick} started processing cohort {name} at {now()}")


      concurrent_processes = set()

      @client.on("privmsg")
      async def process_cohort(nick: str, message: str, **kw) -> None:

          async def notify(msg: str) -> None:
              await client.send("privmsg", target=nick, message=msg)
          if not message.startswith("proc:"):
              return
          _, cohort_name = message.split(":", 1)
          if len(concurrent_processes) > MAX_CONCURRENT_PROCESS:
              log.info(f"")
              await notify(f"can't process {cohort_name}: no capacity")
              return
          frame = await lake.fetch(name=cohort_name)
          task = client.trigger(
            "org.fizzbuzz.process",
              nick=nick,
              data=frame,
              name=cohort_name,
          )
          task.add_done_callback(concurrent_processes.discard)
          await notify(f"started processing cohort {cohort_name}")
          await task
          await notify(f"finished processing cohort {cohort_name}")


Breaking Changes
----------------

These are approximately ordered by expected impact.

* minimum supported python version is now ``python3.12``
* ``Client.send`` is now ``async``
* ``Client.send_raw`` was renamed to ``Client.send_message`` and is now ``async``
* ``async Client.wait`` now returns the event dict, not just the event name

* ``Client.loop`` property was removed
* ``Client.handle_raw`` was removed
* ``Client.raw_handlers`` was renamed to ``Client.message_handlers``, signature changed
* ``Client.protocol`` was renamed to ``Client._protocol``
* ``Client.{host, port, ssl, encoding}`` were each renamed to ``Client.{_host, _port, _ssl, _encoding}``

* ``Client._loop`` was removed
* ``Client._connection_lost`` was removed


Major Changes
-------------

While not breaking, these may impact code that relied on bottom's implementation details.

* ``Client.trigger`` now returns an ``asyncio.Task`` that can be awaited to block until all handlers have finished
  processing the event.
* the ``**kwargs`` passed to each handler (through ``@Client.on`` or waiting with ``Client.wait``) now includes a key
  ``"__event__"`` which is the name of the event that was triggered.  If your handlers did not include ``**kwargs`` in
  their signatures, they will start receiving an unexpected argument ``__event__``.
* the internal ``_events`` was renamed ``_event_futures`` and is now a defaultdict of ``asyncio.Future`` instead of
  ``asyncio.Event``
* ``Protocol.{client, encoding}`` were each removed
* ``Protocol.write`` takes bytes instead of str
* added ``Client.is_closing()`` with the same contract as ``asyncio.Transport.is_closing()``
* if a client is connected, then ``Client.disconnect`` blocks until it sees itself emit ``"client_disconnect"``


Minor Changes
-------------

These include new features or changes which should not impact your ability to migrate, but may be noteworthy.

* :meth:`async wait_for<bottom.wait_for>` helper promoted from an example in the docs to a public function
* :data:`ClientMessageHandler<bottom.ClientMessageHandler>` and :data:`NextMessageHandler<bottom.NextMessageHandler>`
  types now part of the public api to help with type hinting custom message handlers.
* type hints and overloads updated or added for all public interfaces, internal interfaces, most test code, examples,
  and docs.
* ``bottom.util.create_task`` ensures created tasks will not be gc'd, even if you do not keep a reference to the created
  task.  while this is not part of the public api, it is referenced throughout this migration guide.  you're welcome to
  copy the implementation into your own util module, if you don't have it already:

  .. code-block:: python

      import asyncio
      import typing as t
      _background_tasks: set[asyncio.Task] = set()

      def create_task[T](x: t.Coroutine[t.Any, t.Any, T]) -> asyncio.Task[T]:
          task = asyncio.create_task(x)
          task.add_done_callback(_background_tasks.discard)
          _background_tasks.add(task)
          return task

* new examples ``encryption.py`` and ``registry.py`` corresponding to new sections of the extensions documentation
  (:ref:`encryption<ex-encryption>`, :ref:`registry<ex-plugins>`)


Example Migration
=================

The following is a 2.2.0 client with the following features.  These are referenced in the before and after code so
that you can copy sections of interest.  You can also view both files in the repo under ``examples/migration``.

* \(A\) a raw message handler that prints every incoming message
* \(B\) periodically calls handle_raw to inject random privmsg
* \(C, D\) triggers blocking and non-blocking custom events
* \(E\) sends well-formed rfc2812 commands
* \(F\) sends raw messages
* \(G\) waits for custom events
* \(H, I\) uses sync and async handlers
* \(J\) has a poorly formed sync handler
* \(K\) races multiple waits and prints the first completed event

This sample was tested with ``python3.8.20`` and bottom commit `eddceacbaef6fda4160ee7f6f1c375e84fbb99fc`_
which was released to PyPi on `2020-08-06 <https://pypi.org/project/bottom/#history>`_

.. _eddceacbaef6fda4160ee7f6f1c375e84fbb99fc: https://github.com/numberoverzero/bottom/tree/eddceacbaef6fda4160ee7f6f1c375e84fbb99fc


Before - 2.2.0
--------------

*(The full source for this file is available at examples/migration/v3.0.0.py)*

.. code-block:: python

    import asyncio
    import random

    from bottom import Client

    HOST = "chat.freenode.net"
    PORT = 6697
    SSL = True

    NICK = "bottom-bot"
    CHANNEL = "#bottom-dev"
    FAKE_NICK = "casper"

    client = Client(host=HOST, port=PORT, encoding="utf-8", ssl=SSL)


    # (A) a raw message handler that prints every incoming message
    def make_printer(client: Client):
        async def print_every_message(next_handler, message):
            print(f"{client.host}:{client.port} <<< {message}")
            await next_handler(message)

        return print_every_message


    # (A) a raw message handler that prints every incoming message
    client.raw_handlers.insert(0, make_printer(client))


    # (B) periodically calls handle_raw to inject random privmsg
    async def inject_random_messages():
        try:
            while True:
                delay = 10 + random.random() * 2
                print(f"sleeping {delay} before injecting another message")
                await asyncio.sleep(delay, loop=client.loop)
                print("injecting fake message")
                client.handle_raw(f":{FAKE_NICK}!user@host PRIVMSG #{NICK} :spooky ghosts!")
        except asyncio.CancelledError:
            pass


    # (C) triggers blocking events
    # need to use an Event for the caller to wait for this to finish
    slow_event_done = asyncio.Event(loop=client.loop)


    # (C) triggers blocking events
    @client.on("my.slow.event")
    async def handle_slow_event(delay, **kw):
        slow_event_done.clear()
        print(f"slow event sleeping for {delay}")
        await asyncio.sleep(delay, loop=client.loop)
        print("slow event done")
        slow_event_done.set()


    # (D) triggers non-blocking custom events
    @client.on("my.fast.event")
    async def handle_fast_event(delay, **kw):
        print(f"fast event sleeping for {delay / 4}")
        await asyncio.sleep(delay / 4, loop=client.loop)
        print("fast event done, triggering complete event")
        client.trigger("my.fast.event.done")


    def send_messages():
        # (E) sends well-formed rfc2812 commands
        print("sending a LIST command")
        client.send("list", channel=CHANNEL)

        # (F) sends raw messages
        print("sending a raw PART command")
        client.send_raw(f"PART {CHANNEL}")


    # (H) uses sync handlers
    @client.on("PING")
    def keepalive(message, **kwargs):
        print(f"<<< ping {message}")
        client.send("PONG", message=message)
        print(f">>> pong {message}")


    # (I) uses async handlers
    @client.on("privmsg")
    async def message(nick, target, message, **kwargs):
        if nick == NICK:
            return
        if nick == FAKE_NICK:
            print(f"ignoring injected message from {FAKE_NICK}: {message}")
            return
        if target == NICK:
            print(f"responding directly to {nick}")
            target = nick
        else:
            print(f"responding in channel {target}")
        client.send("privmsg", target=target, message=message)


    # (J) has a poorly formed sync handler
    @client.on("join")
    def join(nick, user, host, channel):
        print(f"saw {nick} join {channel}")


    # (K) races multiple waits and prints the first completed event
    @client.on("CLIENT_CONNECT")
    async def connect(**kwargs):
        client.send("NICK", nick=NICK)
        client.send("USER", user=NICK, realname="https://github.com/numberoverzero/bottom")

        # Don't try to join channels until the server has
        # sent the MOTD, or signaled that there's no MOTD.
        done, pending = await asyncio.wait(
            [client.wait("RPL_ENDOFMOTD"), client.wait("ERR_NOMOTD")],
            loop=client.loop,
            return_when=asyncio.FIRST_COMPLETED,
        )
        names = [x.result() for x in done]

        print(f"first complete events were {names}")

        # Cancel whichever waiter's event didn't come in.
        for future in pending:
            future.cancel()

        client.send("JOIN", channel=CHANNEL)
        print("sent join")


    async def main():
        client.loop.create_task(inject_random_messages())

        # (C) triggers blocking custom events
        print("triggering and waiting for my.slow.event")
        client.trigger("my.slow.event", delay=2.5)
        await slow_event_done.wait()

        # (D) triggers non-blocking custom events
        print("triggering and not waiting for my.fast.event")
        client.trigger("my.fast.event", delay=10)
        print("done triggering fast event")

        # (G) waits for custom events
        print("waiting for my.fast.event.done")
        await client.wait("my.fast.event.done")
        print("finished waiting for fast done event")

        print("connecting")
        await client.connect()

        print("waiting to see join before sending messages")
        await client.wait("join")
        print("sending some messages")
        send_messages()

        print("done warmup logic, waiting until disconnect occurs")
        try:
            await client.wait("client_disconnect")
        except asyncio.CancelledError:
            print("task was cancelled - manually disconnecting")
            await client.disconnect()
            print("disconnected")


    if __name__ == "__main__":
        import sys

        import bottom

        print(f"python: {sys.version}")
        print(f"bottom: {bottom.__version__}")
        task = client.loop.create_task(main())
        try:
            client.loop.run_forever()
        except KeyboardInterrupt:
            print("saw ctrl+c, canceling task")
            task.cancel()


After - 3.0.0
-------------

*(The full source for this file is available at examples/migration/v3.0.0.py)*

.. code-block:: python

    # fmt: off
    # isort: skip_file
    import asyncio
    import random
    import typing as t

    from bottom import Client, NextMessageHandler
    # note: this is trivially implemented in your own code, feel free to copy from github or the migration guide
    from bottom.util import create_task

    HOST = "chat.freenode.net"
    PORT = 6697
    SSL = True

    NICK = "bottom-bot"
    CHANNEL = "#bottom-dev"
    FAKE_NICK = "casper"

    client = Client(host=HOST, port=PORT, encoding="utf-8", ssl=SSL)


    # (A) a raw message handler that prints every incoming message
    # FIX: add client to args, pass client into next_handler, handle bytes -> str decoding
    async def print_every_message(next_handler: NextMessageHandler[Client], client: Client, message: bytes) -> None:
        print(f"{client._host}:{client._port} <<< {message.decode(client._encoding)}")
        await next_handler(client, message)


    # (A) a raw message handler that prints every incoming message
    # FIX: raw_handlers -> message_handlers, and we no longer need the wrapper function
    client.message_handlers.insert(0, print_every_message)


    # (B) periodically calls handle_raw to inject random privmsg
    # FIX: no longer need to pass loop to asyncio.sleep
    # FIX: two options to manually trigger raw messages:
    #   1. subclass Client and implement a method that calls client._protocol.data_received(bytes)
    #   2. subclass Client and provide a custom Protocol
    # the first option is recommended and much easier.
    async def inject_random_messages() -> None:
        try:
            while True:
                delay = 10 + random.random() * 2
                print(f"sleeping {delay} before injecting another message")
                await asyncio.sleep(delay)
                print("injecting fake message")

                msg = f":{FAKE_NICK}!user@host PRIVMSG #{NICK} :spooky ghosts!\r\n"
                assert client._protocol is not None
                client._protocol.data_received(msg.encode(client._encoding))
        except asyncio.CancelledError:
            pass


    # (C) triggers blocking events
    # FIX: no longer need an asyncio.Event since the caller can await client.trigger()
    # to block until this (and all handlers for the event) have completed.
    @client.on("my.slow.event")
    async def handle_slow_event(delay: float, **kw: t.Any) -> None:
        print(f"slow event sleeping for {delay}")
        await asyncio.sleep(delay)
        print("slow event done")


    # (D) triggers non-blocking custom events
    # FIX: no change to client.trigger - we can ignore the returned task if we don't want to wait
    @client.on("my.fast.event")
    async def handle_fast_event(delay: float, **kw: t.Any) -> None:
        print(f"fast event sleeping for {delay / 4}")
        await asyncio.sleep(delay / 4)
        print("fast event done, triggering complete event")
        client.trigger("my.fast.event.done")


    # (E, F) FIX OPTION 1:
    #     make the function async, and use await client.send and await client.send_message
    async def send_messages() -> None:
        # (E) sends well-formed rfc2812 commands
        print("sending a LIST command")
        await client.send("list", channel=CHANNEL)

        # (F) sends raw messages
        # FIX: send_raw -> await send_message
        print("sending a raw PART command")
        await client.send_message(f"PART {CHANNEL}")


    #  (E, F) FIX OPTION 2:
    #     keep the function async, and use create_task to schedule the client.send and client.send_message
    def send_messages_fix_2() -> None:
        # (E) sends well-formed rfc2812 commands
        print("sending a LIST command")
        create_task(client.send("list", channel=CHANNEL))

        # (F) sends raw messages
        # FIX: send_raw -> send_message
        print("sending a raw PART command")
        create_task(client.send_message(f"PART {CHANNEL}"))


    # (H) uses sync handlers
    # FIX: same options as E, F above:
    #     1. either make the function asnc so you can `await` the client.send
    #  OR 2. wrap the client.send calls in create_task() to schedule them
    @client.on("PING")
    async def keepalive(message: str, **kwargs: t.Any) -> None:
        print(f"<<< ping {message}")
        await client.send("PONG", message=message)
        print(f">>> pong {message}")


    # (I) uses async handlers
    # FIX: since this example is already async, just await the client.send
    @client.on("privmsg")
    async def message(nick: str, target: str, message: str, **kwargs: t.Any) -> None:
        if nick == NICK:
            return
        if nick == FAKE_NICK:
            print(f"ignoring injected message from {FAKE_NICK}: {message}")
            return
        if target == NICK:
            print(f"responding directly to {nick}")
            target = nick
        else:
            print(f"responding in channel {target}")
        await client.send("privmsg", target=target, message=message)


    # (J) has a poorly formed sync handler
    # FIX: without changes, this raises because there's a new argument named __event__
    #   two options:
    #     1. add **kwargs (or **kw, etc) to the signature to capture new/unused args  (RECOMMENDED)
    #     2. add __event__ as an explicit argument
    #   the first option is strongly recommended, and is part of the semver contract in bottom:
    #     arguments may be added to handlers in minor versions.
    @client.on("join")
    def join(nick: str, user: str, host: str, channel: str, **kw: t.Any) -> None:
        print(f"saw {nick} join {channel}")


    # (K) races multiple waits and prints the first completed event
    # FIX: use the new `wait_for` method:
    from bottom import wait_for
    @client.on("CLIENT_CONNECT")
    async def connect(**kwargs: t.Any) -> None:
        await client.send("NICK", nick=NICK)
        await client.send("USER", user=NICK, realname="https://github.com/numberoverzero/bottom")

        first = await wait_for(client, ["RPL_ENDOFMOTD", "ERR_NOMOTD"], mode="first")
        names = [x["__event__"] for x in first]
        print(f"first complete events were {names}")

        await client.send("JOIN", channel=CHANNEL)
        print("sent join")


    async def main() -> None:
        # FIX: within an async block we no longer need an explicit loop
        create_task(inject_random_messages())

        # (C) triggers blocking custom events
        # FIX: no longer need an asyncio.Event, we can directly wait on the client.trigger
        #     once all handlers have run for "my.slow.event" we'll resume in this coro
        print("triggering and waiting for my.slow.event")
        await client.trigger("my.slow.event", delay=2.5)

        # (D) triggers non-blocking custom events
        # FIX: no change, we can safely ignore the return value from client.trigger
        print("triggering and not waiting for my.fast.event")
        client.trigger("my.fast.event", delay=10)
        print("done triggering fast event")

        # (G) waits for custom events
        # FIX: return value is a dict instead of a string; either look up the name via __event__
        #    or make use of the rest of the kwargs that were passed to the event
        print("waiting for my.fast.event.done")
        ret = await client.wait("my.fast.event.done")
        print(f"event name was {ret['__event__']}")
        print("finished waiting for fast done event")

        print("connecting")
        await client.connect()

        print("waiting to see join before sending messages")
        await client.wait("join")
        print("sending some messages")
        # (E, F)
        # FIX: depends which option was used above.
        #  the first option just made the function async, so await it:
        await send_messages()
        # the second option left the function sync, so just call it:
        send_messages_fix_2()

        print("done warmup logic, waiting until disconnect occurs")
        try:
            await client.wait("client_disconnect")
        except asyncio.CancelledError:
            print("task was cancelled - manually disconnecting")
            await client.disconnect()
            print("disconnected")


    if __name__ == "__main__":
        import sys
        import bottom

        print(f"python: {sys.version}")
        print(f"bottom: {bottom.__version__}")
        # FIX: don't want to use create_task here since there's no active event loop
        # luckily, asyncio.run() exists
        coro = main()
        try:
            asyncio.run(coro)
        except KeyboardInterrupt:
            print("saw ctrl+c, canceling task")
            coro.throw(asyncio.CancelledError)




Detailed Guides
===============


Client.send is now async
------------------------


Client.send_raw renamed, now async
----------------------------------


Client.wait returns dict
------------------------


Client.loop removed
-------------------


Client.handle_raw removed
-------------------------


Client.raw_handlers changes
---------------------------


Client.protocol renamed
-----------------------


host, port, ssl, encoding renamed
---------------------------------


Client._loop removed
--------------------


Client._connection_lost removed
-------------------------------


Client.trigger returns Task
---------------------------


event kwargs includes ``__event__``
-----------------------------------


Protocol.{client,encoding} removed
----------------------------------


Protocol.write takes bytes
--------------------------


added Client.is_closing()
-------------------------


disconnect waits for ``client_disconnect``
------------------------------------------
