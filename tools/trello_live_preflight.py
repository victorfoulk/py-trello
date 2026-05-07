#!/usr/bin/env python3
from __future__ import print_function
import os
import sys

import requests

REQUIRED = (
    'TRELLO_API_KEY',
    'TRELLO_TOKEN',
)


def _state(name):
    """Return a non-secret readiness label for one environment variable."""
    value = os.environ.get(name, '')
    if not value:
        return 'missing'
    if value.startswith('replace-with-'):
        return 'placeholder'
    return 'set'


def main():
    """Validate live Trello credentials without printing secret values."""
    bad = [name for name in REQUIRED if _state(name) != 'set']
    if bad:
        for name in REQUIRED:
            print('%s: %s' % (name, _state(name)))
        print('Missing or placeholder live Trello values: %s' % ', '.join(bad), file=sys.stderr)
        return 2

    params = {
        'key': os.environ['TRELLO_API_KEY'],
        'token': os.environ['TRELLO_TOKEN'],
        'fields': 'username',
    }
    response = requests.get('https://api.trello.com/1/members/me', params=params, timeout=20)
    if response.status_code != 200:
        print('Credential preflight failed: HTTP %s %s' % (response.status_code, response.text[:120]), file=sys.stderr)
        if response.text.strip() == 'invalid key':
            print('Trello rejected TRELLO_API_KEY. Re-copy the API key from the Power-Up API key page, not the app secret, token, or app id.', file=sys.stderr)
        return 1

    username = response.json().get('username')
    prefix = os.environ.get('TRELLO_TEST_BOARD_NAME_PREFIX', 'py-trello-live-test')
    print('Credential preflight OK for Trello user: %s' % username)
    print('Live tests will create and delete a private board named like: %s-<random>' % prefix)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
