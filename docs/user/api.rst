.. _Public Api:

API
^^^

bottom is designed to be a small library, and structured so that you (hopefully!) feel comfortable
jumping in and reading the source if you're not sure how something works.  See the :ref:`Internals<Internal Api>`
section below for some help navigating the codebase, or the :ref:`Development<Development Setup>` section to set up the development
environment for bottom.

Public API
==========

.. autoclass:: bottom.Client
    :members: connect, disconnect, send, on, trigger, wait, send_message, message_handlers
    :special-members: __init__
    :member-order: groupwise

.. autofunction:: bottom.wait_for

.. py:data:: bottom.NextMessageHandler

    Type hint for an async function that takes a message to process.

    This is the type of the first argument in a message handler::

        from bottom import Client, ClientMessageHandler, NextMessageHandler

        class MyClient(Client):
            pass

        async def handle_message(next_handler: NextMessageHandler[MyClient], client: MyClient, message: str):
            print(f"I saw a message: {message}")
            await next_handler(client, message)

    see :attr:`message_handlers<bottom.Client.message_handlers>` for details, or :ref:`Extensions<Extensions>` for
    examples of customizing a :class:`Client<bottom.Client>`'s functionality.

.. py:data:: bottom.ClientMessageHandler

    Type hint for an async function that processes a message, and may call the next handler in the chain.

    This is the type of the entire message handler::

        from bottom import Client, ClientMessageHandler, NextMessageHandler

        class MyClient(Client):
            pass

        async def handle_message(next_handler: NextMessageHandler[MyClient], client: MyClient, message: str):
            print(f"I saw a message: {message}")
            await next_handler(client, message)

        handler: ClientMessageHandler[MyClient] = handle_message

    see :attr:`message_handlers<bottom.Client.message_handlers>` for details, or :ref:`Extensions<Extensions>` for
    examples of customizing a :class:`Client<bottom.Client>`'s functionality.


.. _Internal Api:

Internal
========

If you want to understand how something works internally, you're welcome to `open an issue`_ to discuss, or
you can review the source code.  Here are some general pointers to help with the latter:

.. _open an issue: https://github.com/numberoverzero/bottom/issues/new

Outgoing Messages
-----------------

``Client.send(**kwargs)`` -> ``Protocol.write`` outgoing messages are packed from ``**kwargs`` to a single IRC line.

#. Start at :meth:`bottom.Client.send`
#. Check out ``src/bottom/pack.py::pack_command``
#. For each command, kwargs are usually looked up in one of the helpers ``f`` or ``b``
#. The packed line is sent through ``src/bottom/core.py::Protocol.write``

Incoming Messages
-----------------

``Protocol.data_received`` -> ``Client.on(...)`` incoming messages are unpacked from an IRC line into a dict.

#. Each incoming line is passed through the :attr:`Client.message_handlers<bottom.Client.message_handlers>` list
#. This is connected to the Protocol in ``src/bottom/core.py::make_protocol_factory``
#. The chaining and implementation of ``next_handler`` is in ``src/bottom/util.py::stack_process`` which passes
   its own ``next_processor`` function into the handlers in order
#. The public :class:`Client<bottom.Client>` has a default handler at ``src/bottom/client.py::rfc2812_handler``
   which calls ``unpack_command`` to unpack a dict, then calls :meth:`Client.trigger<bottom.Client.trigger>` to
   schedule a task to invoke any handlers annotated with :meth:`Client.on<bottom.Client.on>`
#. In ``src/bottom/unpack.py::unpack_command`` the broad structure of an IRC line is split with a regex, then
   aliases are resolved (see: ``synonym``) and then kwargs is built up according to canonical command name.

Connection State
----------------
``Protocol`` manages the connection state.

#. A protocol is created in :meth:`Client.connect<bottom.Client.connect>` which makes a new ``protocol_factory``
   in ``src/bottom/core.py::make_protocol_factory``.  Note that the Protocol needs to know how to surface two things,
   and those are both defined in the factory function: (1) what to call when the connection is lost, and (2) what
   to call when a full inbound IRC line is ready.  Neither of these is defined *inside* the
   :class:`Client<bottom.Client>` -- the coupling is done inside the factory function.
#. Incoming data is chunked in ``src/bottom/core.py::Protocol.data_received`` and outgoing data passes through
   ``Protocol.write``
#. Because there are a number of ways to close a connection (remote closes, we close, connection dropped) it's
   possible for one close call at one level to pass down through the layers and then propagate back up again.
   To avoid emitting double ``"client_disconnect"`` events, the closing process needs to maintain two properties:
   (1) Any close call must clean up underlying resources, if they exist and
   (2) Any close call must not re-trigger handlers above in a higher abstraction.  This means that a lower level
   handler must cleanly handle the case that it receives a ``close()`` call while it is already closed *or closing*.
