#!/usr/bin/python3
""" Watch pipeline incoming directory and start processing when a new file arrives """

import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

def on_created(event):
    """ Function to handle new file creating event """
    print(f'{event.src_path} has been created.')
    file_size = -1
    while file_size != os.path.getsize(event.src_path):
        file_size = os.path.getsize(event.src_path)
        time.sleep(1)

    subprocess.run(['/usr/bin/python3', './process_video.py', event.src_path], stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, check=True)

def main():
    """ Main driver for file monitor utility """
    patterns = '*.ts'
    ignore_patterns = ''
    ignore_directories = True
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns,
                                                   ignore_directories, case_sensitive)
    my_event_handler.on_created = on_created

    path = './incoming'
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('Monitoring terminated.')
        my_observer.stop()
        my_observer.join()

if __name__ == '__main__':
    main()
