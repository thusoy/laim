import email.parser
import textwrap
from unittest import mock

from laim.__main__ import read_message, main

def test_read_message():
    sys_mock = mock.Mock()
    sys_mock.stdin.buffer = [
        b'From: foo\n',
        b'\n',
        b'Foo content\n',
        b'.\n',
        b'Should be ignored\n',
    ]
    with mock.patch('laim.__main__.sys', sys_mock):
        message = read_message('8BITMIME', stop_on_dot=True)

    assert message.get_payload() == 'Foo content\n'


def test_read_message_ignore_dot():
    sys_mock = mock.Mock()
    sys_mock.stdin.buffer = [
        b'From: foo\n',
        b'\n',
        b'Foo content\n',
        b'.\n',
        b'Should be included\n',
    ]
    with mock.patch('laim.__main__.sys', sys_mock):
        message = read_message('8BITMIME', stop_on_dot=False)

    assert message.get_payload() == 'Foo content\n.\nShould be included\n'


def test_message_parsing():
    sys_mock = mock.Mock()
    sys_mock.stdin.buffer = [
        b'From: foo\n',
        b'To: bar\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys', sys_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main([])

    assert_send_mail_called(send_mail_mock, None, None, textwrap.dedent('''\
        From: foo\r
        To: bar\r
        \r
        Message\r
    '''))


def assert_send_mail_called(send_mail_mock, sender, recipients, message_string):
    send_mail_mock.assert_called_with(sender, recipients, mock.ANY)
    sent_message = send_mail_mock.call_args[0][2]
    assert sent_message.as_string() == message_string
