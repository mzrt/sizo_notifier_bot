
import logging
from watchdog.events import LoggingEventHandler

class DataChangeHandler(LoggingEventHandler):

    def __init__(self, job, fileName):
        super().__init__()
        logging.info('__init__ run...')
        self.fileName = fileName
        self.job = job

    def on_modified(self, event):
        logging.info('on_modified 1')
        super().on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        if(what=='file' and self.fileName==event.src_path):
            self.job()