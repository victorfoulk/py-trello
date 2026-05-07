Live Trello Testing
===================

The default test command is safe to run without credentials::

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover

Live tests contact Trello and mutate data. They are skipped unless all live
environment variables are present and ``TRELLO_RUN_LIVE_TESTS=1`` is set.

Create Credentials
------------------

Trello now treats personal app keys as legacy. For new testing credentials, use a
Power-Up API key.

1. Sign in to the Trello account that will own the test board.
2. Open https://trello.com/power-ups/admin/.
3. Create a new app/Power-Up for this package, or select an existing one you
   control. For a new app, Trello asks for:

   * ``App name``: for example ``py-trello live tests``.
   * ``Workspace``: the Workspace that will own the app. Workspace admins and
     app collaborators can manage it.
   * ``Email``: an address Atlassian can use to contact you about the app.
   * ``Support contact``: an email or support link users can use. For private
     testing this can be the maintainer's email.
   * ``Author``: company name or personal name.
   * ``Iframe connector URL``: optional and not used by this package's REST API
     tests. Leave it blank for this live-testing setup unless you are also
     building a Trello Power-Up iframe connector.

4. Open the app's ``API key`` page and generate/copy its API key.
5. Add an allowed origin that you control if you will use redirect-based
   authorization. Do not use the deprecated ``*`` wildcard for new setups.
6. Follow the ``Token`` link on the API key page to authorize a token for the
   test account.
7. Treat the token and API secret as secrets. Do not commit them, paste them into
   issues, or share them in logs.

For quick local-only experiments, https://trello.com/app-key may still show a
legacy personal key and a manual token link. Do not use personal keys for new
repo testing or production setup when a Power-Up key is available.

Board Lifecycle
---------------

The live suite creates its own private disposable board at runtime. The board name
uses ``TRELLO_TEST_BOARD_NAME_PREFIX`` plus a random suffix, for example::

    py-trello-live-test-a1b2c3d4e5f6

At process exit, the suite permanently deletes all cards on that board, archives
any lists, and then deletes the board itself. This avoids leaving a reusable test
board full of cards and archived lists. The suite also creates/closes temporary
boards named ``test_create_board`` and ``copied_board`` while testing board
creation and copy behavior.

The current live suite is intentionally compatible with Trello's free tier. It
covers classic board, list, card, checklist, label, action, member, webhook list,
and board-star behavior. Paid-only Trello features should be covered by offline
unit tests or skipped unless paid credentials are available.

Prepare A Local Secret File
---------------------------

Copy the template and fill it in::

    cp test/live.env.example .env.live
    chmod 600 .env.live

Then edit ``.env.live`` with real values. Files named ``.env*`` are ignored by
this repository.

Required variables:

* ``TRELLO_RUN_LIVE_TESTS=1``: explicit opt-in for destructive live tests.
* ``TRELLO_API_KEY``: Trello API key from the Power-Up API key page.
* ``TRELLO_TOKEN``: Trello token authorized for the same account.

Optional variables:

* ``TRELLO_TEST_BOARD_NAME_PREFIX``: prefix for the temporary board name. Defaults
  to ``py-trello-live-test``.
* ``TRELLO_CLEANUP_LIVE_TEST_BOARD=0``: disables automatic board deletion for
  debugging.

Run The Live Suite
------------------

Load the environment and run the preflight check first::

    set -a
    . ./.env.live
    set +a
    python tools/trello_live_preflight.py

The preflight checks that Trello accepts the key/token pair. If Trello returns
``invalid key``, re-copy the API key from the Power-Up API key page; do not use
the app secret, token, or app id in ``TRELLO_API_KEY``.

Then run discovery::

    PYTHONDONTWRITEBYTECODE=1 python -m unittest discover

When live tests are enabled, the test process automatically deletes its generated
test board at exit. Before deleting the board, cleanup permanently deletes every
card returned by Trello's ``cards/all`` endpoint, including archived cards, and
archives every list. To disable automatic cleanup for debugging, set
``TRELLO_CLEANUP_LIVE_TEST_BOARD=0``.

To find and delete leftover generated boards manually, first run a dry run and then force deletion::

    python tools/trello_live_cleanup.py
    python tools/trello_live_cleanup.py --force

To run only the offline API-alignment tests::

    PYTHONDONTWRITEBYTECODE=1 python -m unittest test.test_api_alignment

After The Run
-------------

If a live run fails midway, inspect Trello manually before retrying. The automatic
cleanup should delete the generated board. Also clean up any leftover temporary
boards named ``test_create_board`` or ``copied_board`` if a run was interrupted
before those tests closed them.
