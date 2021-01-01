'''
laim to sendmail compatibility interface.
'''

import argparse
import email.parser
import logging
import os
import pwd
import smtplib
import sys
import traceback
from email.headerregistry import AddressHeader

from laim._version import __version__

# Extracted as a constant to make it easy to override for tests
SMTP_PORT = 25


_logger = logging.getLogger('laim')


def main(argv=None):
    args = parse_args(argv)
    try:
        sendmail(args)
    except Exception as ex: # pylint: disable=broad-except
        _logger.debug(traceback.format_exc())
        _logger.warning('Failed to send mail: %s', ex)
        sys.exit(1)


def mailq(prog='mailq'):
    _logger.warning('%s: Mail queue is empty (and not used by laim)', prog)


def newaliases(prog='newaliases'):
    _logger.warning('%s: Aliases are not used by laim', prog)


def sendmail(args):
    if args.bp:
        mailq('sendmail')
        return

    if args.bi:
        newaliases('sendmail')
        return

    message = read_message(args.i)
    sender = None
    recipients = args.recipients
    if 'From' not in message:
        sender = args.r or pwd.getpwuid(os.getuid()).pw_name
        if args.F:
            message['From'] = '"%s" <%s>' % (args.F, sender)
        else:
            message['From'] = sender

    if 'To' not in message and not recipients:
        raise ValueError("Message doesn't have a To header and no recipients "
            'given on the command line')

    if args.t:
        recipients.extend(extract_recipients_from_to_header(message['To']))

    send_mail(sender, unique(recipients), message)


def extract_recipients_from_to_header(to_header):
    recipients = []
    address_header = AddressHeader.value_parser(to_header)
    for address in address_header:
        if address.token_type != 'address':
            continue
        for mailbox in address.all_mailboxes:
            recipients.append(mailbox.addr_spec)
    return recipients


def unique(iterable):
    seen = set()
    ret = []
    for item in iterable:
        if not item in seen:
            ret.append(item)
            seen.add(item)
    return ret


def read_message(stop_on_dot):
    binary_lines = []
    for line in sys.stdin.buffer:
        if stop_on_dot and line == b'.\n':
            break
        binary_lines.append(line)
    parser = email.parser.BytesParser()
    message = parser.parsebytes(b''.join(binary_lines))
    return message


def send_mail(sender, recipients, message):
    with smtplib.SMTP('127.0.0.1', port=SMTP_PORT, timeout=3) as smtp:
        smtp.send_message(message, from_addr=sender, to_addrs=recipients or None)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('recipients', nargs='*')
    parser.add_argument('-bp', '-q', action='store_true',
        help='List the mail queue')
    parser.add_argument('-bi', '-I', action='store_true',
        help='Initialize the alias database. Ignored.')
    parser.add_argument('-i', '-oi', action='store_false', default=True,
        help="When reading a message from standard input, don't treat a "
        "line with only a .  character  as the end of input.")
    parser.add_argument('-F', help='Set the full name of the sender. Only '
        'used for messages without a From: header')
    parser.add_argument('-r', '-f', help='Set the envelope sender.')
    parser.add_argument('-t', action='store_true', help='Extract recipients '
        'from message headers. These are added to any recipients specified on '
        'the command line.')
    parser.add_argument('-v', action='store_true', help='More verbose logging')

    args, unparsed = parser.parse_known_args(argv)

    configure_logger(logging.DEBUG if args.v else logging.INFO)
    _logger.debug('laim version %s', __version__)

    if unparsed:
        _logger.debug('laim: ignoring the following arguments: %s',
            ' '.join(unparsed))

    return args


def configure_logger(level):
    handler = logging.StreamHandler()
    handler.setLevel(level)
    _logger.addHandler(handler)
    _logger.setLevel(level)


if __name__ == '__main__':
    main() # pragma: no cover
