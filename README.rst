A wrapper around the Trello API written in Python. Each Trello object is
represented by a corresponding Python object. The attributes of these objects
are cached, but the child objects are not. This can possibly be improved when
the API allows for notification subscriptions; this would allow caching
(assuming a connection was available to invalidate the cache as appropriate).

I've created a `Trello Board <https://trello.com/board/py-trello/4f145d87b2f9f15d6d027b53>`_
for feature requests, discussion and some development tracking.

Install
=======

::

    pip install py-trello

Usage
=====

.. code-block:: python

    from trello import TrelloClient

    client = TrelloClient(
        api_key='your-key',
        api_token='your-token',
    )

For new integrations, create or select a Power-Up in Trello's Power-Up Admin
Portal (https://trello.com/power-ups/admin/), then generate the API key from the
Power-Up's API Key page. Personal keys shown at https://trello.com/app-key are
legacy and should only be used as a local-testing fallback. The older
``api_secret`` argument is still accepted as a backwards-compatible alias for
``api_token`` when you are not using OAuth1.

For 3-legged OAuth1, pass the OAuth credentials explicitly:

.. code-block:: python

    client = TrelloClient(
        api_key='your-key',
        api_secret='your-api-secret',
        token='your-oauth-token-key',
        token_secret='your-oauth-token-secret'
    )

Where ``token`` and ``token_secret`` come from the 3-legged OAuth process.

Working with boards
--------------------

.. code-block:: python

    all_boards = client.list_boards()
    last_board = all_boards[-1]
    print(last_board.name)

working with board lists and cards
----------------------------------

.. code-block:: python

    all_boards = client.list_boards()
    last_board = all_boards[-1]
    last_board.list_lists()
    my_list = last_board.get_list(list_id)

    for card in my_list.list_cards():
        print(card.name)


Getting your Trello OAuth Token
===============================
Make sure the following environment variables are set:

* ``TRELLO_API_KEY``
* ``TRELLO_API_SECRET``

These are obtained from the link mentioned above.

``TRELLO_EXPIRATION`` is optional. Set it to a string such as 'never' or '1day'.
Trello's default OAuth Token expiration is 30 days.

Default permissions are read/write.

More info on generating and authorizing tokens is in Atlassian's Trello API
introduction:
https://developer.atlassian.com/cloud/trello/guides/rest-api/api-introduction/

Run

::

    python -m trello oauth

Required Python modules
=======================

Found in ``requirements.txt``

Tests
=====

To run the offline unit tests, run ``PYTHONDONTWRITEBYTECODE=1 python -m unittest test.test_api_alignment``.

To run live integration tests against Trello, follow ``docs/live-testing.rst``.
The live tests are skipped unless credentials are configured and
``TRELLO_RUN_LIVE_TESTS=1`` is set. Start from ``test/live.env.example`` and keep
real credentials in an uncommitted file such as ``.env.live``.

The live tests require these environment variables:

* ``TRELLO_RUN_LIVE_TESTS=1``: explicit opt-in for destructive live tests
* ``TRELLO_API_KEY``: your Trello API key
* ``TRELLO_TOKEN``: your Trello token

The live suite creates a private temporary board, runs the tests against it, and
deletes that board at process exit. You can set ``TRELLO_TEST_BOARD_NAME_PREFIX``
to customize the generated board name prefix. Paid-only Trello features should be
covered by unit tests or skipped unless paid credentials are available.

To run tests across various Python versions,
`tox <https://tox.readthedocs.io/en/latest/>`_ is supported. Install it
and simply run ``tox`` from the ``py-trello`` directory.
