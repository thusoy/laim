import asyncio
from queue import Queue
from unittest import mock

from laim import Laim, LaimHandler


def test_drops_privileges(temp_config):
    with mock.patch('laim.util.os') as os_mock:
        with mock.patch('pwd.getpwnam') as getpwnam_mock:
            with mock.patch('laim.Controller'):
                getpwnam_mock.return_value.pw_uid = 1337
                getpwnam_mock.return_value.pw_gid = 2448
                Laim(port=2525, config_file=temp_config)

    getpwnam_mock.assert_called_with('laim')
    os_mock.setgroups.assert_called_with([])
    os_mock.setuid.assert_called_with(1337)
    os_mock.setgid.assert_called_with(2448)


def test_loads_config(temp_config):
    with mock.patch('laim.drop_privileges'):
        with mock.patch('laim.Controller'):
            handler = Laim(config_file=temp_config)
    assert handler.config['some-secret'] == 'foo secret'


def test_full_queue():
    queue = Queue(2)
    handler = LaimHandler(queue)
    envelope = mock.MagicMock()
    envelope.rcpt_tos = ['foo']
    loop = asyncio.get_event_loop()
    run = loop.run_until_complete
    def add_to_queue():
        return run(handler.handle_DATA(None, mock.Mock(), envelope))

    add_to_queue() == '250 OK'
    add_to_queue() == '250 OK'
    add_to_queue() == '552 Exceeded storage allocation'
