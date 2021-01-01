import threading
import time
from unittest import mock

import pytest

from laim import Laim
from laim.__main__ import main

pytestmark = pytest.mark.integration


def test_sendmail_delivery_to_handler(temp_config):
    handled_event = threading.Event()
    lock = threading.Lock()
    received_sender = None
    received_recipients = None
    received_message = None

    class Handler(Laim):
        def handle_message(self, sender, recipients, message):
            nonlocal received_sender, received_recipients, received_message
            with lock:
                received_sender = sender
                received_recipients = recipients
                received_message = message
            handled_event.set()
            self.stop()

    with mock.patch('laim.laim.drop_privileges'):
        handler = Handler(port=2525, config_file=temp_config)

    def start_handler():
        handler.run()
    handler_thread = threading.Thread(target=start_handler)
    handler_thread.start()

    # Wait for the handler to start and bind to the port
    time.sleep(1)

    with mock.patch('laim.__main__.SMTP_PORT', 2525):
        stdin_mock = mock.Mock()
        stdin_mock.buffer = [
            b'From: foo@bar.com\r\n',
            b'To: bar@foo.com\r\n',
            b'Subject: =?utf-8?q?subject?=\r\n',
            b'\r\n',
            b'Hello, laim!\r\n',
        ]
        with mock.patch('laim.__main__.sys.stdin', stdin_mock):
            try:
                main([])
            except:
                handler.stop()
                pytest.fail()

    handled_event.wait(2)

    assert handled_event.is_set()

    with lock:
        assert received_sender == 'foo@bar.com'
        assert received_recipients == ['bar@foo.com']
        assert received_message.get_payload() == 'Hello, laim!\r\n'
        assert received_message.get('subject') == 'subject'
