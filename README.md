# Laim (pronounced like lime, anagram of mail)

[![Build Status](https://github.com/thusoy/laim/workflows/Test/badge.svg?branch=main)](https://github.com/thusoy/laim/actions)
[![PyPI version](https://img.shields.io/pypi/v/laim.svg)](https://pypi.org/project/laim/)

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

    def handle_message(self, sender, recipients, message):
        self.session.post('https://slack.com/api/chat.postMessage', json={
            'channel': self.channel_id,
            'text': '%s received mail for %s:\n%s' % (
                self.hostname, ', '.join(recipients), message.get_payload()),
        })

if __name__ == '__main__':
    handler = SlackHandler()
    handler.run()
```

A couple of things are worth noting here that laim helped out with.


## Configuration

Laim reads the root-only readable yaml file `/etc/laim/config.yml` on startup, and saves the contents to `self.config`. This makes it easy to add arbitrary configuration you need in your handler, that will be read in a secure way.

Note that until the line calling `super().__init__()`, the script was running as root. After that it dropped privileges to the user 'laim'.


## Async

Laim is not written for high throughput, but does do some basic queuing to make sure you can handle a message synchronously without blocking the reception of other messages. This is done by running the SMTP listener on one thread, and the handler on another. Messages to be delivered are passed to the handler on a bounded in-memory queue, which prevents arbitrarily high memory usage if the handler fails to process messages fast enough by dropping new messages (this event is logged by laim). You can configure the max size of the queue by passing `max_queue_size` to the Laim constructor (default is 50).


## Security considerations

Laim will bind to localhost port 25 to handle SMTP, and will by itself not do any filtering of messages. Since it only binds to localhost there's no extra attack surface for an external attacker, but if an attacker has gotten non-root access to the server they can craft arbitrary messages that will be forwarded to your handler. This could be exploited to send trojans that might get executed by developers on their own machines or similar, thus remain skeptical to any suspicious messages that gets delivered by laim.

The service will start as root, but drops privileges once it has bound to the port and opened a handle to the config file.


# Installation

In decreasing order of stuff you have to do:

* Use the salt state [here](https://github.com/thusoy/salt-states/salt/laim), write a state that
  deploys your handler, and add any configuration to pillar. If you're using a different
  automation tool and have written a cookbook/playbook/module/thing for laim, please let me know
  and I'll add a link to it here!

* Install from my apt repo:
  ```
  $ echo "deb https://repo.thusoy.com/apt/debian $(lsb_release -cs) main" | sudo tee -a /etc/apt/sources.list
  $ curl https://raw.githubusercontent.com/thusoy/repo/main/release-key.asc | sudo apt-key add -
  $ sudo apt-get update
  $ sudo apt-get install laim
  ```
  Write your handler in `/etc/laim/handler.py`, put any configuration in `/etc/laim/config.yml` and restart the service.

* Build the debian package yourself and upload to your own repo:
  `./tools/build_deb.sh`

* Install from PyPI and deploy a handler however you prefer.


# Configuring laim

Beyond writing a handler laim doesn't require any configuration. There's a couple of knobs available though:

- **`max_queue_size`**: The max number of outstanding messages held in memory. This multiplied by the data size limit is the max memory usage of the process, if full new messages will be dropped. Default is 50.
- **`user`**: The user to drop privileges to. Defaults to `laim`, which is created upon installation of the debian package.
- **`config_file`**: Path to a YAML config file that should be read before dropping privileges. The handler can access this through `self.config`.

All the above are keyword arguments to the Laim constructor.

There's also some SMTP related configuration:
- **`data_size_limit`**: Max size of a individual message, in bytes. Default is 32MB. Set to 0 to disable the limit.
- **`ident`**: How the SMTP server identifies itself. Default is `laim <version>`.
- **`enable_SMTPUTF8`**: Whether to announce support for UTF8 in the SMTP EHLO. Default is `True`.
- **`hostname`**: The hostname the SMTP server greets clients with. Defaults to the server's FQDN.
- **`timeout`**: The number of seconds to wait between valid SMTP commands. After this time the connection will be closed by the server. The default is 300 seconds.

The above should be given in the `smtp_kwargs` argument to the Laim constructor, and are forwarded directly to the [aiosmtpd constructor](https://aiosmtpd.readthedocs.io/en/latest/aiosmtpd/docs/smtp.html#SMTP).


# Local testing

Apart from the test suite you can use the included `./devhandler.py` to run laim on port 2525 for testing. To send mail you can modify the file in `smtp-session.txt`, which can be piped to netcat to send a sample mail:

    $ nc localhost 2525 < smtp-session.txt

To send lots of mail to test the queuing system or simple load testing:

    $ count=0; while :; do echo "Sending $count"; sed s/COUNT/$count/ smtp-session.txt | nc localhost 2525 || break; count=$((count+1)); done; echo "Sent $count mails"

Laim stops gracefully on SIGINT and SIGTERM, so you can stop the handler from a third shell and observe that it shuts down cleanly after having processed all queued messages:

    $ pkill -f devhandler.py

There are some more example handlers in the [examples/](/examples/) directory.


License
-------

This project uses the [Hippocratic License](https://firstdonoharm.dev/), and is thus freely
available to use for purposes that do not infringe on the United Nations Universal Declaration of
Human Rights. Note that the python package is tagged with the MIT trove classifier until PyPI
supports a trove classifier for the
Hippocratic License (https://github.com/pypa/warehouse/issues/7157).
