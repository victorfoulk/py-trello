from __future__ import print_function
import unittest

from trello import TrelloClient
from trello.board import Board
from trello.card import Card
from trello.checklist import Checklist


class DummyResponse(object):
    status_code = 200
    text = 'ok'

    def __init__(self, payload=None):
        self._payload = {} if payload is None else payload

    def json(self):
        return self._payload


class RecordingHttpService(object):
    def __init__(self, payload=None):
        self.payload = payload
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return DummyResponse(self.payload)


class RecordingClient(object):
    def __init__(self, payload=None):
        self.payload = {} if payload is None else payload
        self.calls = []

    def fetch_json(self, uri_path, **kwargs):
        self.calls.append((uri_path, kwargs))
        return self.payload


class ApiAlignmentTestCase(unittest.TestCase):
    def test_key_token_auth_uses_api_token_alias_without_mutating_inputs(self):
        http = RecordingHttpService({'ok': True})
        client = TrelloClient('key', api_token='token', http_service=http)
        query_params = {'fields': 'name'}
        headers = {'X-Test': 'yes'}

        self.assertEqual(client.fetch_json('/members/me', query_params=query_params, headers=headers), {'ok': True})

        method, url, kwargs = http.calls[0]
        self.assertEqual(method, 'GET')
        self.assertEqual(url, 'https://api.trello.com/1/members/me')
        self.assertEqual(kwargs['params']['key'], 'key')
        self.assertEqual(kwargs['params']['token'], 'token')
        self.assertEqual(query_params, {'fields': 'name'})
        self.assertEqual(headers, {'X-Test': 'yes'})


    def test_client_copies_proxies_mapping(self):
        proxies = {'https': 'http://proxy.example'}
        client = TrelloClient('key', api_token='token', proxies=proxies)
        proxies['https'] = 'http://changed.example'
        self.assertEqual(client.proxies, {'https': 'http://proxy.example'})

    def test_key_token_auth_rejects_ambiguous_token_names(self):
        with self.assertRaises(ValueError):
            TrelloClient('key', api_secret='legacy-token', api_token='token')

    def test_disable_power_up_uses_documented_board_plugin_path(self):
        board = Board(client=RecordingClient(), board_id='board-id')
        board.disable_power_up('plugin-id')
        self.assertEqual(board.client.calls[0][0], 'boards/board-id/boardPlugins/plugin-id')
        self.assertEqual(board.client.calls[0][1]['http_method'], 'DELETE')

    def test_get_power_ups_sends_filter_as_query_params(self):
        board = Board(client=RecordingClient([]), board_id='board-id')
        board.get_power_ups(filters='nonsense')
        self.assertEqual(board.client.calls[0][0], '/boards/board-id/plugins')
        self.assertEqual(board.client.calls[0][1]['query_params'], {'filter': 'enabled'})
        self.assertNotIn('post_args', board.client.calls[0][1])

    def test_get_label_uses_label_endpoint(self):
        payload = {'id': 'label-id', 'name': 'Priority', 'color': 'red'}
        board = Board(client=RecordingClient(payload), board_id='board-id')
        label = board.get_label('label-id')
        self.assertEqual(board.client.calls[0][0], '/labels/label-id')
        self.assertEqual(label.name, 'Priority')

    def test_card_membership_and_comment_paths_match_spec(self):
        board = Board(client=RecordingClient(), board_id='board-id')
        card = Card(board, 'card-id', name='Card')

        card.assign('member-id')
        card.update_comment('comment-id', 'updated')

        self.assertEqual(board.client.calls[0][0], '/cards/card-id/idMembers')
        self.assertEqual(board.client.calls[0][1]['post_args'], {'value': 'member-id'})
        self.assertEqual(board.client.calls[1][0], '/cards/card-id/actions/comment-id/comments')
        self.assertEqual(board.client.calls[1][1]['post_args'], {'text': 'updated'})

    def test_card_custom_field_setter_uses_plural_cards_endpoint(self):
        board = Board(client=RecordingClient(), board_id='board-id')
        card = Card(board, 'card-id', name='Card')
        custom_field = type('CustomFieldRef', (), {'id': 'custom-field-id', 'field_type': 'text'})()

        card.set_custom_field('hello', custom_field)

        self.assertEqual(board.client.calls[0][0], '/cards/card-id/customField/custom-field-id/item')

    def test_checklist_clear_iterates_over_own_items(self):
        client = RecordingClient()
        checklist = Checklist(client, {
            'id': 'checklist-id',
            'name': 'Checklist',
            'checkItems': [
                {'id': 'one', 'name': 'one', 'state': 'incomplete', 'pos': 1},
                {'id': 'two', 'name': 'two', 'state': 'incomplete', 'pos': 2},
            ],
        })

        checklist.clear()

        self.assertEqual([call[0] for call in client.calls], [
            '/checklists/checklist-id/checkItems/one',
            '/checklists/checklist-id/checkItems/two',
        ])
        self.assertEqual(checklist.items, [])


if __name__ == '__main__':
    unittest.main()
