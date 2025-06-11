.. _Development:

Development
^^^^^^^^^^^

Versioning  and RFC2812
=======================

Bottom follows semver for its public API.

* only the :ref:`documented Public API<Public Api>` is subject to versioning.
  anything not documented there may change at any time.
* new IRC replies/codes may be added in patch versions.
* internal classes and methods may be promoted to public methods in minor versions.

Contributing
============

Contributions welcome!  Please run ``make pr-check`` locally before submitting a PR.

If you'd like to contribute but aren't sure where to start, consider looking through the `open issues`_!

Some pointers are :ref:`available here<Internal Api>` to help you start navigating the codebase.

.. _Development Setup:

Development
-----------
bottom uses ``ruff`` and ``pytest``.  To get started:

.. code-block:: console

    $ git clone https://github.com/numberoverzero/bottom.git
    $ cd bottom
    $ make dev
    # ... make some changes
    $ make pr-check

Documentation
-------------

Documentation improvements are especially appreciated.  For small changes, open
a `pull request`_! If there's an area you feel is lacking and will require more
than a small change, `open an issue`_ to discuss the problem - others are
probably also confused, and may have suggestions to improve the same area.

.. _open issues: https://github.com/numberoverzero/bottom/issues
.. _pull request: https://github.com/numberoverzero/bottom/pulls
.. _open an issue: https://github.com/numberoverzero/bottom/issues/new
