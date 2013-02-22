from burp import IBurpExtender
from burp import ITab
from burp import IHttpListener
from burp import IExtensionStateListener
from burp import IHttpRequestResponse, IHttpService
from Queue import Queue
from thread import start_new_thread
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from socket import error as socketerror
from ssl import wrap_socket
from itertools import izip, cycle
from json import dumps, loads
from base64 import b64encode, b64decode
from javax.swing import JSplitPane, JTextField, JList, JScrollPane, JButton, JPanel, DefaultListModel, ListSelectionModel, BoxLayout
from java.awt.event import ActionListener, ActionEvent
#from java.lang import String as JavaString
#from java.io import ObjectInputStream, ObjectOutputStream, ByteArrayInputStream, ByteArrayOutputStream
from jarray import array as JavaArray
import ShareHttpRequestResponse

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

class BurpExtender(IBurpExtender, ITab, IHttpListener, IExtensionStateListener, ActionListener):
	
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
			try:
				self.server = ShareServer(self.inject,"0.0.0.0",PORT,self.cryptokey)
			except Exception, e:
				self._callbacks.unloadExtension()
				raise e
		try:
			start_new_thread(self.server.run,())
			self.clients = {}
			self.setupGUI()
			self._callbacks.addSuiteTab(self)
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
			connectstring = self._hostfield.getText()
			c = connectstring.split(':')
			if len(c)==1:
				self.addPeer(c[0],PORT)
			elif len(c)==2:
				self.addPeer(c[0],c[1])
			else return
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
	# implement ITab
	#
		
	def getTabCaption(self):
		return "BurpShare"
	
	def getUiComponent(self):
		return self._splitpane
		
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
		# setup UI stuff
		self._splitpane = JSplitPane(JSplitPane.VERTICAL_SPLIT)
		# top UI
		#self._keyfield = JTextField(self.cryptokey) 
		#self._splitpane.setLeftComponent(self._keyfield)
		# bottom list
		self._clientlist = DefaultListModel()
		jlist = JList(self._clientlist)
		jlist.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
		jlist.setLayoutOrientation(JList.VERTICAL)
		listscroller = JScrollPane(jlist)
		# bottom buttons
		addbutton = JButton("+")
		addbutton.setActionCommand("+")
		addbutton.addActionListener(self)
		delbutton = JButton("-")
		delbutton.setActionCommand("-")
		delbutton.addActionListener(self)
		self._hostfield = JTextField(20)
		buttons = JPanel()
		buttons.setLayout(BoxLayout(buttons,BoxLayout.LINE_AXIS))
		buttons.add(delbutton)
		buttons.add(self._hostfield)
		buttons.add(addbutton)
		# bottom panel
		jpanel = JPanel()
		jpanel.add(listscroller)
		jpanel.add(buttons)
		self._splitpane.setRightComponent(jpanel)
		# Burp-specific UI customizations
		self._callbacks.customizeUiComponent(self._splitpane)
		#self._callbacks.customizeUiComponent(self._keyfield)
		self._callbacks.customizeUiComponent(jlist)
		self._callbacks.customizeUiComponent(listscroller)
		self._callbacks.customizeUiComponent(addbutton)
		self._callbacks.customizeUiComponent(delbutton)
		self._callbacks.customizeUiComponent(self._hostfield)
		self._callbacks.customizeUiComponent(buttons)
		self._callbacks.customizeUiComponent(jpanel)
		
	def addPeer(self, ip, port):
		# XXX: should check to see if it already exists
		try:
			self.clients[ip] = ShareClient(ip,port)
		except socketerror:
			self._callbacks.issueAlert("Failed to connect to "+ip+" on port "+str(port))
			return
		start_new_thread(self.clients[ip].run,())
		
	def delPeer(self, ip):
		del self.clients[ip]

	def send(self, packet):
		for ip,c in self.clients.items():
			c.send(packet)
		
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
		self.port = int(self._callbacks.loadExtensionSetting("listenport"))
		
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
		self.socket.bind( (ip,port) )
		self.socket.listen(5)
		
	def run(self):
		while True:
			conn, addr = self.socket.accept()
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