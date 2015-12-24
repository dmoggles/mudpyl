from pymudclient.gui.bindings import gui_macros
from pymudclient.escape_parser import EscapeParser
from code import InteractiveConsole
from textwrap import TextWrapper
from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineReceiver
import time
import json
from pymudclient.colours import HexFGCode, bg_code, BLACK, fg_code, WHITE
from pymudclient.metaline import simpleml, metaline_to_json, json_to_metaline
from pymudclient.net.telnet import TelnetClientFactory
import traceback
from pymudclient.gui.keychords import from_string


class ClientProtocol(ProcessProtocol, LineReceiver):
    
    
    delimiter = '\n'
    MAX_LENGTH = 131072 * 8 * 100

    def __init__(self, communicator):
        self.communicator = communicator
    
    def send_to_client(self, meth, params):
        self.transport.write(json.dumps([meth, params]) + "\n")
        
    
    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        LineReceiver.connectionMade(self)
        self.transport.disconnecting = False 
        self.send_to_client("hello", [self.communicator.mod.name])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def lineReceived(self, line):
        meth, rest = json.loads(line)
        if meth == 'set_channels':
            self.communicator.set_channels(rest)
        elif meth == 'fire_event':
            event_name=rest[0]
            self.communicator.do_fireEvent(event_name, json.loads(rest[1]))
        elif meth == "hello":
            macros = rest[0]
            def make_macro(cmd):
                def macro(cc):
                    cc.client.do_aliases(cmd, False)
                return macro
            self.communicator.macros.clear()
            self.communicator.macros.update(dict((from_string(k), make_macro(l)) for k, l in macros.items()))
            self.communicator.macros.update(self.communicator.baked_in_macros)
            self.communicator.clientConnectionMade(self)
        elif meth == "ack":
            self.messages_not_acknowledged -= 1
            if not self.messages_not_acknowledged:
                self.communicator.total_client_time += time.time() - self.client_started_processing_at
                self.client_started_processing_at = None
        elif meth == "send to mud":
            if not self.queueing:
                self.communicator.telnet.sendLine(rest[0])
            else:
                self.queued_lines.append(rest[0])
        elif meth == "display line":
            metaline = json_to_metaline(rest[0])
            display_line = bool(rest[1])
            self.communicator.write_metaline(metaline, display_line)
            
    def do_triggers(self, metaline, display_line):
        #XXX: need to account for server echo too
        self.send_to_client("do_triggers", [metaline_to_json(metaline), int(display_line)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def do_gmcp(self, data):
        self.send_to_client("do_gmcp", json.dumps(data))
      
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1 
        
    def do_alias(self, line, server_echo, echo= True):
        self.send_to_client("do_aliases", [line, int(server_echo), int(echo)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1 
        
        
    def do_block(self, block):
        self.send_to_client("do_block", json.dumps([metaline_to_json(l) for l in block]))
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledges += 1
        
    def close(self):
        self.send_to_client("close", [])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def fireEvent(self, eventName, *args):
        self.send_to_client('fire_event', [eventName, json.dumps(args)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1

class Connector:
    
    def __init__(self, factory):
        self.factory=factory
        self.telnet=None
        self.client = None
        self.baked_in_macros = gui_macros.copy()
        self.macros = self.baked_in_macros.copy()
        self._escape_parser = EscapeParser()
        self.tracing = False
        self.server_echo = False
        self.console_ns = {'realm',self}
        self.console = InteractiveConsole()
        self.wrapper = TextWrapper(width = 100, drop_whitespace = False)
        self.active_channels=['main']
        self.gui = None
        self.event_handlers={}
        self.accessibility_mode = False
        
        self.protocols=[]
        self._closing_down = False
        
        
    def registerEventHandler(self, eventName, eventHandler):
        if not eventName in self.event_handlers:
            self.event_handlers[eventName]=[]
        self.event_handlers[eventName].append(eventHandler)
     
    def do_fireEvent(self, eventName, *args):
        if eventName in self.event_handlers:
            for eh in self.event_handlers[eventName]:
                self.factory.reactor.callLater(0, eh, *args)
              
  
                
    def fireEvent(self, eventName, *args):
        self.client.fireEvent(eventName, *args)
        self.do_fireEvent(eventName, *args)
        
        
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
        self._closing_down = True   
        
    def addProtocol(self, protocol):
        self.protocols.append(protocol)

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
        
    def maybe_do_macro(self, chord):
        """Try and run a macro against the given keychord.

        A return value of True means a macro was found and run, False means
        no macro was found, or a macro returned True (meaning allow the GUI
        to continue handling the keypress).
        """
        if chord in self.macros:
            macro = self.macros[chord]
            try:
                macro(self)
            except Exception:
                #XXX: integrate
                traceback.print_exc()
            return True
        else:
            return False
    
    
    #To the screen
    
    def gmcpReceived(self, gmcp_pair):
        self.client.do_gmcp(gmcp_pair)

    def blockReceived(self, block):
        self.client.do_block(block)
            
            
    def metalineReceived(self, metaline, display_line = True):
        """Match a line against the triggers and perhaps display it on screen.
        """
        self.client.do_triggers(metaline, display_line)

    def fake_lines(self, *lines):
        for line in lines:
            self.metalineReceived(simpleml(line, fg_code(WHITE, False),
                                           bg_code(BLACK)))
            
            
    def set_channels(self, channels):
        self.active_channels=channels
        
    
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

    def trace(self, line):
        """Write the argument to the screen if we are tracing, elsewise do
        nothing.
        """
        if self.tracing:
            self.write("TRACE: " + line)

    def trace_thunk(self, thunk):
        """If we're tracing, call the thunk and write its result to the
        outputs. If not, do nothing.
        """
        if self.tracing:
            self.write("TRACE: " + thunk())     
            
            
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
            self.client.do_aliases(string, self.server_echo)