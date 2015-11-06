from twisted.internet.protocol import ProcessProtocol
from twisted.protocols.basic import LineReceiver
import json as simplejson
from pymudclient.metaline import simpleml, metaline_to_json, json_to_metaline
from code import InteractiveConsole
from mudpyl.gui.bindings import gui_macros
from twisted.protocols.basic import LineReceiver
import traceback
import time
from mudpyl.colours import fg_code, bg_code, HexFGCode, HexBGCode, WHITE, BLACK
from mudpyl.net.telnet import TelnetClientFactory
from mudpyl.gui.keychords import from_string
from textwrap import TextWrapper
from datetime import datetime

class ClientProtocol(ProcessProtocol, LineReceiver):

    delimiter = '\n'
    MAX_LENGTH = 131072 * 8 * 100

    def __init__(self, communicator):
        self.communicator = communicator
        self.queued_lines = []
        self.queueing = False
        self.error_line_receiver = ErrorReceiver(communicator)
        self.messages_not_acknowledged = 0
        self.client_started_processing_at = None

    def send_to_client(self, meth, params):
        self.transport.write(simplejson.dumps([meth, params]) + "\n")

    def connectionMade(self):
        ProcessProtocol.connectionMade(self)
        LineReceiver.connectionMade(self)
        self.transport.disconnecting = False #erm. Needs this to fix a bug in Twisted?
        self.send_to_client("hello", [self.communicator.mod.name])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1

    def errReceived(self, data):
        self.error_line_receiver.dataReceived(data)

    outReceived = LineReceiver.dataReceived

    def lineReceived(self, line):
        meth, rest = simplejson.loads(line)
        if meth == "send to mud":
            if not self.queueing:
                self.communicator.telnet.sendLine(rest[0])
            else:
                self.queued_lines.append(rest[0])
        elif meth == "display line":
            metaline = json_to_metaline(rest[0])
            display_line = bool(rest[1])
            self.communicator.write_metaline(metaline, display_line)
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
        elif meth == "queue lines":
            self.queuing = True
        elif meth == "flush queue":
            self.queueing = False
            self.communicator.telnet.transport.writeSequence(sum([[line, "\r\n"] for line in self.queued_lines], []))
            self.queued_lines = []
        elif meth == "ack":
            self.messages_not_acknowledged -= 1
            if not self.messages_not_acknowledged:
                self.communicator.total_client_time += time.time() - self.client_started_processing_at
                self.client_started_processing_at = None
        elif meth == "gmcp to mud":
            if self.queueing:
                self.communicator.telnet.transport.writeSequence(sum([[line, "\r\n"] for line in self.queued_lines], []))
                self.queued_lines = []
            if len(rest) == 1:
                m = rest[0]
                o = None
            else:
                m, o = rest
            self.communicator.write_metaline(simpleml("GMCP to mud, meth %s payload %r" % (m, o)), False)
            self.communicator.telnet.sendGMCP(m, o)
        else:
            raise ValueError("bad request: %s" % line)

    def do_triggers(self, metaline, display_line):
        #XXX: need to account for server echo too
        self.send_to_client("do triggers", [metaline_to_json(metaline), int(display_line)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1

    def do_aliases(self, line, server_echo, echo = True):
        self.send_to_client("do aliases", [line, int(server_echo), int(echo)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1

    def do_atcp(self, data):
        self.send_to_client("do atcp", ["".join(data)])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1

    def do_gmcp(self, data):
        try:
            self.send_to_client("do gmcp", ["".join(data)])
        except:
            #XXX. Bandaid.
            pass
        else:
            if not self.messages_not_acknowledged:
                self.client_started_processing_at = time.time()
            self.messages_not_acknowledged += 1

    def close(self):
        self.send_to_client("close", [])
        if not self.messages_not_acknowledged:
            self.client_started_processing_at = time.time()
        self.messages_not_acknowledged += 1
        #self.transport.signalProcess("KILL")

class ErrorReceiver(LineReceiver):

    delimiter = '\n'

    def __init__(self, communicator):
        self.communicator = communicator

    def lineReceived(self, line):
        self.communicator.write_metaline(simpleml("ERROR: " + line))

class ClientCommunicator(object):

    def __init__(self, mod):
        self.mod = mod
        self.gui = None
        self.telnet = None
        self.client = None
        self.baked_in_macros = gui_macros.copy()
        self.macros = self.baked_in_macros.copy()
        self.tracing = False
        self.server_echo = False
        self.console_ns = {'cc': self}
        self.console = InteractiveConsole(self.console_ns)
        self._last_line_end = None
        self.wrapper = TextWrapper(width = 100, 
                                   drop_whitespace = False)
        self.protocols = []
        self._closing_down = False
        self.total_client_time = 0

    #Bidirectional, or just ambivalent, functions.

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

    def trace_on(self):
        """Turn tracing (verbose printing to the output screen) on."""
        if not self.tracing:
            self.tracing = True
            self.trace("Tracing enabled!")

    def trace_off(self):
        """Turn tracing off."""
        if self.tracing:
            self.trace("Tracing disabled!")
            self.tracing = False

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

    #Going towards the screen

    def metalineReceived(self, metaline, display_line = True):
        """Match a line against the triggers and perhaps display it on screen.
        """
        self.client.do_triggers(metaline, display_line)

    def fake_lines(self, *lines):
        for line in lines:
            self.metalineReceived(simpleml(line, fg_code(WHITE, False),
                                           bg_code(BLACK)))

    def write_metaline(self, metaline, display_line = True):
        """Write a line to the screen.
        """
        #we don't need to close off the ends of the note, because thanks to
        #the magic of the ColourCodeParser, each new line is started by the
        #implied colour, so notes can't bleed out into text (though the 
        #reverse can be true).

        #this needs to be before the futzing with NLs and GA, because textwrap
        #obliterates all other newlines.
        metaline = metaline.wrapped(self.wrapper)

        now = datetime.now()
        timestamp = now.strftime("(%H:%M:%S.%%02d)") % (now.microsecond / (10 ** 4))

        for prot in self.protocols:
            #NB: not actually raw, but close enough, right?
            prot.writeRawReceivedMetaline(metaline.copy(), timestamp, display_line = display_line)

        #with no_ga_nl_munging enabled:
        #we don't actually append newlines at the end, but the start. This
        #simplifies things, because we don't use a newline where a soft line
        #end meets a soft line start, so there's only one place in this code
        #that can add newlines.

        #with it enabled:
        #we also don't insert an NL between a command echo following a GA and server text,
        #because a NL will be present anyway.
        #XXX: notes are broken with no_ga_nl_munging enabled
        if self._last_line_end is not None:
            if not getattr(self.mod, "no_ga_nl_munging", False):
                if self._last_line_end != 'soft' or not metaline.soft_line_start:
                    metaline.insert(0, '\n')
            else:
                if self._last_line_end == "hard":
                    metaline.insert(0, "\n")
                elif self._last_line_end == "semi-hard" and metaline.soft_line_start:
                    metaline.insert(0, "\n")

        for prot in self.protocols:
            prot.writeReceivedMetaline(metaline, timestamp, display_line = display_line)

        if display_line:
            if getattr(self.mod, "no_ga_nl_munging", False) and self._last_line_end != "hard" and metaline.soft_line_start:
                self._last_line_end = "semi-hard"
            else:
                self._last_line_end = metaline.line_end

    def trace(self, line):
        """Write the argument to the screen if we are tracing, elsewise do
        nothing.
        """
        if self.tracing:
            self.write_metaline("TRACE: " + line)

    def trace_thunk(self, thunk):
        """If we're tracing, call the thunk and write its result to the
        outputs. If not, do nothing.
        """
        if self.tracing:
            self.write_metaline("TRACE: " + thunk())

    def atcpDataReceived(self, data):
        self.client.do_atcp(data)

    def gmcpDataReceived(self, data):
        self.client.do_gmcp(data)

    #Going towards the MUD.

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

