from __future__ import print_function
import atexit
import os
import sys
import unittest
import uuid

from trello import TrelloClient

LIVE_TRELLO_ENV_VARS = (
    'TRELLO_RUN_LIVE_TESTS',
    'TRELLO_API_KEY',
    'TRELLO_TOKEN',
)
DEFAULT_TEST_BOARD_NAME_PREFIX = 'py-trello-live-test'
MIN_TEST_BOARD_NAME_PREFIX_LENGTH = 8

_TEST_BOARD = None
_TEST_BOARD_CREATED = False


def live_env_ready():
    """Return True when live Trello tests are explicitly and safely enabled.

    The live suite mutates Trello data, so it requires an opt-in flag as well as
    non-placeholder credentials. This avoids accidentally running destructive
    tests in a developer shell that merely happens to contain partial Trello
    environment variables.
    """
    return (
        os.environ.get('TRELLO_RUN_LIVE_TESTS') == '1'
        and all(
            os.environ.get(name)
            and not os.environ.get(name).startswith('replace-with-')
            for name in LIVE_TRELLO_ENV_VARS
        )
    )


requires_live_trello = unittest.skipUnless(
    live_env_ready(),
    'live Trello tests require TRELLO_RUN_LIVE_TESTS=1 and non-placeholder API credentials',
)


def live_client():
    """Build a TrelloClient from the live-test environment."""
    return TrelloClient(os.environ['TRELLO_API_KEY'], api_token=os.environ['TRELLO_TOKEN'])


def test_board_name_prefix():
    """Return the validated prefix used for generated live-test boards.

    The manual cleanup tool deletes boards by this prefix, so the value must be
    specific enough to avoid broad accidental matches.
    """
    prefix = os.environ.get('TRELLO_TEST_BOARD_NAME_PREFIX', DEFAULT_TEST_BOARD_NAME_PREFIX).strip()
    if prefix.startswith('replace-with-') or len(prefix) < MIN_TEST_BOARD_NAME_PREFIX_LENGTH:
        raise ValueError(
            'TRELLO_TEST_BOARD_NAME_PREFIX must be at least %d characters and must not be a placeholder'
            % MIN_TEST_BOARD_NAME_PREFIX_LENGTH
        )
    return prefix


def _new_test_board_name():
    """Return a collision-resistant board name for one live test process."""
    return '%s-%s' % (test_board_name_prefix(), uuid.uuid4().hex[:12])


def get_test_board(client=None):
    """Create or return the private board shared by this live test process.

    A single generated board keeps live tests isolated from user data while still
    allowing tests to share state where the original integration suite depends on
    ordering. The board is deleted by the atexit cleanup hook unless cleanup is
    disabled for debugging.
    """
    global _TEST_BOARD, _TEST_BOARD_CREATED
    client = client or live_client()
    if _TEST_BOARD is None:
        _TEST_BOARD = client.add_board(
            _new_test_board_name(),
            permission_level='private',
            default_lists=False,
        )
        _TEST_BOARD_CREATED = True
    return _TEST_BOARD


def cleanup_test_board(client=None, board=None, delete_board=True):
    """Remove all test artifacts from ``board`` and optionally delete the board.

    Trello's REST API cannot permanently delete lists directly. Cleanup first
    permanently deletes every card returned by ``/cards/all`` (including archived
    cards), then archives every list, then deletes the generated board. Deleting
    the board is the real clean-state operation; archiving lists first makes the
    cleanup idempotent and useful when ``delete_board`` is disabled for debugging.
    """
    client = client or live_client()
    board = board or get_test_board(client)

    cards_deleted = 0
    for card_json in client.fetch_json('/boards/' + board.id + '/cards/all'):
        client.fetch_json('/cards/' + card_json['id'], http_method='DELETE')
        cards_deleted += 1

    lists_archived = 0
    for list_json in client.fetch_json('/boards/' + board.id + '/lists', query_params={'filter': 'all'}):
        if not list_json.get('closed'):
            client.fetch_json(
                '/lists/' + list_json['id'] + '/closed',
                http_method='PUT',
                post_args={'value': 'true'},
            )
            lists_archived += 1

    board_deleted = False
    if delete_board:
        client.fetch_json('/boards/' + board.id, http_method='DELETE')
        board_deleted = True

    return {
        'board_name': board.name,
        'cards_deleted': cards_deleted,
        'lists_archived': lists_archived,
        'board_deleted': board_deleted,
    }


def _cleanup_at_exit():
    """Best-effort cleanup hook for the generated live-test board."""
    if os.environ.get('TRELLO_CLEANUP_LIVE_TEST_BOARD', '1') == '0':
        return
    if not _TEST_BOARD_CREATED or _TEST_BOARD is None:
        return
    try:
        result = cleanup_test_board(board=_TEST_BOARD, delete_board=True)
        print(
            'Cleaned Trello test board {board_name!r}: deleted {cards_deleted} cards, archived {lists_archived} lists, board_deleted={board_deleted}'.format(**result),
            file=sys.stderr,
        )
    except Exception as exc:
        print('Failed to clean Trello test board: %s' % exc, file=sys.stderr)


if live_env_ready():
    atexit.register(_cleanup_at_exit)
