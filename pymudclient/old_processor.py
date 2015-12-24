'''
Created on Dec 3, 2015

@author: Dmitry
'''
from twisted.protocols.basic import LineReceiver
from operator import attrgetter
from pymudclient.escape_parser import EscapeParser
import json
from pymudclient.aliases import AliasMatchingRealm
from pymudclient.triggers import TriggerBlockMatchingRealm, TriggerMatchingRealm
from pymudclient.metaline import metaline_to_json, simpleml, Metaline,\
    json_to_metaline
from pymudclient.colours import fg_code, WHITE, bg_code, BLACK
from pymudclient.tagged_ml_parser import taggedml

class ProcessorRealm(LineReceiver):
    def __init__(self):
        self._escape_parser = EscapeParser()
        self.triggers = self.triggers[:]
        self.aliases = self.aliases[:]
        self.gmcp_events = self.gmcp_events[:]
        for module in self.modules:
            self.load_module(module)
        self.root = self
        self.server_echo = False
        self.tracing = False #XXX
        self.name = None
        self.last_command_sent = None
        self.gmcp_handler=None
        
        self.gmcp={}
        self.event_handlers={}
        self.active_channels=['main']
        
    
    def lineReceived(self, line):
        meth, rest = json.loads(line)
        if meth == 'fire_event':
            self.do_fireEvent(rest[0], json.loads(rest[1]))
        if meth == 'do_gmcp':
            self.gmcpReceived(json.loads(rest[0]))
        if meth == 'do_triggers':
            metaline=json_to_metaline(rest[0])
            display_line = bool(rest[1])
            self.metalineReceived(metaline, display_line)
            
            
    def blockReceived(self, block):
        if len(block) > 0:
            realm = TriggerBlockMatchingRealm(block, parent = self, root = self,    
                                          send_line_to_mud = self.send_mud)
            realm.process()
            
    
    def setActiveChannels(self, channels):
        self.send_to_client('set_channels', channels)
        self.active_channels=channels
     
    def gmcpReceived(self, gmcp_pair):
        """Take GMCP data and do something with it"""
        for gmcp_event in self.gmcp_events:
            gmcp_event(gmcp_pair, self)        
        
    def send_to_client(self, meth, data):
        jsonobj = [meth, data]
        self.transport.write(json.dumps(jsonobj)+"\n")
        
    def send(self, line, echo = True):
        """Match aliases against the line and perhaps send it to the MUD."""
        echo = not self.server_echo and (echo and not self.accessibility_mode)
        realm = AliasMatchingRealm(line, echo, parent = self, root = self,
                                   send_line_to_mud = self.send_mud)
        realm.process()
    
    def send_mud(self, line):
        self.last_command_sent=line
        self.send_to_client('send_to_mud', [line])
        
    def load_module(self, cls, _sort = True):
        """Load the triggers, aliases, macros and other modules of the given
        module.
        """
        robmod = cls(self)
        for mod in robmod.modules:
            self.load_module(mod, _sort = False)
        if _sort:
            self.triggers.sort(key = attrgetter("sequence"))
            self.atcp_triggers.sort(key = attrgetter("sequence"))
            self.gmcp_triggers.sort(key = attrgetter("sequence"))
            self.aliases.sort(key = attrgetter("sequence"))
        return robmod
    
    def connectionMade(self):
        self.transport.write(json.dumps(["hello", [self.macros]]) + "\n")
        
    def registerEventHandler(self, eventName, eventHandler):
        if not eventName in self.event_handlers:
            self.event_handlers[eventName]=[]
        self.event_handlers[eventName].append(eventHandler)
        
    def do_fireEvent(self, eventName, *args):
        if eventName in self.event_handlers:
            for eh in self.event_handlers[eventName]:
                self.factory.reactor.callLater(0, eh, *args)
              
    def metalineReceived(self, metaline):
        """Match a line against the triggers and perhaps display it on screen.
        """
        realm = TriggerMatchingRealm(metaline, parent = self,  root = self,
                                     send_line_to_mud = self.send_mud)
        realm.process()
         
                
    def fireEvent(self, eventName, *args):
        self.send_to_client('fire_event',[eventName, json.dumps(args)])
        self.do_fireEvent(eventName, *args)
        
    def get_state(self, item):
        if item in self.state:
            return self.state[item]
        else:
            return ''
        
    def set_state(self, item, value):
        self.state[item]=value
        
    def cwrite(self, line, soft_line_start=False, display_line=True):
        ml=taggedml(line)
        self.write(ml, soft_line_start,display_line)
        
    def write(self, line, soft_line_start = False, display_line=True):
        #if self.hide_lines>0:
        #    self.hide_lines-=1
        #    return
        
        """Write a line to the screen.
        
        This forcibly converts its argument to a Metaline.
        """
        if not isinstance(line, (basestring, Metaline)):
            line = str(line)
        if isinstance(line, basestring):
            metaline = simpleml(line, fg_code(WHITE, False), bg_code(BLACK))
            metaline.wrap = False
            metaline.soft_line_start = soft_line_start
        else:
            metaline = line
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
                
        jsonobj = ["display line", [metaline_to_json(metaline), int(display_line)]]
        self.transport.write(json.dumps(jsonobj) + "\n")

        self._last_line_end = metaline.line_end
    