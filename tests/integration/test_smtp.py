import threading
import time
from email.message import Message
from unittest import mock
from smtplib import SMTP

import pytest

from laim import Laim

pytestmark = pytest.mark.integration


def test_smtp_delivery_to_handler():
    handled_event = threading.Event()
    lock = threading.Lock()
    received_sender = None
    received_receiver = None
    received_message = None

    class Handler(Laim):
        def handle_message(self, sender, receiver, message):
            nonlocal received_sender, received_receiver, received_message
            with lock:
                received_sender = sender
                received_receiver = receiver
                received_message = message
            handled_event.set()
            self.stop()

    with mock.patch('laim.drop_privileges'):
        handler = Handler(port=2525)

    def start_handler():
        handler.run()
    handler_thread = threading.Thread(target=start_handler)
    handler_thread.start()

    # Wait for the handler to start and bind to the port
    time.sleep(1)

    with SMTP('127.0.0.1', port=2525) as smtp:
        message = Message()
        message['From'] = 'foo@bar.com'
        message['To'] = 'bar@foo.com'
        message.set_payload('Hello, laim!')
        smtp.send_message(message)

    handled_event.wait(2)

    assert handled_event.is_set()

    with lock:
        assert received_sender == 'foo@bar.com'
        assert received_receiver == 'bar@foo.com'
        assert received_message.get_payload() == 'Hello, laim!'
