import os
import queue
import signal
import threading
import time
from collections import namedtuple
from email import message_from_string
from smtpd import SMTPServer

import sdnotify
import yaml
from aiosmtpd.controller import Controller

from .util import drop_privileges
from .log import log, format_message_structure


TaskArguments = namedtuple('TaskArguments', 'sender recipients data')


class Laim:

    def __init__(
            self,
            port=25,
            user='laim',
            max_queue_size=50,
            config_file='/etc/laim/config.yml',
    ):
        self.queue = queue.Queue(max_queue_size)
        self.notifier = sdnotify.SystemdNotifier()
        handler = LaimHandler(self.queue)
        self.controller = Controller(handler, hostname='127.0.0.1', port=port)

        # Start the controller while we have the privileges to bind the port
        self.controller.start()

        # Let systemd we're done binding to the network socket
        self.notifier.notify('READY=1')
        log({
            'action': 'started',
            'port': port,
            'max_queue_size': max_queue_size,
            'config_file': config_file,
        })

        with open(config_file, 'r') as config_fh:
            drop_privileges(user)
            self.config = yaml.safe_load(config_fh)

        signal.signal(signal.SIGTERM, self._signalhandler)
        signal.signal(signal.SIGINT, self._signalhandler)
        self.stop_event = threading.Event()


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
                'subject': message.get('subject'),
                'msg_defects': ','.join(e.__class__.__name__ for e in message.defects),
            }
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
