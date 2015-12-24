from pymudclient.escape_parser import EscapeParser
from code import InteractiveConsole
from textwrap import TextWrapper
import time
from pymudclient.colours import HexFGCode, bg_code, BLACK
from pymudclient.metaline import simpleml, json_to_metaline, metaline_to_json
from pymudclient.net.telnet import TelnetClientFactory
import json
from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineReceiver


class ClientProtocol(ProcessProtocol, LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 131072 * 8 * 100

    def __init__(self, communicator):
        self.communicator = communicator
        self.messages_not_acknowledged = 0
        
    def send_to_client(self, meth, params):
        print('send to processor: %s, %s'%(meth, json.dumps(params)))
        self.transport.write(json.dumps([meth, params]) + "\n")

    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        LineReceiver.connectionMade(self)
        self.transport.disconnecting = False #erm. Needs this to fix a bug in Twisted?
        self.send_to_client("hello", [self.communicator.mod.name])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def lineReceived(self, line):
        print('received from processor: %s'%line)
        meth, rest = json.loads(line)
        if meth == 'sent_to_mud':
            self.communicator.telnet.sendLine(rest[0])    
        elif meth == "display_line":
            metaline = json_to_metaline(rest[0])
            soft_line_start = bool(rest[1])
            self.communicator.write(metaline, soft_line_start)
        elif meth == "hello":
            self.communicator.clientConnectionMade(self)
    
    def close(self):
        self.send_to_client("close", [])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def mud_line_received(self, metaline, display_line):
        self.send_to_client('mud_line', [metaline_to_json(metaline), int(display_line)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def user_line_received(self, line, server_echo, echo=True):
        self.send_to_client('user_line', [line, int(server_echo), int(echo)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1 
        
    def do_block(self, block):
        self.send_to_client('do_block', [json.dumps([metaline_to_json(l) for l in block])])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledges += 1
        
        
class Factory():
    def __init__(self, realm, name):
        self.realm = realm
        self.name = name
        self.gui = None
class Connector:
    def __init__(self,  mod):
        self.mod = mod
        self.factory=Factory(self, mod.name)
        self.telnet=None
        self.client=None
        self._escape_parser=EscapeParser()
        self.console=InteractiveConsole()
        self.wrapper = TextWrapper(width=100, drop_whitespace=False)
        self._closing_down = False
        self.protocols = []
        self.gui = None
        self.macros={}
        self.baked_in_macros={}
        self.state={}
     
     
    
    def addProtocol(self, protocol):
        self.protocols.append(protocol)
           
    def close(self):
        """Close up our connection and shut up shop.
        
        It is guaranteed that, on registered connection event receivers,
        connection_lost will be called before close.
        """
        if not self._closing_down:
            #lose the connection first.
            self.telnet.close()
        else:
            #connection's already lost, we don't need to wait
            for prot in self.protocols:
                prot.close()
            self.client.close()
        self._closing_down = True
        
    
    def telnetConnectionLost(self):
        """The link to the MUD died.

        It is guaranteed that this will be called before close on connection
        event receivers.
        """
        message = time.strftime("Connection closed at %H:%M:%S.")
        colour = HexFGCode(0xFF, 0xAA, 0x00) #lovely orange
        metaline = simpleml(message, colour, bg_code(BLACK))
        self.write_metaline(metaline)
        for prot in self.protocols:
            prot.connectionLost()
        self.client.connectionLost()
        #we might be waiting on the connection to die before we send out
        #close events
        if self._closing_down:
            for prot in self.protocols:
                prot.close()
            self.client.close()
        self._closing_down = True

    def telnetConnectionMade(self):
        """The MUD's been connected to."""
        message = time.strftime("Connection opened at %H:%M:%S.")
        colour = HexFGCode(0xFF, 0xAA, 0x00) #lovely orange
        metaline = simpleml(message, colour, bg_code(BLACK))
        self.write_metaline(metaline)
        for prot in self.protocols:
            prot.connectionMade()

    def clientConnectionMade(self, client):
        """We've got our user's stuff running. Benissimo!"""
        colour = HexFGCode(0xFF, 0xAA, 0x00)
        if self.telnet is None:
            message = "Hi, welcome to mudpyl. Trying to connect..."
            factory = TelnetClientFactory(self)
            from twisted.internet import reactor
            reactor.connectTCP(self.mod.host, self.mod.port, factory)
        else:
            self.client.close()
            message = "Client reloaded!"
        self.client = client
        self.write_metaline(simpleml(message, colour))
        
    def reload_client(self):
        c = ClientProtocol(self)
        from twisted.internet import reactor
        reactor.spawnProcess(c, self.mod.executable_path)
        
        
    def metalineReceived(self, metaline, display_line = True):
        """Match a line against the triggers and perhaps display it on screen.
        """
        self.client.mud_line_received(metaline, display_line)
        
    def blockReceived(self, block):
        self.client.do_block(block) 
        
    def receive_gui_line(self, string):
        """Send lines input into the GUI to the MUD.
        
        WARNING: this may have the power to execute arbitrary Python
        code. Thus, triggers and aliases should avoid using this, as
        they may be vulnerable to injection from outside sources. Use
        send instead.
        """
        if string.startswith('/'):
            self.console.push(string[1:])
        else:
            self.client.user_line_received(string, self.server_echo)
            
    def write(self, metaline, soft_line_start = False):
        #if self.hide_lines>0:
        #    self.hide_lines-=1
        #    return
        
        """Write a line to the screen."""
        
        
        #we don't need to close off the ends of the note, because thanks to
        #the magic of the ColourCodeParser, each new line is started by the
        #implied colour, so notes can't bleed out into text (though the 
        #reverse can be true).

        #this needs to be before the futzing with NLs and GA, because textwrap
        #obliterates all other newlines.
        metaline = metaline.wrapped(self.wrapper)

        #we don't actually append newlines at the end, but the start. This
        #simplifies things, because we don't use a newline where a soft line
        #end meets a soft line start, so there's only one place in this code
        #that can add newlines.
        
        if self._last_line_end is not None:
            if self._last_line_end == 'hard' or not metaline.soft_line_start:
                metaline.insert(0, '\n')
                
        for prot in self.protocols:
            prot.metalineReceived(metaline,self.active_channels)

        self._last_line_end = metaline.line_end
        
    def registerEventHandler(self, eventName, eventHandler):
        pass