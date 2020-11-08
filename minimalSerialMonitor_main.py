'''
	MINIMALIST SERIAL MONITOR - By YekoHat

BaudRate dispo pour l'instant (ajoutes a GLADE):
- 0 : 9600
- 1 : 115200

- Mettre en place toutes fonctions de la gui puis intégrer le serial
- Enlever le "D:" devant les messages debug et à la place les mettre en gras
'''

import gi
import serial, sys, glob
from threading import Thread

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

macroList = ["","","","",""]
builder = Gtk.Builder()
builder.add_from_file("guiMinimalSerialPY22.glade")
#builder.add_from_file("C:/Users/YekoHat/Desktop/ShareLubuntu/guiMinimalSerialPY22.glade")

textBuff = builder.get_object("textBuffer")
sendEntry = builder.get_object("sendEntry")
comBox = builder.get_object("comPortBox")
baudBox = builder.get_object("baudRateBox")
connectBtn = builder.get_object("connectButton")

serialPort = serial.Serial()

#tag_bold = textBuff.create_tag("bold", weight=Pango.Weight.BOLD)
tag_orange = textBuff.create_tag("bg", background="orange")

print("Initialization...")

#------------------- FONCTIONS ------------------

# Simplification des draw de texte avec un debug console + textView
def addText(text, textBuffer=textBuff):
	print(text)
	# Curseur du début du texte qui va être écrit 
	beforeIter = textBuffer.get_end_iter()
	textBuffer.insert(beforeIter, text)
	textBuffer.apply_tag(tag_orange, beforeIter, textBuffer.get_end_iter())

# Pour eviter le if debug activé, print etc.
def debug(text, enable=builder.get_object("debugCheck").get_active()):
	if(enable):
		addText("\nD: " + text)

# Ce qui sera la fonction qui enverra des données sur le serial port
def sendText(txt):
	if(builder.get_object("debugCheck").get_active()): #Pour un message de debug
		debug("Sended \"" + txt + "\"")
	elif(builder.get_object("echoCheck").get_active()): #Pour l'echo
		addText(txt)
	
	if(builder.get_object("NLcheck").get_active()):
		txt += "\n"
	if(builder.get_object("CRcheck").get_active()):
		txt += "\r"

	serialPort.write(txt.encode("utf-8"))

def getAvailableSerialPort():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def connectSerial():
	try:
		comPort = comBox.get_active_text()
		baudRate = int(baudBox.get_active_text())
	except ValueError: # Si baudrate_id = '' 
		pass

	serialPort.baudrate = baudRate
	serialPort.port = comPort

	try:
		serialPort.open()
	except FileNotFoundError:
		debug("Serial port not found. Check if the port is still available..")

	if(serialPort.is_open):
		debug("Connected to " + comPort + " with a baud rate of " + str(baudRate))
	else:
		debug("Failed to connect.")

def disconnectSerial():
	serialPort.close()
	if(serialPort.is_open == True): #Encore connecté donc échec
		debug("Failed to disconnect port..")
		return False
	else:
		debug("Disconnected successfully")
		return True

# Modifie les attributs des widgets en lien avec la connection serial
def toggleWidgets(connected):
	if(connected == False):
		connectBtn.set_label("Connect")
	else:
		connectBtn.set_label("Disconnect")

	comBox.set_sensitive(not connected)
	baudBox.set_sensitive(not connected)

	sendEntry.set_sensitive(connected)
	builder.get_object("sendBtn").set_sensitive(connected)
	builder.get_object("macroBox").set_sensitive(connected)

# Gère les macro
def macro(idMacro):
	editMode = builder.get_object("editToggle").get_active()
	textToSave = sendEntry.get_text()
	if(editMode == True):
		macroList[idMacro] = textToSave
		debug("Macro " + str(idMacro) + " set to " + textToSave)
	else:
		sendText(macroList[idMacro])

	debug("Mc" + str(idMacro) + ", editMode= " + str(editMode) + ", text= " + textToSave)

#-------------------------------------------------------

class SignalHandler:
	def onChangeBaud(self, *args):
		debug("Change baud to id:" + builder.get_object("baudRateBox").get_active_id())

	def onEditDone(self, *args):
		self.onChangeBaud()

	def onMc1Click(self, *args):
		macro(1)
	def onMc2Click(self, *args):
		macro(2)
	def onMc3Click(self, *args):
		macro(3)
	def onMc4Click(self, *args):
		macro(4)
	def onMc5Click(self, *args):
		macro(5)

	def onSendClick(self, *args):
		sendText(sendEntry.get_text())

	def onCleanClick(self, *args):
		textBuff.delete(textBuff.get_start_iter(), textBuff.get_end_iter())
		debug("Buffer cleaned !")

	def onInfoClick(self, *args):
		dialog = Gtk.MessageDialog(window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Minimal Serial Monitor (with some extras)")
		dialog.format_secondary_text("Coded by YekoHat with Python and GTK3+")
		dialog.run()
		dialog.destroy()

	def onConnectClick(self, *args):
		print("Connect click")

		if(comBox.get_active_id() == None or baudBox.get_active_id() == None):
			debug("ComPort or BaudRate isn't selected !")

		#debug("isOpen before action state: " + str(serialPort.is_open))

		if(serialPort.is_open == False):
			connectSerial()
			toggleWidgets(True)

		else:
			if(disconnectSerial() == True): #Si on s'est bien déconnecté
				toggleWidgets(False)
			else:
				toggleWidgets(True)

		#debug("isOpen after action state: " + str(serialPort.is_open))

	#A chaque fois qu'on touche a la comBox, on recharge la liste des ports
	def onFocusComBox(self, *args):
		# Ajoute les ports dispo a la combox
		for cpt, port in enumerate(getAvailableSerialPort()):
			comBox.append(str(cpt), str(port))

	# Active ou désactive le char wrapping du texte dans le textView
	def onWrapToggle(self, *args):
		if(builder.get_object("wrapToggle").get_active() == True):
			textView.set_wrap_mode(GTK_WRAP_CHAR)
		else:
			textView.set_wrap_mode(GTK_WRAP_NONE)

class SerialThread(Thread):
	def __init__(self):
		Thread.__init__(self)

	def run(self):
		#A executer pendant l'execution du thread
		debug("Serial reader thread running !")
		while(serialPort.is_open):
			addText(serialPort.readline())
		
window = builder.get_object("mainWindow")
builder.connect_signals(SignalHandler())

threadSerial = SerialThread()
threadSerial.start()

window.show_all()
Gtk.main()

