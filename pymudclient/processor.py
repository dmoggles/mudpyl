from twisted.protocols.basic import LineReceiver
from pymudclient.escape_parser import EscapeParser
import json
from pymudclient.metaline import json_to_metaline, metaline_to_json
from twisted.internet.task import LoopingCall
from operator import attrgetter



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
        
        self.triggers = []
        self.aliases = []
        self.gmcp_events = []
        
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
        self.transport.write(json.dumps(["hello", [self.macros]]) + "\n")
        self.heartbeat_lc = LoopingCall(self.heartbeat)
        self.heartbeat_lc.start(10)
    
    def send_to_client(self, meth, params):
        #print('send to processor: %s, %s'%(meth, json.dumps(params)))
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
            for l in lines:
                #self.transport.write(json.dumps(['display_line',[l]])+'\n')
                self.send_to_client('display_line',[l,1])
            
        
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
            self.gmcp_triggers.sort(key = attrgetter("sequence"))
            self.aliases.sort(key = attrgetter("sequence"))
        return robmod