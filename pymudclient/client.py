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
import traceback
from pymudclient.gui.bindings import gui_macros
from pymudclient import spawnProcessHelper
from pymudclient.tagged_ml_parser import taggedml
from pymudclient.gui.keychords import from_string



class ClientProtocol(ProcessProtocol, LineReceiver):
    delimiter = '\n'
    MAX_LENGTH = 131072 * 8 * 100

    def __init__(self, communicator):
        self.communicator = communicator
        self.messages_not_acknowledged = 0
        self.buffering = False
        self.buffer = ''
        
    def send_to_client(self, meth, params):
        line = json.dumps([meth, params])
        if len(line)>1000:
            self.transport.write("%buff_begin%\n")
            while len(line)>1000:
                self.transport.write(line[:1000]+"\n")
                line=line[1000:]
            self.transport.write(line+"\n")
            self.transport.write("%buff_end%\n")
        else:
            self.transport.write(json.dumps([meth, params]) + "\n")

    def lineReceived(self, line):
        if line == '%buff_begin%':
            self.buffering = True
            self.buffer = ''
        elif line == '%buff_end%':
            if self.buffering == True:
                self.lineReceived_recomposed(self.buffer)
            self.buffering = False
        else:
            if self.buffering == True:
                self.buffer += line
            else:
                self.lineReceived_recomposed(line)
    
    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        LineReceiver.connectionMade(self)
        self.transport.disconnecting = False #erm. Needs this to fix a bug in Twisted?
        self.send_to_client("hello", [self.communicator.mod.name])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
    def lineReceived_recomposed(self, line):
        meth, rest = json.loads(line)
        if meth == 'ack':
            self.messages_not_acknowledged -= 1
            if not self.messages_not_acknowledged:
                process_time = time.time() - self.client_started_processing_at
                self.communicator.total_client_time += process_time
                self.client_started_processing_at = None
                #print('Process Time: %(process_time)d, Total Process Time: %(total_process_time)d\n'%
                #      {'process_time':process_time, 'total_process_time':self.communicator.total_client_time})
        elif meth == 'send_to_mud':
            self.communicator.telnet.sendLine(rest)   
        elif meth == 'ping':
            self.send_to_client('ping', []) 
        elif meth == "display_line":
            metaline = json_to_metaline(rest[0])
            soft_line_start = bool(rest[1])
            self.communicator.write(metaline, soft_line_start)
        elif meth == 'set_active_channels':
            self.communicator.setActiveChannels(rest)
        elif meth == "hello":
            macros = rest[0]
            def make_macro(cmd):
                def macro(cc):
                    cc.client.do_alias(cmd, False)
                return macro
            self.communicator.macros.clear()
            self.communicator.macros.update(dict((from_string(k), make_macro(l)) for k, l in macros.items()))
            self.communicator.macros.update(self.communicator.baked_in_macros)
            self.communicator.clientConnectionMade(self)
        elif meth == "error":
            if self.communicator.debug:
                self.communicator.cwrite('<white*:red>ERROR RECEIVED: \n %s'%rest)
            else:
                print(rest)
        elif meth == 'set_state':
            self.communicator.set_state(rest[0],rest[1])
        elif meth == 'event':
            event_name = rest[0]
            args = rest[1]
            self.communicator.fireEventLocal(event_name, *args)
        
        elif meth == 'debug':
            line = rest[0]
            if self.communicator.debug:
                self.communicator.cwrite('<grey:white>PROCESSOR DEBUG [[%s]]'%line)
            else:
                print('PROCESSOR DEBUG [[%s]]'%line)
        else:
            if self.communicator.debug:
                self.communicator.cwrite('<white*:red>UNKNOWN METHOD RECEIVED: \n Method:%(meth)s \n Args: %(rest)s'%{'rest':rest, 'meth':meth})
            else:
                print('UNKNOWN METHOD RECEIVED: \n Method:%(meth)s \n Args: %(rest)s'%{'rest':rest, 'meth':meth})
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
        self.messages_not_acknowledged += 1
        
    def do_alias(self, line, server_echo, echo= True):
        self.send_to_client("do_aliases", [line, int(server_echo), int(echo)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1 
    
    def do_triggers(self, metaline, display_line):
        self.send_to_client("do_triggers", [metaline_to_json(metaline), int(display_line)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
    
    def do_gmcp(self, gmcp_pair):
        self.send_to_client("do_gmcp", [gmcp_pair])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
    
    def do_event(self, eventName, *args):
        self.send_to_client('event', [eventName, args])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        
        
    def errReceived(self, data):
        if self.communicator.debug:
            self.communicator.cwrite('<white*:red>CORE ERROR RECEIVED: \n %s'%data)
        else:
            print(data) 
       
    
    outReceived = LineReceiver.dataReceived
        
class Connector:
    def __init__(self,  mod):
        self.mod = mod
        self.gui = None
        self.telnet=None
        self.client=None
        self._escape_parser=EscapeParser()
        self.console=InteractiveConsole()
        self.wrapper = TextWrapper(width=100, drop_whitespace=False)
        self._closing_down = False
        self.protocols = []
        self.extra_gui = None
        self.macros=gui_macros.copy()
        self.baked_in_macros=gui_macros.copy()
        self.state={}
        self._last_line_end = None
        self.active_channels=['main']
        self.gmcp_handler=None
        self.gmcp={}
        self.server_echo=False
        self.processor_exec = ''
        self.module_name = ''
        self.debug = True
        self.event_handlers={}
        self.reactor = None
        self.total_client_time = 0
        self.block=[]
        self.user_echo = True
        
        
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
        self.write(metaline)
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
        self.write(metaline)
        for prot in self.protocols:
            prot.connectionMade()

    def clientConnectionMade(self, client):
        """We've got our user's stuff running. Benissimo!"""
        colour = HexFGCode(0xFF, 0xAA, 0x00)
        if self.telnet is None:
            message = "Trying to connect..."
            factory = TelnetClientFactory(self)
            from twisted.internet import reactor
            reactor.connectTCP(self.mod.host, self.mod.port, factory)
        else:
            self.client.close()
            message = "Client reloaded!"
        self.client = client
        self.write(simpleml(message, colour))
        
    def reload_client(self):
        c = ClientProtocol(self)
        from twisted.internet import reactor
        #reactor.spawnProcess(c, self.mod.executable_path)
        spawnProcessHelper.spawnProcess(c, self.processor_exec, self.module_name)
        
        
    def metalineReceived(self, metaline, display_line = True):
        """Match a line against the triggers and perhaps display it on screen.
        """
        self.client.do_triggers(metaline, display_line)
        
    def blockReceived(self, block):
        self.client.do_block(block) 
        
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
            
        
            self.client.do_alias(string, self.server_echo, self.user_echo)
    
    def cwrite(self, line, soft_line_start=False):
        ml=taggedml(line)
        self.write(ml, soft_line_start)
        
           
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
        
    
    
    def setActiveChannels(self, channels):
        self.active_channels = channels
        
    def gmcpReceived(self, gmcp_pair):
        self.client.do_gmcp(gmcp_pair)
        
    def set_state(self, name, value):
        self.state[name]=value
    
    def registerEventHandler(self, eventName, eventHandler):
        if not eventName in self.event_handlers:
            self.event_handlers[eventName]=[]
        self.event_handlers[eventName].append(eventHandler)
        
    def fireEvent(self, eventName, *args):
        self.client.do_event(eventName,*args)
        self.fireEventLocal(eventName, *args)
    
    def fireEventLocal(self, eventName, *args):
        if eventName in self.event_handlers:
            for eh in self.event_handlers[eventName]:
                self.reactor.callLater(0, eh, *args)   
                
    def get_state(self, item):
        if item in self.state:
            return self.state[item]
        else:
            return ''
    
   
