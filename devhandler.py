#!./venv/bin/python

import os
import time
from unittest import mock

from laim import Laim


def main():
    with mock.patch('os.setgroups'):
        # Prevent a call to setgroups() that requires superuser privileges
        handler = DevHandler(
            port=2525,
            user=os.getlogin(),
            max_queue_size=5,
            config_file='devconfig.yml',
            smtp_kwargs={
                'ident': 'devlaim',
                'data_size_limit': 0,
                'hostname': 'devlaim',
            },
        )
    handler.run()
    print('Exiting after handling %d messages' % handler.count)


class DevHandler(Laim):
    count = 0

    def handle_message(self, sender, recipient, message):
        print('Has secret %r, got message for %s from %s: %s' % (
            self.config['devsecret'], recipient, sender, message.get_payload()))
        time.sleep(0.2)
        self.count +=1


if __name__ == '__main__':
    main()
