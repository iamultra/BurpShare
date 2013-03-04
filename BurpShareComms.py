from thread import start_new_thread
from Queue import Queue
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
from socket import error as socketerror
from itertools import izip, cycle
from base64 import b64encode, b64decode
from jarray import array as JavaArray
import ShareHttpRequestResponse

class BurpShareConnection():
	def __init__(self,insock,addr,key,queue=None,callback=None):
		self.q = queue
		self.sock = insock
		self.addr = addr
		self.key = key
		self.dorun = True
		self.callback = callback
		
	def setKey(self, newKey):
		self.key = newKey

	def die(self):
		self.dorun = False
		if self.q:
			self.q.join()
		self.sock.close()
		
class BurpShareConnectionOut(BurpShareConnection):
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
			
class BurpShareConnectionIn(BurpShareConnection):
	def run(self):
		while self.dorun:
			data = self.sock.recv(65535)
			if data:
				packet = BurpSharePacket(data)
				packet.decrypt(self.key)
				self.callback(packet, addr)
			else:
				pass #socket is dead, tell an adult
				
class BurpShareConnector:
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
		inconn = BurpShareConnectionIn(sock, addr, key, None, callback)
		outconn = BurpShareConnectionOut(sock, addr, key, outq)
		start_new_thread(inconn.run,())
		start_new_thread(outconn.run,())
		return BurpShareConnectionTracker(inconn, outconn, outq, addr, key)
		
	@staticmethod
	def establishOutgoing(ip, port, key, callback):
		sock = BurpShareConnector.createConnection(ip, port)
		if sock:
			obj = BurpShareConnector.summonWorkers(sock, (ip, port), key, callback)
			return obj
		return None

class BurpShareListener:
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
			obj = BurpShareConnector.summonWorkers(conn, addr, self.key, self.callbackChild)
			ok = self.callbackAdd(obj)
			if not ok: pass #WHAT DO?!
			
	def die(self):
		self.sock.shutdown(SHUT_RDWR)
		self.sock.close()
			
class BurpSharePacket:
	def __init__(self,data):
		self.data = data
		
	def getData(self):
		return self.data
		
	@staticmethod
	def xorcrypt(text,key):
		return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(text,cycle(key)))
		
	def decrypt(self,key):
		self.data = BurpSharePacket.xorcrypt(self.data,key)
		
	def encrypt(self,key):
		self.data = BurpSharePacket.xorcrypt(self.data,key)
		
	@staticmethod
	def jsontorr(j):
		request = JavaArray(b64decode(j["request"]),'b')
		response = JavaArray(b64decode(j["response"]),'b')
		rr = BurpShareHttpRequestResponse(request,response,j["comment"],j["highlight"],j["host"],j["port"],j["protocol"])
		return rr

	@staticmethod
	def rrtojson(rr):
		j = {}
		j["request"] = ""
		request = rr.getRequest()
		if request != None:
			j["request"] = b64encode(request.tostring())
		j["response"] = ""
		response = rr.getResponse()
		if response != None:
			j["response"] = b64encode(response.tostring())
		j["comment"] = rr.getComment()
		j["highlight"] = rr.getHighlight()
		j["host"] = rr.getHost()
		j["port"] = rr.getPort()
		j["protocol"] = rr.getProtocol()
		return j

class BurpShareConnectionTracker:
	def __init__(self, inconn, outconn, outqueue, addr, key):
		self.inconn = inconn
		self.outconn = outconn
		self.outqueue = outqueue
		if addr:
			self.host, self.port = addr
		self.key = key
	
	def getQueue(self):
		return self.outqueue
		
	def getAddr(self):
		return self.addr
		
	def getHost(self):
		return self.host
		
	def getPort(self):
		return self.port
		
	def getKey(self):
		return self.key
		
	def setKey(self, newKey):
		if inconn: inconn.setKey(newKey)
		if outconn: outconn.setKey(newKey)
		
	def die(self):
		if inconn:
			inconn.die()
			inconn = None
		if outconn:
			outconn.die()
			outconn = None
