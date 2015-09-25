# -*- coding: utf-8 -*-
import socket
import time


if __name__ == "__main__":
	connFd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

	connFd.connect(("127.0.0.1", 3333))
	print "connect to network server success"

	while True:
		data = raw_input("raw_input:")
		if connFd.send(data) != len(data):
			print "send data to network server failed"
			break
		print connFd.recv(1024)

	connFd.close()
