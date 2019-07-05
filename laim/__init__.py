import os
import queue
import signal
import threading
from collections import namedtuple
from email import message_from_string
from smtpd import SMTPServer

import yaml
from aiosmtpd.controller import Controller

from .util import drop_privileges


TaskArguments = namedtuple('TaskArguments', 'sender receiver data')


class Laim:

    def __init__(
            self,
            port=25,
            user='laim',
            max_queue_size=50,
            config_file='/etc/laim/conf.yml',
    ):
        self.queue = queue.Queue(max_queue_size)
        handler = LaimHandler(self.queue)
        self.controller = Controller(handler, hostname='127.0.0.1', port=port)
        with open(config_file, 'r') as config_fh:
            drop_privileges(user)
            self.config = yaml.safe_load(config_fh)

        signal.signal(signal.SIGTERM, self._signalhandler)
        signal.signal(signal.SIGINT, self._signalhandler)
        self.stop_event = threading.Event()


    def handle_message(self, sender, receiver, message):
        raise NotImplementedError('The handler must implement handle_message')


    def run(self):
        worker_thread = threading.Thread(
            target=self._start_worker,
            name='Laim worker',
            daemon=False,
        )
        worker_thread.start()

        self.controller.start()
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

            message_string = task_args.data.decode('utf-8')
            message = message_from_string(message_string)
            self.handle_message(task_args.sender, task_args.receiver, message)


class LaimHandler:
    def __init__(self, queue):
        self.queue = queue


    async def handle_DATA(self, server, session, envelope):
        mail_from = envelope.mail_from
        data = envelope.content
        for receiver in envelope.rcpt_tos:
            try:
                self.queue.put_nowait(TaskArguments(mail_from, receiver, data))
            except queue.Full:
                print('Queue full, discarding message from %s to %s' % (
                    mail_from, receiver))
                return '552 Exceeded storage allocation'

        return '250 OK'
