#!/usr/bin/python

# Echo client program
import socket
from time import sleep

HOST = 'localhost'    # The remote host
PORT = 50007              # The same port as used by the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.send('DN|1'.encode())
    sleep(1)
    s.send('PS|1'.encode())
    sleep(1)
    s.send('CC|1'.encode())
    sleep(1)
    s.send('BL|0|2'.encode())
    sleep(1)
    s.send('CD|1'.encode())
    sleep(1)
    #data = s.recv(1024)
#print('Received', repr(data))
