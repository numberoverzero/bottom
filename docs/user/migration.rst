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

#. rich typing that survives subclassing and arbitrary function signatures, taking advantage of:

   * ParamSpec and Concatenate (`PEP 612 <https://docs.python.org/3/library/typing.html#typing.ParamSpec>`_)
   * Type Parameter Lists and Variance Inference (`PEP 695 <https://typing.python.org/en/latest/spec/generics.html#variance-inference>`_)
   * Deferred Type Annotations (`PEP 649 <https://peps.python.org/pep-0649/>`_)

   together these let you easily maintain type checking for your subclass of :class:`Client<bottom.Client>` as
   it passes through :data:`ClientMessageHandler<bottom.ClientMessageHandler>`:

     .. code-block:: python

         async def handle_spatial_query(
             next_handler: NextMessageHandler[SpatialClient],
             client: SpatialClient,
             message: bytes
         ) -> None:
             if not message.startswith(b"!q"):
                 await next_handler(client, message)
             else:
                 req = message[2:].strip().decode(client._encoding)
                 res = await client.db.process(req)
                 await client.send_packed_coords(res.coords, res.ctx)

#. Decoupling of :class:`Client<bottom.Client>` and ``Protocol`` along the str/bytes boundary:

   * Previously clients and protocols knew about each other, making it hard to subclass one without also reimplementing
     the other.  Now you can use a Protcol without a Client, or the reverse.
   * Alternatively, you now only need to implement two callback functions to use the Protocol directly.
   * The protocol doesn't have to call ``Client.handle_raw(str)`` so it avoids encodings entirely.
   * Now that :attr:`message_handlers<bottom.Client.message_handlers>` has access to raw bytes, they can handle
     other encodings.  Non-utf-8 characters were previously ignored silently.
   * The stack processing retains narrowed type checking for subclasses of Client.

#. consistent behavior between an :meth:`Client.on<bottom.Client.on>` decorated handler and an awaited
   :meth:`Client.wait<bottom.Client.wait>` return value.  this allows you to not just wait for an event in an arbitrary
   function, but to also use the same ``**kwargs`` that were sent to each handler:

   .. code-block:: python

       @client.on("privmsg")
       async def print_nick(nick: str, **kw) -> None:
           print(f"saw nick {nick}")


       async def process() -> None:
           res = await client.wait("privmsg")
           nick = res["nick"]
           print(f"saw nick {nick}")

#. Blocking on a :meth:`Client.trigger<bottom.Client.trigger>` call until all handlers have run.  Implementing this
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
    #   1. subclass Client and implement a method that calls client._protocol.on_message(bytes)
    #   2. subclass Client and provide a custom Protocol
    # the first option is recommended and much easier.
    async def inject_random_messages() -> None:
        try:
            while True:
                delay = 10 + random.random() * 2
                print(f"sleeping {delay} before injecting another message")
                await asyncio.sleep(delay)
                print("injecting fake message")

                msg = f":{FAKE_NICK}!user@host PRIVMSG #{NICK} :spooky ghosts!"
                assert client._protocol is not None
                client._protocol.on_message(msg.encode(client._encoding))
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


.. _m-client-send:

Client.send is now async
------------------------

If you're calling :meth:`Client.send<bottom.Client.send>` from an async function, the easiest fix is to ``await``
the call:

.. code-block:: python

    async def process():
        # client.send("privmsg", target="#chan", message="hello")
        # becomes
        await client.send("privmsg", target="#chan", message="hello")

If you're calling send from a non async function, you have two choices:

#. if possible, make your function async and then use the previous.
#. if you can't make your function async, you can wrap the call in :func:`asyncio.create_task` or use the same from
   ``bottom.util``:

.. code-block:: python

    def some_fn():
        # client.send("privmsg", target="#chan", message="hello")
        # becomes
        coro = client.send("privmsg", target="#chan", message="hello")
        asyncio.create_task(coro)
        # or
        bottom.util.create_task(coro)

if you use :func:`asyncio.create_task` make sure you read the warning about garbage collecting and weakrefs.
bottom.util.create_task handles this for you.


Client.send_raw renamed, now async
----------------------------------

Similar to the changes above for :ref:`Client.send<m-client-send>` you simply need to rename
any occurrences of "send_raw" with "send_message" and then either ``await`` the call or, if you cannot make your
function async, wrap the call in ``create_task``:

.. code-block:: python

    def some_fn():
        # client.send_raw("JOIN #chan hunter2")
        # becomes
        coro = client.send_raw("JOIN #chan hunter2")
        asyncio.create_task(coro)
        # or
        bottom.util.create_task(coro)


Client.wait returns dict
------------------------

Previously, :meth:`Client.wait<bottom.Client.wait>` returned a string, which was the event that was being waited on.
This allowed you to collect them or pass the coro to another function and when the wait finished, it would know which
event finished.

Now, the entire dict that was triggered, including the event name, is passed to wait.  This is equivalent to the kwargs
passed to a handler registered with :meth:`Client.on<bottom.Client.on>`, and the event name is under the key (or arg)
``""__event__"``.

If your code didn't use the return value of Client.wait, then you can ignore this change.

If you previously used that string, you can update your code as follows:

.. code-block:: python

    async def process():
        # name = await client.wait("my.event")
        # becomes
        event = await client.wait("my.event")
        name = event["__event__"]

If you want, you can also inspect the other kwargs that were passed:

.. code-block:: python

    async def process():
        event = await client.wait("privmsg")
        print("{nick} said {message} to {target}".format(**event))


.. _m-client-loop:

Client.loop removed
-------------------

asyncio has made significant improvements since bottom was first implemented.  In many cases you were accessing
``Client.loop`` from an async context (within an async function, or within a sync function that was being called from
an event loop) and the loop is now available from :func:`asyncio.get_running_loop`.  Further, most functions no longer
require (or even allow!) an explicit loop parameter.

.. code-block:: python

    asyc def process():
        # event = asyncio.Event(loop=client.loop)
        # becomes
        event = asyncio.Event()

for synchronous functions that are being called from the event loop, eg. they're decorated with
:meth:`Client.on<bottom.Client.on>` you can use:

.. code-block:: python

    @client.on("privmsg")
    def process(**kw):
        # event = asyncio.Event(loop=client.loop)
        # becomes
        event = asyncio.Event(loop=asyncio.get_running_loop())


Client.handle_raw removed
-------------------------

It's not common to need to inject a *complete* irc line into your client - it's often simpler to use
:meth:`Client.trigger<bottom.Client.trigger>` and handle the event with :meth:`Client.on<bottom.Client.on>` or
:meth:`Client.wait<bottom.Client.wait>`.  If you still need this functionality, you can subclass Client and push data
into its Protocol:

.. code-block:: python

    from bottom import Client

    class MyClient(Client):
        def trigger_message(self, message: str) -> None:
            as_bytes = message.strip().encode(self._encoding)
            self._protocol.on_message(as_bytes)


    async def process():
        # client.handle_raw("JOIN #chan")
        # becomes
        client.trigger_message("JOIN #chan")


Client.raw_handlers changes
---------------------------

There were a number of changes to ``raw_handlers``.  To start, here's the migration of a simple handler that prints
the incoming message and then calls the next handler in the chain:

.. code-block:: python

    # 2.2.0
    async def print_message(next_handler, message: str) -> None:
        print(message)
        await next_handler(message)

    v2client.raw_handlers.insert(0, print_message)


    # 3.0.0
    async def print_message(next_handler, client: Client, message: bytes) -> None:
        print(message.decode(client._encoding))
        await next_handler(client, message)

    v3client.message_handlers.insert(0, print_message)

The primary changes are passing ``message`` as bytes instead of a string, and the introduction of a ``client``
argument in the second position, which also needs to be forwarded to the ``next_handler``.

The typing has improved significantly.  Previously the signature of ``next_handler`` was ``typing.Callable`` with no
parameters.  Now, the function takes a subclass of :class:`Client<bottom.Client>` as a generic parameter, which allows
you to access attributes of that subclass.

This is the 3.0.0 signature for ``print_message`` above:

.. code-block:: python

    from bottom import NextMessageHandler

    async def print_message(
      next_handler: NextMessageHandler[Client],
      client: Client,
      message: bytes) -> None: ...


Finally, you probably used a wrapper function that captured a ``client`` argument, so you had access to the client when
the message handler was called:

.. code-block:: python


    # 2.2.0 -- binding the client so it's available later
    def print_message_factory(client: Client):
        async def print_message(next_handler, message: str):
            print(f"{client.host}:{client.port} -- {message}")
            await next_handler(message)
        return print_message


    # usage: need the client to pass into the client's raw_handler
    v2client.raw_handlers.insert(0, print_message_factory(v2client))

In 3.0.0 this is no longer necessary, since the client is passed through the handler stack.


Client.protocol renamed
-----------------------

This is now a protected attribute on the Client:

.. code-block:: python

    # client.protocol
    # becomes
    client._protocol


host, port, ssl, encoding renamed
---------------------------------

These are all now protected attributes on the Client:

.. code-block:: python

    # print(f"{client.host}:{client.port} (ssl: {client.ssl}) {client.encoding}")
    # becomes
    print(f"{client._host}:{client._port} (ssl: {client._ssl}) {client._encoding}")


Client._loop removed
--------------------

See :ref:`async Client.loop<m-client-loop>` above - this is rarely needed in modern asyncio.


Client._connection_lost removed
-------------------------------

This is now loosely coupled between Client and Protocol.  If you previously called this to trigger a disconnect,
just use :meth:`Client.disconnect<bottom.Client.disconnect>`.  If you called this from the Protocol side, instead use
``Protocol.close()``.

.. code-block:: python

    def some_fn():
        # client._connection_lost()
        # becomes
        asyncio.create_task(client.disconnect())

    async def process():
        # client._connection_lost()
        # becomes
        await client.disconnect()

    def some_fn():
        # protocol.client._connection_lost()
        # becomes
        protcol.close()

If your subclass of Client implemented this function, you can register a handler for the ``"client_disconnect"``
event, or overwrite the ``disconnect`` method.

.. code-block:: python

    V2Client(Client):
        def _connection_lost(self, protocol) -> None:
            print("saw conn lost")
            super()._connection_lost(protocol)

    # becomes

    V3Client(Client):
        def __init__(self, *a, **kw) -> None:
            super().__init__(*a, **kw)
            self.on("client_disconnect")(self._connection_lost)

        def _connection_lost(self, **kw) -> None:
            print("saw conn lost")


Client.trigger returns Task
---------------------------

Previously, :meth:`Client.trigger<bottom.Client.trigger>` didn't return anything.  You can continue to ignore the
return value from this and it will function exactly as it did.

If you want to replace code that triggered an event and then waited on another signal to know the original had been
handled, you can now just ``await`` the return value of :meth:`Client.trigger<bottom.Client.trigger>`:

.. code-block:: python

    # 2.2.0 code

    @client.on("first.event.start")
    async def process(**kw):
        print("first processing...")
        await asyncio.sleep(3, loop=client.loop)
        client.trigger("first.event.stop")

    @client.on("second.event.start")
    async def process(**kw):
        print("second processing...")
        await asyncio.sleep(3, loop=client.loop)
        client.trigger("second.event.stop")

    async def coordinate():
        client.trigger("first.event.start")
        client.trigger("second.event.start")
        await asyncio.wait([
            asyncio.create_task(client.wait("first.event.stop")),
            asyncio.create_task(client.wait("second.event.stop")),
        ])
        print("all tasks complete")

This is much simpler, and the processing functions no longer need to know who or what they need to report back on
completion.

.. code-block:: python

    # 3.0.0 code

    @client.on("first.event.start")
    async def process(**kw):
        print("processing...")
        await asyncio.sleep(3, loop=client.loop)

    @client.on("second.event.start")
    async def process(**kw):
        print("processing...")
        await asyncio.sleep(3, loop=client.loop)

    async def coordinate():
        await asyncio.wait([
            client.trigger("first.event.start"),
            client.trigger("second.event.start"),
        ])
        print("all tasks complete")


event kwargs includes ``__event__``
-----------------------------------

There is an additional arg with the name ``__event__`` passed to any handler that's registered through
:meth:`Client.on<bottom.Client.on>` and is also included in the event dict that can be awaited through
:meth:`Client.wait<bottom.Client.wait>`.  If your handlers do not include ```**kwargs`` as required, they will raise
:class:`TypeError` when they get an unexpected new keyword argument.

.. code-block:: python


    @client.on("privmsg")
    def invalid_handler(nick, target, message):
        print("I raise TypeError because I didn't include **kwargs ")

    >>> client.trigger("privmsg", nick="n", target="#chan", message="m")

    Traceback (most recent call last):
      File "<stdin>", line 5, in <module>
    TypeError: invalid_handler() got an unexpected keywork argument '__event__'

The correct signature for any event handler includes a catchall for keyword args:


.. code-block:: python

    @client.on("any-event")
    def correct_handler(some, args, you, define, **kw): ...

    # of course, keyword args doesn't have to be named kw or kwargs:
    @client.on("any-event")
    def also_correct_handler(some, args, you, define, **unexpected_keyword_arguments): ...

You can use this argument in handlers that are registered to multiple events to know which one they are handling.
Remember that events are normalized as ``event.strip().upper()``:

.. code-block:: python


    @client.on("join")
    @client.on("part")
    def channel_action(nick, channel, **kw):
        event = kw["__event__"]
        if event == "JOIN":
            print(f"{nick} joined {channel}")
        elif event == "PART":
            print(f"{nick} left {channel}")
        else:
            log.warn(f"unexpected event {event}")


.. _m-proto-encoding:

Protocol.{client, encoding} removed
-----------------------------------

Because the protocol only handles bytes, it no longer needs an ``encoding``.  This isn't a problem because the protocol
forwards incoming messages through ``Protocol.on_message`` as bytes, and sends outgoing messages through
``Protocol.write`` as bytes.

The protocol should not need to know its client anymore - if you need to send a message up through the client, use
``Protocol.on_message`` and if you need to disconnect the Protocol, use ``Protocol.close()``.


Protocol.write takes bytes
--------------------------

Since there is no longer a :ref:`Protocol.encoding<m-proto-encoding>` the protocol only handles bytes.  If you still
subclass or patch the Protocol class, you should update as follows:

.. code-block:: python

    class V2Protocol(Protocol):
        def write(self, message: str) -> None:
            print(f"outgoing {message}")
            super().write(message)

    # becomes

    class V3Protocol(Protocol):
        def write(self, message: bytes) -> None:
            print(f"outgoing {message}")
            super().write(message)


added Client.is_closing()
-------------------------

This has the same semantics as :meth:`Transport.is_closing<asyncio.BaseTransport.is_closing>` but on the
:class:`Client<bottom.Client>`. It is True when the client has never connected, or has connected and disconnected,
or is in the process of disconnecting.

This should replace any code that used to check ``if Client.protocol`` to determine if the client was connected:

.. code-block:: python

    # if client.protocol is None:
    #     print("client is disconnected")
    # becomes
    if client.is_closing():
        print("client is disconnected")


disconnect waits for ``client_disconnect``
------------------------------------------

This is a small ergonomics improvement, but may still require code changes.  Anywhere that you previously called
:meth:`Client.disconnect<bottom.Client.disconnect>` and then waited for a "client_disconnect" signal, you should now
only call disconnect.  The second wait will not trigger since the disconnect already waited:

.. code-block:: python

    async def v2_cleanup():
        # start disconnecting
        await client.disconnect()
        print("start disconnect")

        # WARN: this will block forever in v3
        await client.wait("client_disconnect")
        print("done disconnect")


    async def v3_cleanup():
        print("start disconnect")
        await client.disconnect()
        print("done disconnect")
