from burp import IBurpExtender
from burp import ITab
from burp import IHttpListener
from burp import IExtensionStateListener
from burp import IHttpRequestResponse, IHttpService
from Queue import Queue
from thread import start_new_thread
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET, SO_REUSEADDR
from socket import error as socketerror
from ssl import wrap_socket
from itertools import izip, cycle
from json import dumps, loads
from base64 import b64encode, b64decode
from jarray import array as JavaArray
import ShareHttpRequestResponse

from BurpShareUI import *

PORT=61398

def xorcrypt(text,key):
    return ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(text,cycle(key)))

def jsontorr(j):
	request = JavaArray(b64decode(j["request"]),'b')
	response = JavaArray(b64decode(j["response"]),'b')
	rr = ShareHttpRequestResponse(request,response,j["comment"],j["highlight"],j["host"],j["port"],j["protocol"])
	return rr

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

class BurpExtender(IBurpExtender, IHttpListener, IExtensionStateListener, ActionListener):
	
	#
	# implement IBurpExtender
	#
	
	def	registerExtenderCallbacks(self, callbacks):
		self._callbacks = callbacks
		self._callbacks.setExtensionName("BurpShare")
		self._callbacks.registerHttpListener(self)
		
		self.restorestate()

		if not self.cryptokey: self.cryptokey = 'ThereCanBeOnlyOne'
		if not self.ip: self.ip = '0.0.0.0'
		if not self.port: self.port = PORT
		
		try:
			self.server = ShareServer(self.inject,self.ip,self.port,self.cryptokey)
		except Exception, e:
			self._callbacks.unloadExtension()
			raise e
		try:
			self._callbacks.issueAlert("Listening on port "+str(self.port))
			start_new_thread(self.server.run,())
			self.clients = {}
			self.setupGUI()
			self._callbacks.addSuiteTab(self.ui)
		except Exception, e:
			self.server.die()
			self._callbacks.unloadExtension()
			raise e
		self.savestate()
		return
		
	#
	# implement ActionListener
	#
		
	def actionPerformed(self, e):
		event = e.getActionCommand()
		if event == "+":
			host = self._hostfield.getText()
			c = host.split(':')
			if len(c)==1:
				ok = self.addPeer(c[0],int(PORT))
			elif len(c)==2:
				ok = self.addPeer(c[0],int(c[1]))
			else: return
			if ok:
				self._clientlist.addElement(host)
		elif event == "-":
			# this needs to read which entry is selected in the clientlist
			# kill the peer, then remove it from the list
			pass
		else:
			raise Exception("Unknown action to be performed:", event)
		self.savestate()
		return
		

		
	#
	# implement IHttpListener
	#
		
	def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
		if not messageIsRequest:
			pass
			#print "got HttpMessage response"
		else:
			pass
			#print "got HttpMessage request"
		if self.isConnected():
			rr = ShareHttpRequestResponse(messageInfo)
			data = dumps(rrtojson(rr))
			print "Sending", len(data), "bytes"
			data = xorcrypt(data,self.cryptokey)
			packet = SharePacket(data)
			self.send(packet)
		return
	
	#
	# implement IExtensionStateListener
	#
		
	def extensionUnloaded(self):
		self.server.die()
		for client in self.clients:
			client.die()
			
			
	def setupGUI(self):
		self.ui = BurpShareUI()
		
	def addPeer(self, ip, port):
		if ip in self.clients:
			self._callbacks.issueAlert("Already connected to "+ip)
			return False
		try:
			self.clients[ip] = ShareClient(ip,port)
		except socketerror:
			self._callbacks.issueAlert("Failed to connect to "+ip+" on port "+str(port))
			return False
		start_new_thread(self.clients[ip].run,())
		return True
		
	def delPeer(self, ip):
		del self.clients[ip]

	def send(self, packet):
		for ip,c in self.clients.items():
			c.send(packet)
			
	def isConnected(self):
		if len(self.clients)>0:
			return True
		return False
		
	def inject(self, packet, addr):
		data = packet.getData()
		print "Received",len(data),"bytes from",addr
		data = xorcrypt(data,self.cryptokey)
		i = ""
		try:
			i = loads(data)
		except Exception:
			print "Malformed packet from",addr
			return
		item = jsontorr(i)
		self._callbacks.addToSiteMap(item)
		
	def restorestate(self):
		self.cryptokey = self._callbacks.loadExtensionSetting("cryptokey")
		self.ip = self._callbacks.loadExtensionSetting("listenip")
		self.port = self._callbacks.loadExtensionSetting("listenport")
		try:
			self.port = int(self.port)
		except:
			pass
		
	def savestate(self):
		self._callbacks.saveExtensionSetting("cryptokey",self.cryptokey)
		self._callbacks.saveExtensionSetting("listenip",self.ip)
		self._callbacks.saveExtensionSetting("listenport",str(self.port))

class ShareClient:
	def __init__(self,ip,port):
		self.q = Queue()
		self.ip = ip
		self.port = port
		self.socket = socket(AF_INET,SOCK_STREAM)
		self.socket.settimeout(5.0)
		self.socket.connect( (self.ip,self.port) )
		self.dorun = True
		
	def send(self,packet):
		self.q.put(packet)
		
	def run(self):
		while self.dorun:
			packet = self.q.get()
			self.socket.sendall(packet.getData())
			self.q.task_done()
			
	def die(self):
		self.dorun = False
		self.q.join()
		self.socket.close()
			
class ShareServer:
	def __init__(self,burpmethod,ip,port,key):
		self.q = Queue()
		self.burpmethod = burpmethod
		self.socket = socket(AF_INET,SOCK_STREAM)
		self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.socket.bind( (ip,port) )
		self.socket.listen(5)
		
	def run(self):
		while True:
			conn, addr = self.socket.accept()
			# Shouldn't we fork on accept()?
			while True:
				data = conn.recv(65535)
				if not data: break
				self.burpmethod(SharePacket(data),addr)
			
	def die(self):
		self.socket.shutdown(SHUT_RDWR)
		self.socket.close()
			
class SharePacket:
	def __init__(self,data):
		self.data = data
		
	def getData(self):
		return self.data
