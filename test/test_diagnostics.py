from __future__ import print_function
import os
import unittest

from test import live_trello
from trello.trelloclient import _redact_url


class DiagnosticTestCase(unittest.TestCase):
    def test_redact_url_hides_query_credentials(self):
        url = 'https://api.trello.com/1/members/me?key=abc&token=def&fields=username'
        self.assertEqual(
            _redact_url(url),
            'https://api.trello.com/1/members/me?key=REDACTED&token=REDACTED&fields=username'
        )

    def test_redact_url_hides_token_path_segments(self):
        url = 'https://api.trello.com/1/tokens/secret-token/webhooks?key=abc'
        self.assertEqual(
            _redact_url(url),
            'https://api.trello.com/1/tokens/REDACTED/webhooks?key=REDACTED'
        )


    def test_live_board_prefix_rejects_unsafe_values(self):
        old_value = os.environ.get('TRELLO_TEST_BOARD_NAME_PREFIX')
        try:
            os.environ['TRELLO_TEST_BOARD_NAME_PREFIX'] = 'x'
            with self.assertRaises(ValueError):
                live_trello.test_board_name_prefix()
        finally:
            if old_value is None:
                os.environ.pop('TRELLO_TEST_BOARD_NAME_PREFIX', None)
            else:
                os.environ['TRELLO_TEST_BOARD_NAME_PREFIX'] = old_value


if __name__ == '__main__':
    unittest.main()
