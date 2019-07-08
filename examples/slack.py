import os
import socket

import requests
from laim import Laim


class SlackHandler(Laim):

    def __init__(self):
        super().__init__(
            config_file=os.path.join(os.path.dirname(__file__), 'slack.yml'),
            user=os.getlogin(),
        )
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'Bearer %s' % self.config['slack-token']
        })
        self.channel_id = self.config['slack-channel-id']
        self.hostname = socket.gethostname()


    def handle_message(self, sender, recipients, message):
        self.session.post('https://slack.com/api/chat.postMessage', json={
            'channel': self.channel_id,
            'text': '%s received mail for %s:\n%s' % (
                self.hostname, ', '.join(recipients), message.get_payload()),
        })


if __name__ == '__main__':
    handler = SlackHandler()
    handler.run()
