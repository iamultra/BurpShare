from burp import IBurpExtender
from burp import ITab
from burp import IHttpListener
from burp import IExtensionStateListener

#TODO cleanup imports
from javax.swing import *
from java.awt import *
from javax.swing.table import DefaultTableModel
from java.awt.event import *

#
# implement ITab
#
class BurpShareUI(ITab):

	def __init__(self, customizeUiComponentFunction, actionlistener):
		self.peerList = []

		self.uiFunction = customizeUiComponentFunction
		self.actionlistener = actionlistener
		self.setupGUI()
				
	def getTabCaption(self):
		return "BurpShare"
	
	def getUiComponent(self):
		return self._panel

	def _createPeerPanel(self):
		label = JLabel("Peers")
		self.uiFunction(label)

		addPeerButton = JButton("Add")
		self.uiFunction(addPeerButton)

		delPeerButton = JButton("Remove")
		self.uiFunction(delPeerButton)

		buttonPanel = JPanel()
		buttonPanel.layout = BoxLayout(buttonPanel,BoxLayout.Y_AXIS)
		buttonPanel.add(addPeerButton)
		buttonPanel.add(delPeerButton)

		peerColNames = ('Host', 'Name', 'Key')	
		dataModel = DefaultTableModel(self.peerList,peerColNames)
		peerTable = JTable(dataModel)
		self.uiFunction(peerTable)	

		peerPanel = JPanel()
		peerPanel.layout =  BoxLayout(peerPanel,BoxLayout.X_AXIS)
		#peerPanel.add(label)
		peerPanel.add(buttonPanel)
		#peerPanel.add(addPeerButton)
		peerPanel.add(JScrollPane(peerTable))
		#peerPanel.add(delPeerButton)

		return peerPanel
	
	def _createConfigPanel(self):
		configPanel = JPanel()
		configPanel.layout = FlowLayout()

		interfaceLabel = JLabel("Interface:")
		self.uiFunction(interfaceLabel)

		keyLabel = JLabel("Shared Key:")
		self.uiFunction(keyLabel)

		interfaceField = JTextField('0.0.0.0:61398',20)
		self.uiFunction(interfaceField)

		keyField = JTextField('',20)
		self.uiFunction(keyField)

		updateButton = JButton("Update")
		self.uiFunction(updateButton)

		interfacePanel = JPanel()		
		interfacePanel.layout = FlowLayout() 
		interfacePanel.add(interfaceLabel)
		interfacePanel.add(interfaceField)

		keyPanel = JPanel()
		keyPanel.layout = FlowLayout()
		keyPanel.add(keyLabel)
		keyPanel.add(keyField)

		buttonPanel = JPanel()
		buttonPanel.layout = FlowLayout()
		buttonPanel.add(updateButton)

		configPanel.add(interfacePanel)
		configPanel.add(keyPanel)
		configPanel.add(buttonPanel)

		return configPanel

	def _createOptionsPanel(self):
		optionsPanel = JPanel()
		return optionsPanel

	def setupGUI(self):
		self._panel = JPanel()
		self._panel.layout = BoxLayout(self._panel,BoxLayout.Y_AXIS)
		
		#TODO separate properly
		#peerSeparator = JSeparator()
		#configSeparator = JSeparator()

		#TODO fixup labels
		#peerLabel = JLabel("Peers")
		#self.uiFunction(peerLabel)	
		#configLabel = JLabel("Configuration")
		#self.uiFunction(configLabel)
		#optionsLabel = JLabel("Options")
		#self.uiFunction(optionsLabel)

		#self._panel.add(peerLabel)
		self._panel.add(self._createPeerPanel())
		#self._panel.add(peerSeparator)
		#self._panel.add(configLabel)
		self._panel.add(self._createConfigPanel())
		#self._panel.add(configSeparator)
		#self._panel.add(optionsLabel)	
		self._panel.add(self._createOptionsPanel())

			
	def peerConnected(self, addressString, key):
		pass
		
	def peerDisconnected(self, addressString):
		pass

	def getSelectedPeer(self):
		pass
		
	def getHostText(self):
		pass
		
	def getState(self):
		"""
		Returns the internal state of BurpShareUI as a string.
		"""
		return ""
		
	def setState(self, string):
		"""
		Takes a string returned by getState() and sets the internal state accordingly.
		Note that all imported connections should be in the disconnected state.
		"""
		pass
