from twisted.protocols.basic import LineReceiver
from pymudclient.escape_parser import EscapeParser
import json
from pymudclient.metaline import json_to_metaline, metaline_to_json, simpleml,\
    Metaline
from twisted.internet.task import LoopingCall
from operator import attrgetter
from zope.interface.declarations import implementedBy
from pymudclient.triggers import TriggerMatchingRealm, TriggerBlockMatchingRealm,\
    RegexTrigger
from pymudclient.colours import fg_code, WHITE, bg_code, BLACK
from pymudclient.aliases import AliasMatchingRealm
import traceback
from pymudclient.tagged_ml_parser import taggedml


class MudProcessor(LineReceiver):
    delimiter = "\n"
    MAX_LENGTH = 131072 * 8 * 100

    def __init__(self):
        self._escape_parser=EscapeParser()
        self.macros = {}
        self.log=open(r'c:\temp\log_process.log','w',0)
        self.log.write('Init MudProcessor\n')
        self.buffering = False
        self.buffer = ''
        self.missed_heartbeats = 0
        self.heartbeat_lc = None
        self.settings_directory=''
        self.server_echo = True
        self.triggers = []
        self.aliases = []
        self.gmcp_events = []
        self.gmcp={}
        self.last_command_sent = ''
        self.root=self
        self.tracing = False
        self.active_channels = ['main']
        self.state={}
        self.event_handlers={}
        self.reactor = None
        self.block=[]
        self.queue_to_send=[]
        self.connected=False
        self.name=''
        self.safe_to_send=True
        self.highlights={}
        
        
    def heartbeat(self):
        self.missed_heartbeats+=1
        if self.missed_heartbeats == 3:
            self.stop()
        else:
            self.send_to_client('ping', [])
        
    def stop(self):
        self.send_to_client('bye', [])
        self.log.close()
        self.transport.loseConnection()
        from twisted.internet import reactor
        reactor.stop()
        
    def connectionMade(self):
        self.log.write('ConnectionMade\n')
        self.connected = True
        #self.transport.write(json.dumps(["hello", [self.macros]]) + "\n")
        self.send_to_client('hello', [self.macros] if len(self.macros) else [{}])
        self.heartbeat_lc = LoopingCall(self.heartbeat)
        self.heartbeat_lc.start(10)
        
        for meth,params in self.queue_to_send:
            self.send_to_client(meth, params)
    
    def send_to_client(self, meth, params):
        #print('send to processor: %s, %s'%(meth, json.dumps(params)))
        if self.connected:
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
        else:
            self.queue_to_send.append((meth,params))

    
    def lineReceived(self, line):
        self.log.write('Line: %s \n'%line)
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
    def lineReceived_recomposed(self, line):
        
            
        meth,rest = json.loads(line)
        if meth == "close":
            self.stop()
        elif meth == "ping":
            self.missed_heartbeats=-1
            
        elif meth == "hello":
            self.log.write('Hello received\n')
            name = rest[0]
            self.name = name
            
        elif meth == 'mud_line':
            metaline = json_to_metaline(rest[0])
            display_line = bool(rest[1])
            #self.match_triggers(metaline, display_line)
            #self.transport.write(json.dumps(['display_line', [metaline_to_json(metaline), 1]])+'\n')
            self.send_to_client('display_line', [metaline_to_json(metaline),1])
        elif meth == 'user_line':
            line = rest[0]
            self.log.write('User Line: %s\n'%line)
            #self.transport.write(json.dumps(['send_to_mud',line])+'\n')
            self.send_to_client('send_to_mud', line)
        elif meth == 'do_block':
            lines = json.loads(rest[0])
            block = []
            for l in lines:
                block.append(json_to_metaline(l))
            self.blockReceived(block)
        
        elif meth == 'do_triggers':
            metaline=json_to_metaline(rest[0])
            display_line = bool(rest[1])
            self.metalineReceived(metaline, display_line)
        
        elif meth == 'do_aliases':
            line = rest[0]
            self.server_echo = bool(rest[1])
            echo = bool(rest[2])
            self.parseSend(line, echo)
        elif meth == 'do_gmcp':
            pair = rest[0]
            gmcp_key,gmcp_data = pair
            self.gmcp[gmcp_key]=gmcp_data
            for gmcp_event in self.gmcp_events:
                gmcp_event(pair, self)
        else:
            raise ValueError("bad line: %s" % line)
        #self.transport.write(json.dumps(["ack", [meth,rest]]) + "\n")
        self.send_to_client('ack', [meth,rest])
    
    
    
    def load_module(self, cls, _sort = True):
        """Load the triggers, aliases, macros and other modules of the given
        module.
        """
        robmod = cls(self)
        for mod in robmod.modules:
            self.load_module(mod, _sort = False)
        if _sort:
            self.triggers.sort(key = attrgetter("sequence"))
            self.gmcp_events.sort(key = attrgetter("sequence"))
            self.aliases.sort(key = attrgetter("sequence"))
        
        return robmod
    
    def registerEventHandler(self, eventName, eventHandler):
        if not eventName in self.event_handlers:
            self.event_handlers[eventName]=[]
        self.event_handlers[eventName].append(eventHandler)
    
    
    def fireEvent(self, eventName, *args):
        self.send_to_client('event', [eventName,args])
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
        
    def set_state(self, name, value):
        self.state[name]=value
        self.send_to_client('set_state', [name,value])
        
    def metalineReceived(self, metaline, display_line):
        realm = TriggerMatchingRealm(metaline, parent = self, root = self,
                                     display_line = display_line)
        try:
            realm.process()
        except:
            self.handle_exception(traceback.format_exc())
    
    def cwrite(self, line, display_line=True, channels=['main']):
        ml=taggedml(line)
        ml.channels = channels
        self.write(ml, display_line)
        
    def write(self, line, display_line = True):
        if not isinstance(line, (basestring, Metaline)):
            line = str(line)
        if isinstance(line, basestring):
            metaline = simpleml(line, fg_code(WHITE, False), bg_code(BLACK))
            metaline.wrap = False
        else:
            metaline = line
        self.send_to_client('display_line', [metaline_to_json(metaline),int(display_line)])
    
    def send_mud(self, line):
        self.last_command_sent = line
        self.send_to_client('send_to_mud', line)
        
    def safe_send(self, line, echo = True):
        if self.safe_to_send:
            self.send(line, echo)
        
    def send(self, line, echo = True):
        """Match aliases against the line and perhaps send it to the MUD."""
        echo = not self.server_echo and echo
        realm = AliasMatchingRealm(line, echo, parent = self, root = self)
        try:       
            realm.process()
        except:
            self.handle_exception(traceback.format_exc())
        
    def parseSend(self, string, echo):
        for line in list(self._escape_parser.parse(string + '\n')):
            self.send(line, echo)
            
    def setActiveChannels(self, channels):
        self.active_channels = channels
        self.send_to_client('set_active_channels', channels)
        
    def handle_exception(self, trace):
        self.send_to_client('error', trace)
        
        
    def blockReceived(self, block):
        self.block = block 
        realm = TriggerBlockMatchingRealm(self.block, parent = self, root = self, 
                                          display_group=True)
        realm.process()
    
    def set_timer(self, time, fn, *args, **kwargs):
        from twisted.internet import reactor
        realm = TimerRealm(self)
        timer = self.reactor.callLater(time, fn, realm, *args, **kwargs)
        return timer
    
    def debug(self, msg):
        self.send_to_client('debug', [msg])
        
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
            
    
    def add_highlight(self, highlight_text, highlight_color, bold=False):
        def _color(match, realm):
            start = 0
            loc = realm.metaline.line.find(highlight_text, start)
            while loc!=-1:
                realm.alterer.change_fore(loc, loc + len(highlight_text), fg_code(highlight_color, bold))
                start=loc+len(highlight_text)
                loc = realm.metaline.line.find(highlight_text, start)
            
        new_trigger = RegexTrigger(highlight_text, _color)
        self.triggers.append(new_trigger)
        self.highlights[highlight_text]=new_trigger
        
    def remove_highlight(self, highlight_text):
        if highlight_text in self.highlights:
            self.triggers.remove(self.highlights[highlight_text])
            del self.highlights[highlight_text]
            
class TimerRealm(object):

    def __init__(self, root):
        self.root = self.parent = root
    
    
    def safe_send(self, line, echo=False):
        self.parent.safe_send(line, echo)
    def send(self, line, echo = False):
        self.parent.send(line, echo)

    def send_gmcp(self, meth, obj = None):
        self.parent.send_gmcp(meth, obj)

    def cwrite(self, *args, **kwargs):
        self.parent.cwrite(*args, **kwargs)
        
    def write(self, *args, **kwargs):
        self.parent.write(*args, **kwargs)

    def write_now(self, *args, **kwargs):
        self.parent.write_now(*args, **kwargs)

    def trace(self, *args, **kwargs):
        self.parent.trace(*args, **kwargs)

    def trace_thunk(self, *args, **kwargs):
        self.parent.trace_thunk(*args, **kwargs)

    def set_timer(self, *args, **kwargs):
        return self.parent.set_timer(*args, **kwargs)
    
    def fireEvent(self, eventName, *args):
        return self.parent.fireEvent(eventName, *args)

    def queue(self):
        self.parent.queue()

    def flush(self):
        self.parent.flush()

    def parseSend(self, line, echo = False):
        self.parent.parseSend(line, echo)
