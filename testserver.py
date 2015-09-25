# -*- coding: utf-8 -*-
import server
import time

class CTestServer(server.Server):

	def __init__(self):
		super(CTestServer, self).__init__()

	def OnConnected(self, connid):
		print "OnConnected..",connid

	def OnDisconnected(self, connid):
		print "OnDisconnected..",connid

	def OnNewDataRecv(self, connid):
		conn = self.GetConnect(connid)
		while conn.GetReadBufSize() > 0:
			data = conn.PopReadBuf(4*1024)
			print "connid %s recvdata:%s"%(connid, data)
			conn.SendData("server recv %s btypes data"%len(data))



if __name__ == '__main__':
	testServer = CTestServer()

	testServer.Start("127.0.0.1", 3333)

	while True:
		testServer.ProcessOnce()
		time.sleep(0.005)

	testServer.End()



