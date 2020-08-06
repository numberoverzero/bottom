Development
^^^^^^^^^^^

Versioning  and RFC2812
=======================

* Bottom follows semver for its **public** API.

  * Currently, ``Client`` is the only public member of bottom.
  * IRC replies/codes which are not yet implemented may be added at any time,
    and will correspond to a patch - the function contract of ``@on`` method
    does not change.
  * You should not rely on the internal api staying the same between minor
    versions.
  * Over time, private apis may be raised to become public.  The reverse will
    never occur.

Contributing
============

Contributions welcome!  Please make sure ``tox`` passes (including flake8 and
docs build) before submitting a PR.

Pull requests that decrease coverage will not be merged.

Development
-----------
bottom uses ``tox``, ``pytest``, ``coverage``, and ``flake8``.  To get
everything set up in a new virtualenv::

    git clone https://github.com/numberoverzero/bottom.git
    cd bottom
    python3.8 -m venv --copies .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pip install -e .
    tox

Documentation
-------------

Documentation improvements are especially appreciated.  For small changes, open
a `pull request`_! If there's an area you feel is lacking and will require more
than a small change, `open an issue`_ to discuss the problem - others are
probably also confused, and may have suggestions to improve the same area.

.. _pull request: https://github.com/numberoverzero/bottom/pulls
.. _open an issue: https://github.com/numberoverzero/bottom/issues/new

TODO
====

* Better ``Client`` docstrings
* Add missing replies/errors to ``unpack.py:unpack_command``

  * Add reply/error parameters to ``unpack.py:parameters``
  * Document events, client.send
