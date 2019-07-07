'''
laim to sendmail compatibility interface.
'''

import argparse
import email.parser
import sys
from email.policy import SMTPUTF8, SMTP


def main(argv=None):
    args = parse_args(argv)
    sendmail(args)


def mailq(prog='mailq'):
    sys.stderr.write('%s: Mail queue is empty (and not used by laim)\n' % prog)


def newaliases(prog='newaliases'):
    sys.stderr.write('%s: Aliases are not used by laim\n' % prog)


def sendmail(args):
    if args.bp:
        return mailq('sendmail')
    if args.bi:
        return newaliases('sendmail')
    message = read_message(args.B, args.i)
    send_mail(None, None, message)


def read_message(body_type, stop_on_dot):
    binary_lines = []
    for line in sys.stdin.buffer:
        if stop_on_dot and line == b'.\n':
            break
        binary_lines.append(line)
    parser_policy = SMTPUTF8 if body_type == '8BITMIME' else SMTP
    parser = email.parser.BytesParser(policy=parser_policy)
    message = parser.parsebytes(b''.join(binary_lines))
    return message


def send_mail(sender, recipients, message):
    with SMTP('127.0.0.1', port=25, timeout=3) as smtp:
        smtp.send_message(message, from_addr=sender, to_addrs=recipients)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument('recipients', nargs='*')
    parser.add_argument('-bp', '-q', action='store_true',
        help='List the mail queue')
    parser.add_argument('-bi', '-I', action='store_true',
        help='Initialize the alias database. Ignored.')
    parser.add_argument('-B', choices=('7BIT', '8BITMIME'),
        help='Set the message body type')
    parser.add_argument('-i', '-oi', action='store_false', default=True,
        help="When reading a message from standard input, don't treat a "
        "line with only a .  character  as the end of input.")

    args, unparsed = parser.parse_known_args(argv)
    if unparsed:
        sys.stderr.write('ignoring the following arguments: %s\n' %
            ' '.join(unparsed))
    return args


if __name__ == '__main__':
    main()
