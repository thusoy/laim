from unittest import mock

from laim import Laim


def test_drops_privileges():
    with mock.patch('laim.os') as os_mock:
        with mock.patch('pwd.getpwnam') as getpwnam_mock:
            getpwnam_mock.return_value.pw_uid = 1337
            getpwnam_mock.return_value.pw_gid = 2448
            Laim(port=2525)

    getpwnam_mock.assert_called_with('laim')
    os_mock.setgroups.assert_called_with([])
    os_mock.setuid.assert_called_with(1337)
    os_mock.setgid.assert_called_with(2448)
