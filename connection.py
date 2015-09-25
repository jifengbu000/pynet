# -*- coding: utf-8 -*-

import socket, select, errno
import traceback
import time


class Connect(object):
	MAX_RECV_DATA = 8*1024*1024
	MAX_SEND_DATA = 8*1024*1024
	EACH_RECV_SIZE = 4*1024
	EACH_SEND_SIZE = 4*1024
	def __init__(self, connsocket):
		self._socket = connsocket
		self._readBuf = ""
		self._writeBuf = ""

	def GetReadBufSize(self):
		return len(self._readBuf)

	def GetWriteBufSize(self):
		return len(self._readBuf)

	def Close(self):
		self._socket.close()
		self._socket = None

	def RecvConnectData(self, server):
		recvSize = 0
		while True:
			try:
				if recvSize > self.MAX_RECV_DATA:
					print "recvSize %s overflow"%recvSize
					break
				data = self._socket.recv(self.EACH_RECV_SIZE)
				if data:
					recvSize += len(data)
					self._readBuf += data
				elif recvSize <= 0: #走到这里出错了吧
					server.CloseConnect(self._socket.fileno())
			except socket.error, msg:
				print msg.errno, msg
				if msg.errno in [errno.EAGAIN, errno.EWOULDBLOCK]:
					break
				else:
					print traceback.print_exc()
					server.CloseConnect(self._socket.fileno())
					break

		if recvSize > 0:
			server.OnNewDataRecv(self._socket.fileno())

		server._OnConnRecvData(self._socket.fileno(), recvSize)

	def SendConnectData(self, server):
		sendLen = 0
		while True:
			sendLen += self._socket.send(self._writeBuf[sendLen:sendLen+self.EACH_SEND_SIZE])
			if sendLen >= len(self._writeBuf):
				break
			if sendLen >= self.MAX_SEND_DATA:
				break
		self._writeBuf = self._writeBuf[sendLen:]
		server._OnConnSendData(self._socket.fileno(), sendLen)

	def PopReadBuf(self, nSize):
		if nSize <= 0:
			return ""
		data = self._readBuf[:nSize]
		self._readBuf = self._readBuf[nSize:]
		return data

	def SendData(self, data):
		self._writeBuf += data
