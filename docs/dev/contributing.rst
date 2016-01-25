Contributing
============

Contributions welcome!  Please make sure ``tox`` passes (including flake8 and
docs build) before submitting a PR.

Pull requests that decrease coverage will not be merged.

Development
-----------
bottom uses ``tox``, ``pytest``, ``coverage``, and ``flake8``.  To get
everything set up with pyenv_:

.. code-block:: python

    git clone https://github.com/numberoverzero/bottom.git
    cd bottom
    pyenv virtualenv 3.5.1 bottom
    python setup.py develop
    tox

Documentation
-------------

Documentation improvements are especially appreciated.  For small changes, open
a `pull request`_! If there's an area you feel is lacking and will require more
than a small change, `open an issue`_ to discuss the problem - others are
probably also confused, and may have suggestions to improve the same area.

.. _pyenv: https://github.com/yyuu/pyenv
.. _pull request: https://github.com/numberoverzero/bottom/pulls
.. _open an issue: https://github.com/numberoverzero/bottom/issues/new
