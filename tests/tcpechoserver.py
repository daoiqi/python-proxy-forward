#!/usr/bin/env python

"""
A simple echo server
"""

from __future__ import print_function
import socket

def main():
    host = ''
    port = 50000
    backlog = 1
    size = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host,port))
    s.listen(backlog)
    while 1:
        client, address = s.accept()
        data = client.recv(size)
        if not data:
            print("client disconnected")
            break

        if data == 'quit':
            print("client quit")
            break

        # print(data)
        client.send(data)
        client.close()

    s.shutdown(socket.SHUT_RDWR)
    s.close()

if __name__ == '__main__':
    main()
