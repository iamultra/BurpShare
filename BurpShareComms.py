from thread import start_new_thread
from Queue import Queue
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
from socket import error as socketerror
from itertools import izip, cycle

class ShareConnection():
	def __init__(self,insock,addr,key,queue=None,callback=None):
		Thread.__init__(self)
		self.q = queue
		self.sock = insock
		self.addr = addr
		self.key = key
		self.dorun = True
		self.callback = callback

	def die(self):
		self.dorun = False
		if self.q:
			self.q.join()
		self.sock.close()
		
class ShareConnectionOut(ShareConnection):
	def run(self):
		while self.dorun:
			packet = self.q.get() #BLOCKS
			packet.encrypt(self.key)
			try:
				self.sock.sendall(packet.getData())
			except socketerror, e:
				print e #socket is dead, tell an adult
			finally:
				self.q.task_done()
			
class ShareConnectionIn(ShareConnection):
	def run(self):
		while self.dorun:
			data = self.sock.recv(65535)
			if data:
				packet = SharePacket(data)
				packet.decrypt(self.key)
				self.callback(packet, addr)
			else:
				pass #socket is dead, tell an adult
				
class ShareConnector:
	@staticmethod
	def createConnection(ip, port):
		sock = socket(AF_INET,SOCK_STREAM)
		sock.settimeout(5.0)
		try:
			sock.connect( (ip,port) )
		except socketerror, e:
			print "ShareConnector.createConnection:",e
			return None
		return sock
		
	@staticmethod
	def summonWorkers(sock, addr, key, callback):
		outq = Queue()
		inconn = ShareConnectionIn(sock, addr, key, None, callback)
		outconn = ShareConnectionOut(sock, addr, key, outq)
		start_new_thread(inconn.run,())
		start_new_thread(outconn.run,())
		return outq
		
	@staticmethod
	def establishOutgoing(ip, port, key, callback):
		sock = ShareConnector.createConnection(ip, port)
		if sock:
			outq = ShareConnector.summonWorkers(sock, (ip, port), key, callback)
			return outq
		return None

class ShareListener:
	def __init__(self,addfunc,ip,port,key,sendupfunc):
		self.q = Queue()
		self.callbackAdd = addfunc
		self.callbackChild = sendupfunc
		self.key = key
		self.sock = socket(AF_INET,SOCK_STREAM)
		self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.sock.bind( (ip,port) )
		self.sock.listen(5)
		
	def run(self):
		while True:
			conn, addr = self.sock.accept()
			print "ShareListener: new connection from", addr
			outq = ShareConnector.summonWorkers(conn, addr, self.key, self.callbackChild)
			ok = self.callbackAdd(addr, outq)
			if not ok: pass #WHAT DO?!
			
	def die(self):
		self.sock.shutdown(SHUT_RDWR)
		self.sock.close()
			
class SharePacket:
	def __init__(self,data):
		self.data = data
		
	def getData(self):
		return self.data
		
	@staticmethod
	def xorcrypt(text,key):
		return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(text,cycle(key)))
		
	def decrypt(self,key):
		self.data = SharePacket.xorcrypt(self.data,key)
		
	def encrypt(self,key):
		self.data = SharePacket.xorcrypt(self.data,key)
