#!/usr/bin/env python

from __future__ import print_function
import socket
import sys
from timeout import timeout


host = 'localhost'
port = 50000
backlog = 4
size = 1024
count = 0


def send_server(message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (host, port)
    sock.connect(server_address)

    try:
        sock.sendall(message)

        data = sock.recv(size)

    finally:
        # print('closing socket')
        sock.close()


def shutdown_server():
    send_server('quit')

@timeout(10)
def run_test():
    global count
    while True:
        send_server('Hello World!')
        count += 1


def main():
    try:
        run_test()
    except Exception as e:
        print (e)
    finally:
        pass

    print('count=%s' % count)
    shutdown_server()


if __name__ == '__main__':
    main()
