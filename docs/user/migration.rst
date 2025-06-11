.. _Migrations:

Migrating from 2.2.0 to 3.0
^^^^^^^^^^^^^^^^^^^^^^^^^^^


bottom changed substantially from 2.2.0 to 3.0 including a number of breaking changes.  below you'll find a summary of
the changes; an example of updating a small irc bot; and finally detailed sections per change.

If you encounter issues migrating, please either use the `open support issue`_ or `open an issue`_.


.. _open support issue: https://github.com/numberoverzero/bottom/issues/71
.. _open an issue: https://github.com/numberoverzero/bottom/issues/new

Summary
=======

Breaking Changes
----------------

These are approximately ordered by expected impact.

* minimum supported python version is now ``python3.12``
* ``Client.send`` is now ``async``
* ``Client.send_raw`` was renamed to ``Client.send_message`` and is now ``async``
* ``async Client.wait`` now returns the event dict, not just the event name

* ``Client.loop`` property was removed
* ``Client.handle_raw`` was removed
* ``Client.raw_handlers`` was renamed to ``Client.message_handlers``
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
* ``Protocol.client`` was removed
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

Client.raw_handlers renamed
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

Protocol.client removed
-----------------------

added Client.is_closing()
-------------------------

disconnect waits for ``client_disconnect``
------------------------------------------
