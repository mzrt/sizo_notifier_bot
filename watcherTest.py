import os
from dotenv import dotenv_values
import json
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, LoggingEventHandler

devMode = 'app' in os.environ and os.environ['app']=="dev"
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **(dotenv_values(".env.development.local") if devMode else {}),
    **os.environ,  # override loaded values with environment variables
}
dataFileName = config['DATA_JSON_FILENAME']

class TestDataChangeHandler(LoggingEventHandler):

    def __init__(self, job):
        super().__init__()
        logging.info('__init__ run...')
        self.job = job

    def on_modified(self, event):
        logging.info('on_modified 1')
        super().on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        if(what=='file'):
            self.job()

def testJob():
    logging.info('Run job')

if __name__ == "__main__":
    
    if not os.path.isfile(dataFileName):
        with open(dataFileName, 'w') as output_file:
            json.dump({}, output_file, ensure_ascii=False, indent=4)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logging.info(f'monitoring {dataFileName} start ...')
    event_handler = TestDataChangeHandler(testJob)
    event_handler2 = LoggingEventHandler()
    observer = Observer()
    observer.schedule(event_handler, '.', recursive=True)
    observer.schedule(event_handler2, '.', recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()