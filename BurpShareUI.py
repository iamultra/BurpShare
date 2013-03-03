from burp import IBurpExtender
from burp import ITab
from burp import IHttpListener
from burp import IExtensionStateListener

from javax.swing import *
from java.awt import *
from javax.swing.table import DefaultTableModel
from java.awt.event import *

#ActionListener, ActionEvent

#from javax.swing import JSplitPane, JTextField, JList, JScrollPane, JButton, JPanel, DefaultListModel, ListSelectionModel, BoxLayout

#from java.awt import Component, GridLayout 
#
# implement ITab
#

class BurpShareUI(ITab):

	def __init__(self, customizeUiComponentFunction, actionlistener):
		self.uiFunction = customizeUiComponentFunction
		self.actionlistener = actionlistener
		self.setupGUI()
			
	def getTabCaption(self):
		return "BurpShare"
	
	def getUiComponent(self):
		return self._panel

	def _createPeerPanel(self):
		self.peerList = [
			["127.0.0.1","Test","testkey"],
			["192.168.1.1","Test2","newkey"],
			["127.0.0.1","Test","testkey"],
			["192.168.1.1","Test2","newkey"],		
			["127.0.0.1","Test","testkey"],
			["192.168.1.1","Test2","newkey"],
		]

		peerPanel = JPanel(GridLayout(0,2))

		label = JLabel("Peers")

		addPeerButton = JButton("Add")
		addPeerButton.setMargin(Insets(1,1,1,1))
		delPeerButton = JButton("Remove")
		delPeerButton.setMargin(Insets(1,1,1,1))

		peerColNames = ('Host', 'Name', 'Key')	
		dataModel = DefaultTableModel(self.peerList,peerColNames)
		peerTable = JTable(dataModel) 		

		#peerPanel.add(label)
		peerPanel.add(addPeerButton)
		peerPanel.add(peerTable)
		peerPanel.add(delPeerButton)

		return peerPanel
	
	def _createConfigPanel(self):
		configPanel = JPanel(GridLayout(0,2))

		label = JLabel("")

		interfaceLabel = JLabel("Interface: ")
		keyLabel = JLabel("Shared Key: ")

		interfaceField = JTextField('12345',5)
		keyField = JTextField('',20)

		configPanel.add(interfaceLabel)
		configPanel.add(interfaceField)
		configPanel.add(keyLabel)
		configPanel.add(keyField)

		return configPanel

	def _createOptionsPanel(self):
		optionsPanel = JPanel()
		return optionsPanel


	def setupGUI(self):
		self._panel = JPanel()
		self._panel.layout = BoxLayout(self._panel,BoxLayout.Y_AXIS)
		self._panel.add(self._createPeerPanel())
		self._panel.add(self._createConfigPanel())	
		self._panel.add(self._createOptionsPanel())

		# Burp-specific UI customizations
		#self._callbacks.customizeUiComponent(self._splitpane)
		#self._callbacks.customizeUiComponent(self._keyfield)
		#self._callbacks.customizeUiComponent(jlist)
		#self._callbacks.customizeUiComponent(listscroller)
		#self._callbacks.customizeUiComponent(addbutton)
		#self._callbacks.customizeUiComponent(delbutton)
		#self._callbacks.customizeUiComponent(self._hostfield)
		#self._callbacks.customizeUiComponent(buttons)
		#self._callbacks.customizeUiComponent(jpanel)
		
	def peerConnected(self, addressString, key):
		pass
		
	def peerDisconnected(self, addressString):
		pass

