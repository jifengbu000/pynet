# -*- coding: utf-8 -*-

import socket, select, errno
import traceback
import platform
from connection import Connect

#http://my.oschina.net/moooofly/blog/147297
#http://scotdoyle.com/python-epoll-howto.html



TIME_OUT = 0.0001


class ServerBase(object):
	def __init__(self):
		self._server_address = None
		self._port = None
		self._socket = None

		self._connections = {}

	def IsStarting(self):
		return self._socket is not None


	def Start(self, listenip, port):
		if self.IsStarting():
			return False

		self._server_address = (listenip, port)
		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._socket.bind(self._server_address)
		self._socket.listen(1)
		print  "start server suss, server addr:" , self._server_address
		self._socket.setblocking(0)

		return True

	def End(self):
		if not self.IsStarting():
			return
		self.CloseAllConect()
		self._socket.close()
		self._socket = None

	def ProcessOnce(self):
		pass

	def CreateConnect(self, connsocket):
		return Connect(connsocket)

	def GetConnect(self, fileno):
		return self._connections.get(fileno)

	def AcceptConnect(self):
		connsocket, address = self._socket.accept()
		connsocket.setblocking(0)
		conn = self.CreateConnect(connsocket)
		self._connections[connsocket.fileno()] = conn
		try:
			self.OnConnected(connsocket.fileno())
		except:
			traceback.print_exc()
		return connsocket

	def CloseConnect(self, fileno):
		connection =self._connections.get(fileno)
		if not connection:
			return False
		connection.Close()
		self._connections.pop(fileno, None)
		try:
			self.OnDisconnected(fileno)
		except:
			traceback.print_exc()
		return True



	def CloseAllConect(self):
		for fileno in self._connections.keys():
			self.CloseConnect(fileno)

	def RecvConnectData(self, fileno):
		connection = self._connections.get(fileno)
		if not connection:
			return
		connection.RecvConnectData(self)

	def SendConnectData(self, fileno):
		connection = self._connections.get(fileno)
		if not connection:
			return
		connection.SendConnectData(self)


	#==========回调===========
	def OnConnected(self, connid):
		pass

	def OnDisconnected(self, connid):
		pass

	def OnNewDataRecv(self, connid):
		pass

	def _OnConnSendData(self, fileno, sendSize):
		pass

	def _OnConnRecvData(self, fileno, recvSize):
		pass




class Server_Linux(ServerBase):
	def __init__(self):
		super(Server_Linux, self).__init__()
		self._epoll = None


	def Start(self, listenip, port):
		if not super(Server_Linux, self).Start(listenip, port):
			return False
		self._epoll = select.epoll()
		self._epoll.register(self._socket.fileno(), select.EPOLLIN)
		return True


	def End(self):
		if not self.IsStarting():
			return
		self._epoll.unregister(self._socket.fileno())
		self._epoll.close()
		self._epoll = None
		super(Server_Linux, self).End()


	def ProcessOnce(self):
		if not self.IsStarting():
			return
		events = self._epoll.poll(TIME_OUT)
		for fileno, event in events:
			if event & select.EPOLLIN:
				if fileno == self._socket.fileno():
					connsocket = self.AcceptConnect()
					self._epoll.register(connsocket.fileno(), select.EPOLLIN)
				else:
					self.RecvConnectData(fileno)
			elif event & select.EPOLLOUT:
				self.SendConnectData(fileno)
			elif event & select.EPOLLHUP:
				self.CloseConnect(fileno)

	def CloseConnect(self, fileno):
		if super(Server_Linux, self).CloseConnect(fileno):
			self._epoll.unregister(fileno)


	def _OnConnSendData(self, fileno, sendSize):
		self._epoll.modify(fileno, select.EPOLLIN | select.EPOLLET)

	def _OnConnRecvData(self, fileno, recvSize):
		self._epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)


class CServer_Windows(ServerBase):
	def __init__(self):
		super(CServer_Windows, self).__init__()

	def GetInputs(self):
		return [conn._socket for conn in self._connections.itervalues()] + [self._socket]

	def GetOutputs(self):
		return [conn._socket for conn in self._connections.itervalues()]

	def ProcessOnce(self):
		if not self.IsStarting():
			return
		inputs = self.GetInputs()
		outputs = self.GetOutputs()
		readable , writable , exceptional = select.select(inputs, outputs, inputs, TIME_OUT)

		for s in readable:
			if s == self._socket:
				self.AcceptConnect()
			else:
				self.RecvConnectData(s.fileno())

		for s in writable:
			self.SendConnectData(s.fileno())

		for s in exceptional:
			self.CloseConnect(s.fileno())


Server = None

if platform.system() == "Linux":
	Server = Server_Linux
elif platform.system() == "Windows":
	Server = CServer_Windows
