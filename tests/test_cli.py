import email.parser
import email.policy
import os
import pwd
import textwrap
from unittest import mock

import pytest

from laim.__main__ import read_message, main, extract_recipients_from_to_header

def test_read_message():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'From: foo\n',
        b'\n',
        b'Foo content\n',
        b'.\n',
        b'Should be ignored\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        message = read_message(stop_on_dot=True)

    assert message.get_payload() == 'Foo content\n'


def test_read_message_ignore_dot():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'From: foo\n',
        b'\n',
        b'Foo content\n',
        b'.\n',
        b'Should be included\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        message = read_message(stop_on_dot=False)

    assert message.get_payload() == 'Foo content\n.\nShould be included\n'


def test_message_parsing():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'From: foo\n',
        b'To: bar\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main([])

    assert_send_mail_called(send_mail_mock, None, [], textwrap.dedent('''\
        From: foo\r
        To: bar\r
        \r
        Message\r
    '''))


def test_message_without_from_and_with_F_argument():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'To: bar\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main(['-F', 'foo name'])

    current_user = pwd.getpwuid(os.getuid()).pw_name
    assert_send_mail_called(send_mail_mock, current_user, None, textwrap.dedent('''\
        To: bar\r
        From: "foo name" <%s>\r
        \r
        Message\r
    ''' % current_user))


def test_message_without_from_and_with_F_argument():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'To: bar\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main(['-F', 'foo name'])

    current_user = pwd.getpwuid(os.getuid()).pw_name
    assert_send_mail_called(send_mail_mock, current_user, [], textwrap.dedent('''\
        To: bar\r
        From: "foo name" <%s>\r
        \r
        Message\r
    ''' % current_user))


def test_message_without_to():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'Subject: test subject\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            with pytest.raises(SystemExit):
                main([])


def test_message_without_to_but_with_recipients():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'Subject: test subject\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main(['foo'])

    current_user = pwd.getpwuid(os.getuid()).pw_name
    assert_send_mail_called(send_mail_mock, current_user, ['foo'], textwrap.dedent('''\
        Subject: test subject\r
        From: %s\r
        \r
        Message\r
    ''' % current_user))


@pytest.mark.parametrize('flag', ('-r', '-f'))
def test_message_without_from_and_with_sender_argument(flag):
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'To: bar\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main([flag, 'foo'])

    assert_send_mail_called(send_mail_mock, 'foo', [], textwrap.dedent('''\
        To: bar\r
        From: foo\r
        \r
        Message\r
    '''))


def test_message_extract_recipient():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'From: foo\n',
        b'To: bar, foo\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main(['-t', 'baz', 'foo'])

    assert_send_mail_called(send_mail_mock, None, ['baz', 'foo', 'bar'], textwrap.dedent('''\
        From: foo\r
        To: bar, foo\r
        \r
        Message\r
    '''))


def test_quoted_printable_long_subject():
    stdin_mock = mock.Mock()
    stdin_mock.buffer = [
        b'Subject: =?utf-8?q?mail_with_long_long_long_long_long_long_long_long_long_long_long_s?=\n',
        b' =?utf-8?q?ubject?=\n',
        b'To: foo\n',
        b'\n',
        b'Message\n',
    ]
    with mock.patch('laim.__main__.sys.stdin', stdin_mock):
        with mock.patch('laim.__main__.send_mail') as send_mail_mock:
            main([])

    current_user = pwd.getpwuid(os.getuid()).pw_name
    assert_send_mail_called(send_mail_mock, current_user, [], textwrap.dedent('''\
        Subject: =?utf-8?q?mail_with_long_long_long_long_long_long_long_long_long_long_long_s?=\r
         =?utf-8?q?ubject?=\r
        To: foo\r
        From: %s\r
        \r
        Message\r
    ''' % current_user))


def assert_send_mail_called(send_mail_mock, sender, recipients, message_string):
    send_mail_mock.assert_called_with(sender, recipients, mock.ANY)
    sent_message = send_mail_mock.call_args[0][2]
    assert sent_message.as_string(policy=email.policy.SMTP) == message_string


@pytest.mark.parametrize('test_case', [
    ('foo', ['foo']),
    ('<foo>', ['foo']),
    ('"Foo Name" <foo@bar.com>, bar, Baz <bzz@baz.org>', ['foo@bar.com', 'bar', 'bzz@baz.org'])
])
def test_extract_recipients_from_to_header(test_case):
    to_header, expected = test_case
    actual = extract_recipients_from_to_header(to_header)
    assert actual == expected
