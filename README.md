# Laim (pronounced like lime, anagram of mail)

Flexible library to handle local SMTP on servers.

Modern &ast;nix servers use mail for a lot of reporting. Cron uses mail to notify about failing jobs, unattended-upgrades sends reports by mail, and sudo can send mail when invoked. Having a standardized way to report somewhere is great, but having to run a full-blown email infrastructure to receive these messages is hard.

Laim makes it easy to run a secure, local-only SMTP agent, where you define how messages are handled in python. Laim takes care of the hard parts of SMTP, dropping privileges and reading configuration, you just have to write the code to handle the message however you like. Post to slack? Write to log? Send text message? All three? Up to you!

Example handler that posts to slack:

```py
import socket

import requests
from laim import Laim

class SlackHandler(Laim):
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'Bearer %s' % self.config['SLACK_TOKEN']
        })
        self.channel_id = self.config['SLACK_CHANNEL_ID']
        self.hostname = socket.gethostname()

    def handle_message(self, recipient, message):
        self.session.post('https://slack.com/api/chat.postMessage', json={
            'channel': self.channel_id,
            'text': '%s received mail for %s:\n%s' % (self.hostname, recipient, message)    
        })

if __name__ == '__main__':
    handler = SlackHandler()
    handler.run()
```

A couple of things are worth noting here that laim helped out with.


## Configuration

Laim reads the root-only readable yaml file /etc/laim.conf on startup, and saves the contents to `self.config`. This makes it easy to add arbitrary configuration you need in your handler, that will be read in a secure way.

Note that until the line calling `super().__init__()`, the script was running as root. After that it dropped privileges to the user 'laim'.


## Async

Laim is not written for high throughput, but does do some basic queuing to make sure you can handle a message synchronously without blocking the reception of other messages. This is done by running the SMTP receiver on one thread, and the handler on another. Messages to be delivered are passed to the handler on a bounded in-memory queue, which prevents arbitrarily high memory usage if the handler fails to process messages fast enough by dropping new messages (this event is logged by laim).


## Security considerations

Laim will bind to localhost port 25 to handle incoming SMTP, and will by itself only filter out non-plaintext messages. This means that if an attacker gets access to the machine, they can send arbitrary messages to your handler.

The service will start as root, but drops privileges once it has bound to the port and opened a handle to the config file.
