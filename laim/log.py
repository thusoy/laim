import numbers
import re
import threading
import time

from blinker import signal

from ._version import __version__

STDOUT_LOCK = threading.Lock()
NEEDS_QUOTES_RE = re.compile(r'[\s=]')

before_log = signal('before-log')


def log(context, start_time=None, sender=None):
    context['version'] = __version__

    if start_time is not None:
        context['duration_ms'] = (time.time() - start_time)*1000

    before_log.send(sender, log_data=context)
    message = format_context(context)

    with STDOUT_LOCK:
        print(message)


def format_context(context):
    return ' '.join(
        format_key_value_pair(key, val) for (key, val) in context.items()
    )


def format_key_value_pair(key, value):
    if value is None:
        value = ''
    elif value is True:
        value = 'true'
    elif value is False:
        value = 'false'
    elif isinstance(value, numbers.Integral):
        value = str(value)
    elif isinstance(value, numbers.Real):
        value = '%.4f' % value
    else:
        value = str(value)

    should_quote = NEEDS_QUOTES_RE.search(value)

    if should_quote:
        value = '"%s"' % value

    return '%s=%s' % (key, value)


def format_message_structure(message):
    if not message.is_multipart():
        return message.get_content_type()

    ret = []
    ret.append(message.get_content_type())
    ret.append('(')

    first = True
    for part in message.get_payload():
        if not first:
            ret.append(', ')
        ret.append(format_message_structure(part))
        first = False

    ret.append(')')

    return ''.join(ret)
