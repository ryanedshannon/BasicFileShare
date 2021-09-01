import socket
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

sending = False
receiving = False

# Connects two machines over a local area network
class Watcher:
    # Directory where new files are changed
    DIRECTORY_TO_WATCH = ""

    def __init__(self):
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        while True:
            time.sleep(5)
        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        print(event)
        global sending
        global receiving
        print("Sending: ", sending)
        print("Receiving: ", receiving)
        if event.is_directory:
            return None
        elif sending is False and receiving is False:
            file = event.src_path.split('\\')[1].split('~')[0]
            if event.event_type == 'moved':
                dest_file = event.dest_path.split('\\')[1].split('~')[0]
                send(file, True)
                send(dest_file, False)
            elif event.event_type == 'modified' or event.event_type == 'created':
                send(file, False)
            elif event.event_type == 'deleted':
                send(file, True)


def send(filename, deleting):
    global sending
    sending = True
    # Client IP
    client = ''
    port = 5000

    s = socket.socket()
    s.connect((client, port))

    s.send(filename.encode())
    s.recv(1024).decode()
    s.send(str(deleting).encode())
    if deleting:
        print("Sent delete order for ", filename)
        time.sleep(1)
        sending = False
        return
    s.recv(1024)
    s.send(str(os.path.getsize(filename)).encode())
    s.recv(1024).decode()
    with open(filename, 'rb') as f:
        packet = f.read(1024)
        s.send(packet)
        while packet.decode() != "":
            packet = f.read(1024)
            s.send(packet)
    print("Sent ", filename)
    s.close()
    time.sleep(1)
    sending = False


def receive(name, sock):
    global receiving
    receiving = True
    filename = sock.recv(1024).decode()
    sock.send(b'FILE')
    deleting = sock.recv(1024).decode()
    if deleting == "True":
        print("Deleting ", filename)
        os.remove(filename)
        time.sleep(1)
        receiving = False
        return
    sock.send(b'DELETE')
    file_size = int(sock.recv(1024).decode())
    sock.send(b'DATA')
    f = open(filename, 'wb')
    data = sock.recv(1024)
    totalRecv = len(data)
    f.write(data)
    while totalRecv < file_size:
        data = sock.recv(1024)
        totalRecv += len(data)
        f.write(data)
    print("Received ", filename)
    sock.send(b'DONE')
    f.close()
    sock.close()
    time.sleep(1)
    receiving = False


def server():
        # Host IP
        host = ''
        port = 5000

        s = socket.socket()
        s.bind((host, port))
        s.listen(5)

        print (os.listdir())
        print ("Server Started.")
        while True:
            c, addr = s.accept()
            print ("client connected ip:<" + str(addr) + ">")
            t = threading.Thread(target=receive, args=("receive", c))
            t.start()
        s.close()

# Directory where files are changed
os.chdir(r"")
server = threading.Thread(target=server, args=())
server.start()
w = Watcher()
w.run()