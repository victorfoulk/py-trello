#!/usr/bin/env python3
from __future__ import print_function
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.live_trello import cleanup_test_board, live_client, test_board_name_prefix


def main():
    """Find and optionally delete leftover generated live-test boards.

    This tool intentionally defaults to a dry run because it performs permanent
    board deletion when ``--force`` is supplied. Matching is limited to the
    validated generated-board prefix from ``TRELLO_TEST_BOARD_NAME_PREFIX``.
    """
    parser = argparse.ArgumentParser(description='Delete leftover py-trello live-test boards by prefix.')
    parser.add_argument('--force', action='store_true', help='actually delete matching boards')
    args = parser.parse_args()

    client = live_client()
    prefix = test_board_name_prefix()
    matches = [board for board in client.list_boards(board_filter='all') if board.name.startswith(prefix + '-')]

    if not matches:
        print('No boards found with prefix %r.' % prefix)
        return 0

    if not args.force:
        print('Dry run. Matching boards:')
        for board in matches:
            print('  %s (%s)' % (board.name, board.id))
        print('Run again with --force to delete these boards.')
        return 1

    for board in matches:
        result = cleanup_test_board(client=client, board=board, delete_board=True)
        print('Deleted {board_name}: {cards_deleted} cards, {lists_archived} lists archived, board_deleted={board_deleted}'.format(**result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
