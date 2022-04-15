import platform
import queue
import signal
import threading
import time
from collections import namedtuple
from email import message_from_string
from email.header import decode_header, make_header

import sdnotify
import setproctitle
import yaml
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP

from .util import drop_privileges, unfold
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
        setproctitle.setproctitle('laim')
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
        }, sender=self)

        with open(config_file, 'r') as config_fh:
            drop_privileges(user)
            self.config = yaml.safe_load(config_fh)

        self.stop_event = threading.Event()
        signal.signal(signal.SIGTERM, self._signalhandler)
        signal.signal(signal.SIGINT, self._signalhandler)

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
        self.queue.put(None)
        self.stop_event.set()


    def _signalhandler(self, signum, frame): # pylint: disable=unused-argument
        self.stop()


    def _start_worker(self):
        while True:
            task_args = self.queue.get()
            if task_args is None:
                break

            start_time = time.time()
            message_string = task_args.data.decode('utf-8')
            message = message_from_string(message_string)
            raw_subject = message.get('subject')

            # Decode the subject to make it easier to consume for handlers
            decoded_subject = None
            if raw_subject:
                decoded_subject = str(make_header(decode_header(raw_subject)))
                message.replace_header('subject', decoded_subject)

            log_data = {
                'action': 'handle-message',
                'parse_time': '%.3fs' % (time.time() - start_time),
                'sender': task_args.sender,
                'recipients': ','.join(task_args.recipients),
                'msg_structure': format_message_structure(message),
                'raw_subject': unfold(raw_subject),
                'decoded_subject': decoded_subject,
                'msg_defects': ','.join(e.__class__.__name__ for e in message.defects),
            }

            try:
                handler_data = self.handle_message(task_args.sender, task_args.recipients, message)
                if handler_data:
                    log_data.update(handler_data)
            except Exception as ex: # pylint: disable=broad-except
                log_data['action'] = 'handle-message-error'
                log_data['error'] = ex.__class__.__name__
                log_data['error_msg'] = str(ex)
            finally:
                log(log_data, start_time, sender=self)


class LaimHandler:
    def __init__(self, task_queue):
        self.task_queue = task_queue


    async def handle_DATA(self, server, session, envelope): # pylint: disable=invalid-name,unused-argument
        start_time = time.time()
        mail_from = envelope.mail_from
        data = envelope.content
        recipients = envelope.rcpt_tos
        log_data = {
            'action': 'queued-message',
            'mail_from': mail_from,
            'recipients': ','.join(recipients),
            'msg_size': len(data),
            'client': session.host_name,
        }
        try:
            self.task_queue.put_nowait(TaskArguments(mail_from, recipients, data))
            log(log_data, start_time, sender=self)
        except queue.Full:
            log_data['action'] = 'queue-full'
            log(log_data, start_time, sender=self)
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
