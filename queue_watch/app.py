import time
import re
import os
import requests
import configparser
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

config = configparser.ConfigParser()
config.read('config.ini')

ENDPOINT = config.get('dialer', 'endpoint')

log_file_path = "/var/log/asterisk/queue_log"

class QueueLogHandler(FileSystemEventHandler):
    last_position = 0
    last_inode = None

    def on_modified(self, event):
        if event.src_path == log_file_path:
            self.process_log()

    def process_log(self):
        try:
            current_inode = os.stat(log_file_path).st_ino

            if self.last_inode != current_inode:
                self.last_position = 0
                self.last_inode = current_inode

            with open(log_file_path, "r") as file:
                file.seek(self.last_position)
                lines = file.readlines()
                self.last_position = file.tell()

            for line in lines:
                parts = line.strip().split("|")
                if len(parts) < 5:
                    continue

                timestamp = int(parts[0])
                interface = parts[1] if parts[1] != "NONE" else None
                queue = parts[2] if parts[2] != "NONE" else None
                member = parts[3] if parts[3] != "NONE" else None
                event_type = parts[4]

                if not member or not queue or not event_type:
                    continue

                if event_type not in ["ADDMEMBER", "UNPAUSE", "UNPAUSEALL", "REMOVEMEMBER"]:
                    continue

                status = "removed" if event_type in ["REMOVEMEMBER"] else "added"

                # Получаем внутренний номер
                if "from-queue" in member:
                    match = re.search(r'Local/(\d+)@from-queue/n', member)
                    internal_number = match.group(1) if match else member
                else:
                    internal_number = member

                self.update_queue_status(internal_number, queue, status)

        except Exception as e:
            print(f"Ошибка при обработке файла: {e}")

    def update_queue_status(self, internal_number, queue, status):
        data = {
            "internal_number": internal_number,
            "queue": queue,
            "status": status
        }
        try:
            response = requests.post(ENDPOINT, json=data)
            if response.status_code == 200:
                print(f"Успешно отправлено: {data}")
            else:
                print(f"Ошибка при отправке данных: {response.status_code}")
        except requests.RequestException as e:
            print(f"Ошибка подключения к API: {e}")

if __name__ == "__main__":
    event_handler = QueueLogHandler()
    observer = Observer()
    observer.schedule(event_handler, path="/var/log/asterisk/", recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()