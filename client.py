#!/usr/bin/python

# test stuff
import socket
from time import sleep

HOST = 'localhost'
PORT = 50007
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.send('DN|1'.encode())
    sleep(1)
    s.send('PS|1'.encode())
    sleep(1)
    s.send('CC|1'.encode())
    sleep(1)
    s.send('BL|1|2'.encode())
    sleep(1)
    s.send('CC|2'.encode())
    sleep(1)
    s.send('CD|1'.encode())
    sleep(1)
    #data = s.recv(1024)
#print('Received', repr(data))
