import os
import platform
import queue
import re
import signal
import threading
import time
from collections import namedtuple
from email import message_from_string
from email.header import decode_header, make_header
from smtpd import SMTPServer

import sdnotify
import yaml
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP

from .util import drop_privileges
from .log import log, format_message_structure
from ._version import __version__


TaskArguments = namedtuple('TaskArguments', 'sender recipients data')


class Laim:

    def __init__(
            self,
            port=25,
            user='laim',
            max_queue_size=50,
            config_file='/etc/laim/config.yml',
            smtp_kwargs=None,
    ):
        self.queue = queue.Queue(max_queue_size)
        self.notifier = sdnotify.SystemdNotifier()
        handler = LaimHandler(self.queue)
        privilege_event = threading.Event()
        self.controller = LaimController(
            privilege_event,
            handler,
            port=port,
            smtp_kwargs=smtp_kwargs,
        )

        # Start the controller while we have the privileges to bind the port
        self.controller.start()

        # Let systemd we're done binding to the network socket
        self.notifier.notify('READY=1')
        log({
            'action': 'started',
            'port': port,
            'max_queue_size': max_queue_size,
            'config_file': config_file,
            'py': platform.python_version(),
        })

        with open(config_file, 'r') as config_fh:
            drop_privileges(user)
            self.config = yaml.safe_load(config_fh)

        signal.signal(signal.SIGTERM, self._signalhandler)
        signal.signal(signal.SIGINT, self._signalhandler)
        self.stop_event = threading.Event()

        # Allow client sessions to be created
        privilege_event.set()


    def handle_message(self, sender, recipients, message):
        raise NotImplementedError('The handler must implement handle_message')


    def run(self):
        worker_thread = threading.Thread(
            target=self._start_worker,
            name='Laim worker',
            daemon=False,
        )
        worker_thread.start()

        self.stop_event.wait()
        self.controller.stop()


    def stop(self):
        self.stop_event.set()


    def _signalhandler(self, signum, frame):
        self.stop()


    def _start_worker(self):
        while True:
            try:
                task_args = self.queue.get(block=True, timeout=1)
            except queue.Empty:
                if self.stop_event.is_set():
                    break
                continue

            start_time = time.time()
            message_string = task_args.data.decode('utf-8')
            message = message_from_string(message_string)
            log_context = {
                'action': 'handle-message',
                'parse_time': '%.3fs' % (time.time() - start_time),
                'sender': task_args.sender,
                'recipients': ','.join(task_args.recipients),
                'msg_structure': format_message_structure(message),
                'subject': unfold(message.get('subject')),
                'msg_defects': ','.join(e.__class__.__name__ for e in message.defects),
            }

            # Decode the subject to make it easier to consume for handlers
            if 'subject' in message:
                message.replace_header('subject', str(make_header(decode_header(message['subject']))))

            try:
                self.handle_message(task_args.sender, task_args.recipients, message)
            except Exception as e:
                log_context['action'] = 'handle-message-error'
                log_context['error'] = e
            finally:
                log(log_context, start_time)


class LaimHandler:
    def __init__(self, queue):
        self.queue = queue


    async def handle_DATA(self, server, session, envelope):
        start_time = time.time()
        mail_from = envelope.mail_from
        data = envelope.content
        recipients = envelope.rcpt_tos
        log_context = {
            'action': 'queued-message',
            'mail_from': mail_from,
            'recipients': ','.join(recipients),
            'msg_size': len(data),
            'client': session.host_name,
        }
        try:
            self.queue.put_nowait(TaskArguments(mail_from, recipients, data))
            log(log_context, start_time)
        except queue.Full:
            log_context['action'] = 'queue-full'
            log(log_context, start_time)
            return '552 Exceeded storage allocation'

        return '250 OK'


class LaimController(Controller):
    def __init__(self, privilege_event, handler, port, smtp_kwargs=None):
        super().__init__(handler, hostname='localhost', port=port)
        self.smtp_kwargs = smtp_kwargs
        self.privilege_event = privilege_event


    def factory(self):
        kwargs = {
            'enable_SMTPUTF8': True,
            'ident': 'laim %s' % __version__,
        }
        if self.smtp_kwargs:
            kwargs.update(self.smtp_kwargs)

        return LaimSMTP(self.privilege_event, self.handler, **kwargs)


class LaimSMTP(SMTP):
    '''
    Subclass to make sure no sessions are created before we've dropped
    privileges.
    '''
    def __init__(self, privilege_event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.privilege_event = privilege_event


    def _create_session(self):
        self.privilege_event.wait()
        return super()._create_session()


def unfold(folded):
    '''Helper to unfold headers'''
    if folded is None:
        return None
    return re.sub(r'\r?\n ', ' ', folded)
