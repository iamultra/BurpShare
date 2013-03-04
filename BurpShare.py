from burp import IBurpExtender
from burp import ITab
from burp import IHttpListener
from burp import IExtensionStateListener
from burp import IHttpRequestResponse, IHttpService
from Queue import Queue
from thread import start_new_thread
from json import dumps, loads
import ShareHttpRequestResponse
from BurpShareComms import BurpShareConnector, BurpShareListener, BurpSharePacket, BurpShareConnectionTracker
from BurpShareUI import BurpShareUI
from java.awt.event import ActionListener

PORT=61398

class BurpExtender(IBurpExtender, IHttpListener, IExtensionStateListener):
	"""
	The main extension class.
	"""
	
	def registerExtenderCallbacks(self, callbacks):
		"""
		Required by IBurpExtender. This is where initialization happens.
		"""
		self._callbacks = callbacks
		self._callbacks.setExtensionName("BurpShare")
		self._callbacks.registerHttpListener(self)
		
		self.restoreState()

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
		return
		
	def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
		"""
		Required by IHttpListener. This is where Http events come in.
		"""
		if not messageIsRequest:
			pass
			#print "got HttpMessage response"
		else:
			pass
			#print "got HttpMessage request"
		if self._isConnected():
			rr = BurpShareHttpRequestResponse(messageInfo)
			data = dumps(BurpSharePacket.rrtojson(rr))
			print "Sending", len(data), "bytes"
			packet = BurpSharePacket(data)
			self._send(packet)
		return

	def extensionUnloaded(self):
		"""
		Required by IExtensionStateListener. Destruction of the extension.
		"""
		self.server.die()
		for obj in self.clients:
			obj.die()
			
	def _setupGUI(self):
		self.actionListener = BurpShareActionListener(self)
		self.ui = BurpShareUI(self._callbacks.customizeUiComponent,self.actionListener)
		self._restoreUIState()
		
	def _setupListener(self):
		self.server = BurpShareListener(self.addIncomingPeer,self.ip,self.port,self.cryptokey,self.inject)
		self._callbacks.issueAlert("Listening on port "+str(self.port))
		start_new_thread(self.server.run,())
		
	def _killListener(self):
		self._callbacks.issueAlert("Killing listener")
		self.server.die()

	def updateListener(self, ip, port):
		self._killListener()
		self.ip = ip
		self.port = port
		self._setupListener()
		
	def updateKey(self, newKey):
		self.cryptokey = newKey
		
	def _addPeer(self, obj):
		addrstr = obj.getHost()+":"+str(obj.getPort())
		#print "adding peer to internal lists", addr
		self.clients[addrstr] = obj
		return True
		
	def addIncomingPeer(self, obj):
		"""
		Callback for incoming connections. Returns True on success, False on failure.
		"""
		addrstr = obj.getHost()+":"+str(obj.getPort())
		ret = self._addPeer(obj)
		if ret:
			self.ui.peerConnected(addrstr, self.cryptokey)
			self.saveState()
		
	def createOutgoingPeer(self, ip, port):
		"""
		Activation point for user-initiated connections. Returns True on success, False on failure.
		"""
		obj = BurpShareConnector.establishOutgoing(ip, port, self.cryptokey, self.inject)
		if obj:
			return self._addPeer(obj)
		#print "createOutgoingPeer: failed to establish outgoing connection to",ip,port
		return False
		
	def delPeer(self, addrstr):
		"""
		Activation point for user-initiated disconnections.
		"""
		self.clients[addrstr].die()
		del self.clients[addrstr]

	def _send(self, packet):
		for obj in self.clients:
			obj.getQueue().put(packet)
			
	def _isConnected(self):
		if len(self.clients)>0:
			return True
		return False
		
	def inject(self, packet, addr):
		"""
		Callback for incoming data.
		"""
		data = packet.getData()
		print "Received",len(data),"bytes from",addr
		i = ""
		try:
			i = loads(data)
		except Exception:
			print "Malformed packet from",addr
			return
		item = BurpSharePacket.jsontorr(i)
		self._callbacks.addToSiteMap(item)
		
	def restoreState(self):
		self.cryptokey = self._callbacks.loadExtensionSetting("cryptokey")
		self.ip = self._callbacks.loadExtensionSetting("listenip")
		self.port = self._callbacks.loadExtensionSetting("listenport")
		try:
			self.port = int(self.port)
		except:
			pass
		
	def saveState(self):
		self._callbacks.saveExtensionSetting("cryptokey",self.cryptokey)
		self._callbacks.saveExtensionSetting("listenip",self.ip)
		self._callbacks.saveExtensionSetting("listenport",str(self.port))
		self._saveUIState()
		
	def _restoreUIState(self):
		state = self._callbacks.loadExtensionSetting("UIState")
		if state:
			self.ui.setState()

	def _saveUIState(self):
		state = self.ui.getState()
		self._callbacks.saveExtensionSetting("UIState",state)

class BurpShareActionListener(ActionListener):
	"""
	ActionListener class. This acts as a bridge for GUI -> Main.
	"""
	def __init__(self, burpshare):
		self.burpshare = burpshare
		self.alert = burpshare._callbacks.issueAlert
		
	def actionPerformed(self, e):
		event = e.getActionCommand()
		if event == "addPeer":
			host = self.burpshare.ui.getHostText()
			c = host.split(':')
			port = PORT
			if len(c)>1:
				port = int(c[1])
			ret = self.burpshare.createOutgoingPeer(c[0],port)
			if not ret:
				self.alert("Unable to connect to "+c[0]+" port "+str(port))
				return
			addr = ip+":"+str(port)
			self.burpshare.ui.peerConnected(addr, self.cryptokey)
		elif event == "removePeer":
			peer = self.burpshare.ui.getSelectedPeer()
			if peer:
				self.burpshare.delPeer(peer)
				self.burpshare.ui.peerDisconnected(peer)
		elif event == "connectPeer":
			# figure out which peer we're talking about
			# then call self.burpshare.createOutgoingPeer(peer)
			pass
		elif event == "disconnectPeer":
			# figure out which peer we're talking about
			# then call self.burpshare.delPeer(peer)
			pass
		elif event == "updateListener":
			# pull ip & port info from box
			# then call self.burpshare.updateListener(ip, port)
			pass
		elif event == "updateKey":
			# pull new key from text field
			# then call self.burpshrae.updateKey(key)
			pass
		else:
			raise Exception("Unknown action to be performed:", event)
		self.burpshare.saveState()
		return
