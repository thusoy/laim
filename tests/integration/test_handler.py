from unittest import mock

import pytest

from laim import Laim, TaskArguments

pytestmark = pytest.mark.integration


def test_handler(temp_config):
    class Handler(Laim):
        def handle_message(self, sender, recipients, message):
            self.stop_event.set()

    with mock.patch('laim.drop_privileges'):
        with mock.patch('laim.Controller'):
            handler = Handler(config_file=temp_config)

    handler.queue.put(TaskArguments(mock.Mock(), [], b''))
    handler._start_worker()

    assert handler.stop_event.is_set()


def test_crashing_handler(temp_config):
    class Handler(Laim):
        def handle_message(self, sender, recipients, message):
            self.stop_event.set()
            raise ValueError()

    with mock.patch('laim.drop_privileges'):
        with mock.patch('laim.Controller'):
            handler = Handler(config_file=temp_config)

    handler.queue.put(TaskArguments(mock.Mock(), [], b''))
    handler._start_worker()

    # the worker thread shouldn't crash
    assert handler.stop_event.is_set()
