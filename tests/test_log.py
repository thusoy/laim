import email.message
from email.mime.multipart import MIMEMultipart

import pytest

from laim.log import format_message_structure, format_context


@pytest.mark.parametrize('context,expected', [
    ({'somekey': 1}, 'somekey=1'),
    ({'somekey': 0}, 'somekey=0'),
    ({'empty': None}, 'empty='),
    ({'true': True}, 'true=true'),
    ({'false': False}, 'false=false'),
    ({'float': 1.23456789}, 'float=1.2346'),
    ({'mykey': 'my custom value'}, 'mykey="my custom value"'),
])
def test_logfmt_formatting(context, expected):
    assert format_context(context) == expected


def test_format_message_structure_plain():
    msg = email.message.Message()
    assert format_message_structure(msg) == 'text/plain'

    msg.set_type('text/html')
    assert format_message_structure(msg) == 'text/html'


def test_format_message_structure_multipart():
    msg = MIMEMultipart('alternative')
    attach1 = email.message.Message()
    attach1.set_type('text/plain')
    msg.attach(attach1)

    attach2 = email.message.Message()
    attach2.set_type('text/html')
    msg.attach(attach2)

    assert format_message_structure(msg) == 'multipart/alternative(text/plain, text/html)'


def test_format_message_structure_nested():
    msg = MIMEMultipart()
    attach1 = email.message.Message()
    attach1.set_type('text/plain')
    msg.attach(attach1)

    nested_msg = MIMEMultipart('alternative')
    nested1 = email.message.Message()
    nested1.set_type('image/jpg')
    nested_msg.attach(nested1)

    nested2 = email.message.Message()
    nested2.set_type('image/png')
    nested_msg.attach(nested2)

    msg.attach(nested_msg)

    expected = 'multipart/mixed(text/plain, multipart/alternative(image/jpg, image/png))'
    assert format_message_structure(msg) == expected
