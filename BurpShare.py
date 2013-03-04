from burp import IBurpExtender
from burp import ITab
from burp import IHttpListener
from burp import IExtensionStateListener
from burp import IHttpRequestResponse, IHttpService
from Queue import Queue
from thread import start_new_thread
from json import dumps, loads
from base64 import b64encode, b64decode
from jarray import array as JavaArray
import ShareHttpRequestResponse
from BurpShareComms import ShareConnector, ShareListener, SharePacket
from BurpShareUI import *

PORT=61398

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

class BurpExtender(IBurpExtender, IHttpListener, IExtensionStateListener):
	
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
			self._setupListener()
			self.clients = {}
			self._setupGUI()
			self._callbacks.addSuiteTab(self.ui)
		except Exception, e:
			self.server.die()
			self._callbacks.unloadExtension()
			raise e
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
		if self._isConnected():
			rr = ShareHttpRequestResponse(messageInfo)
			data = dumps(rrtojson(rr))
			print "Sending", len(data), "bytes"
			data = xorcrypt(data,self.cryptokey)
			packet = SharePacket(data)
			self._send(packet)
		return
	
	#
	# implement IExtensionStateListener
	#
		
	def extensionUnloaded(self):
		self.server.die()
		for client in self.clients:
			client.die()
			
	def _setupGUI(self):
		self.actionListener = BurpShareActionListener(self)
		self.ui = BurpShareUI(self._callbacks.customizeUiComponent,self.actionListener)
		
	def _setupListener(self):
		self.server = ShareListener(self.addIncomingPeer,self.ip,self.port,self.cryptokey,self.inject)
		self._callbacks.issueAlert("Listening on port "+str(self.port))
		start_new_thread(self.server.run,())
		
	def _addPeer(self, ip, port, outq):
		addr = ip+":"+str(port)
		print "adding peer to internal lists", addr
		self.ui.peerConnected(addr, self.cryptokey)
		self.clients[addr] = outq
		return True
		
	def addIncomingPeer(self, addr, outq):
		ip, port = addr
		return self._addPeer(ip, port, outq)
		
	def createOutgoingPeer(self, ip, port):
		outq = ShareConnector.establishOutgoing(ip, port, self.cryptokey, self.inject)
		if outq:
			return self._addPeer(ip, port, outq)
		print "createOutgoingPeer: failed to establish outgoing connection to",ip,port
		return False
		
	def delPeer(self, addr):
		self.ui.peerDisconnected(addr)
		del self.clients[addr]

	def _send(self, packet):
		for q in self.clients:
			q.put(packet)
			
	def _isConnected(self):
		if len(self.clients)>0:
			return True
		return False
		
	def inject(self, packet, addr):
		data = packet.getData()
		print "Received",len(data),"bytes from",addr
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

class BurpShareActionListener(ActionListener):
	def __init__(self, burpshare):
		self.burpshare = burpshare
		
	def actionPerformed(self, e):
		event = e.getActionCommand()
		if event == "+":
			host = self.burpshare.ui.getHostText()
			c = host.split(':')
			if len(c)==1:
				ret = self.burpshare.createOutgoingPeer(c[0],int(PORT))
			elif len(c)==2:
				ret = self.burpshare.createOutgoingPeer(c[0],int(c[1]))
			else: return
		elif event == "-":
			peer = self.burpshare.ui.getSelectedPeer()
			if peer:
				self.burpshare.delPeer(peer)
		else:
			raise Exception("Unknown action to be performed:", event)
		burpshare.savestate()
		return
